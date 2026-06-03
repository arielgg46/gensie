"""
PARSE-style pipeline (arxiv:2510.08623): schema optimization (ARCHITECT),
reflection + guardrails (SCOPE), and backward-compatible output (RELAY).

Runtime note: the paper runs ARCHITECT as an offline build phase; here we use
a single LLM refinement call per task (configurable) so competition inference
remains tractable while preserving the same mechanistic stages.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Mapping, Optional

from openai import OpenAI

from gensie.agent import GenSIEAgent
from gensie.runtime import (
    ChatMessage,
    require_all_json_schema_properties,
    trace_step as _runtime_trace_step,
)
from gensie.schemas import coerce_nullable_string_nulls
from gensie.task import Task

_ARCHITECT_SYSTEM = """You refine JSON Schemas so another LLM can extract structured values from unstructured TEXT. The schema is a contract for machine consumption—precise, low-noise, no narrative essays.

Return exactly one JSON object: {"optimized_schema": <object>}. No text outside that JSON.

Structural contract (non-negotiable):
- Preserve the same property graph as the user schema: identical keys at every path, same nesting, same array item shapes, and the same primitive types. Do not rename, split, merge, flatten, or relocate fields.
- Do not add properties that are not already present in the user schema tree. Improve clarity only inside existing properties and containers.
- Stay within OpenAI `json_schema` strict capabilities: no $ref, no oneOf/anyOf/allOf/not, no if/then/else, no keywords the API cannot enforce in strict mode.

How to improve extraction quality:
- Conciseness: short, high-signal descriptions; avoid redundant prose or duplicate constraints.
- Disambiguation: when two fields could be confused, sharpen descriptions (not new keys) so roles are unmistakable (scope, units, “excluding X”, “canonical name vs display name”, etc.).
- Validation overlays: use enum for closed vocabularies; pattern and length bounds when formats are known; numeric min/max when safe; describe normalization in text when the instruction implies rounding, currency handling, or locale.
- Dates and times: in descriptions, spell out acceptable formats, defaults for missing timezone, and what to output when TEXT is partial or relative (today, next Tuesday) if the task allows inference—otherwise say “leave null/omit unless explicit”.
- Objects and arrays: refine nested item schemas the same way; specify per-item invariants when lists must stay internally consistent.
- Required lists: mirror the user schema; never invent new required paths.

Self-check before responding: (1) Could an extractor fill every leaf from TEXT using task + schema? (2) Are all constraints mutually consistent? (3) Did I keep the graph identical?"""

_SCOPE_SYSTEM = """You extract structured data from TEXT following TASK instruction and SCHEMA.

Output contract:
- Produce one JSON value matching SCHEMA exactly: types, shapes, nesting. No markdown, explanations, or keys not defined by SCHEMA.

Presence and nullability:
- Include every required property. Optional properties: include when TEXT supports a defensible value; if SCHEMA allows null for “unknown”, use null rather than guessing; if optional and null is disallowed, omit the key when unsupported.

Grounding and evidence:
- Strings must be traceable to TEXT (verbatim spans or explicitly allowed paraphrase per instruction). Never invent entities, identifiers, amounts, dates, locations, quotes, or citations.
- Numbers/booleans: set only when TEXT states them (digits, words, clear negation/affirmation). Avoid speculative math or unit conversion unless TASK requires it and TEXT supplies inputs.
- Enums: emit exactly one allowed literal with correct spelling and casing.

Constraints and structure:
- Honor pattern, minLength, maxLength, minimum, maximum, and enum together—do not satisfy one constraint by breaking another.
- Nested records: keep fields mutually consistent with the same snippet of TEXT (e.g. names with roles, line items with totals when both appear).
- Arrays: include only items evidenced by TEXT; no filler elements. Preserve TEXT order unless TASK specifies otherwise.

Conflicts and uncertainty:
- When TEXT contradicts itself, prefer the latest explicit correction in dialogue; otherwise pick the least speculative reading permitted by SCHEMA, or null/omit as appropriate.
- If TASK asks for a field but TEXT lacks support, follow SCHEMA rules for missing data (null vs omit) rather than hallucinating.

Repair rounds: if you receive “Issues” after a prior answer, apply minimal edits to your JSON to fix only those issues; leave correct fields untouched."""

_REFLECTION_USER_PREFIX = (
    "The last JSON failed automated validation relative to TEXT and SCHEMA.\n"
    "Return a corrected single JSON object. Change only what is necessary to resolve the issues below; "
    "do not rewrite unrelated correct fields. Typical failures here: required keys missing or null when not allowed; "
    "values not evidenced in TEXT; enum/pattern/length/type mismatches; structural shape mistakes.\n"
    "Issues:\n"
)

_WHITESPACE_RE = re.compile(r"\s+")


_MISSING = object()


def trace_step(
    task: Task,
    step_name: str,
    *,
    prompt: str | None = None,
    **kwargs: Any,
) -> None:
    prompt_messages = kwargs.pop("prompt_messages", None)
    if prompt_messages is None and prompt is not None:
        prompt_messages = (ChatMessage(role="user", content=prompt),)
    _runtime_trace_step(
        task,
        step_name,
        prompt_messages=prompt_messages,
        **kwargs,
    )


def _normalize_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    return _WHITESPACE_RE.sub(" ", s.strip().casefold())


def _overlay_rich_schema(
    base: Any,
    refined: Any,
    *,
    path: str = "",
) -> Any:
    """
    Merge refinement onto base for the same tree shape. Only description/title/
    validation-related keys are copied from refined. Structure must match.
    """
    if isinstance(base, dict) and isinstance(refined, dict):
        if base.get("type") != refined.get("type") and "type" in base and "type" in refined:
            # Prefer base structure if types diverge — preserves API validity.
            merged = dict(base)
        else:
            merged = dict(base)
        overlay_keys = {
            "description",
            "title",
            "pattern",
            "minLength",
            "maxLength",
            "minimum",
            "maximum",
            "enum",
            "format",
            "additionalProperties",
        }
        for k, v in refined.items():
            if k in overlay_keys and k not in merged:
                merged[k] = v
            elif k in overlay_keys and k in merged:
                merged[k] = v
        if base.get("type") == "object" and isinstance(base.get("properties"), dict):
            merged_props = dict(base["properties"])
            ref_props = refined.get("properties") if isinstance(refined.get("properties"), dict) else {}
            for name, b_sch in merged_props.items():
                if name in ref_props:
                    merged_props[name] = _overlay_rich_schema(
                        b_sch, ref_props[name], path=f"{path}.{name}" if path else name
                    )
            merged["properties"] = merged_props
        if base.get("type") == "array":
            b_items = base.get("items")
            r_items = refined.get("items")
            if isinstance(b_items, dict) and isinstance(r_items, dict):
                merged["items"] = _overlay_rich_schema(
                    b_items, r_items, path=f"{path}[]"
                )
        return merged
    return base


def _collect_required_paths(schema: Mapping[str, Any], prefix: str = "") -> List[str]:
    req: List[str] = []
    typ = schema.get("type")
    if typ == "object" and isinstance(schema.get("properties"), dict):
        required = set(schema.get("required") or [])
        for name, sub in schema["properties"].items():
            p = f"{prefix}.{name}" if prefix else name
            if name in required:
                req.append(p)
            req.extend(_collect_required_paths(sub, p))
    elif typ == "array" and isinstance(schema.get("items"), dict):
        req.extend(_collect_required_paths(schema["items"], f"{prefix}[]"))
    return req


def _get_at_path(data: Any, dotted: str) -> Any:
    if not dotted:
        return data
    parts = dotted.replace("[]", ".[]").split(".")
    cur: Any = data
    for part in parts:
        if part == "[]":
            if not isinstance(cur, list):
                return _MISSING
            if not cur:
                return _MISSING
            cur = cur[0]
        else:
            if not isinstance(cur, dict) or part not in cur:
                return _MISSING
            cur = cur[part]
    return cur


def _missing_required_errors(schema: Mapping[str, Any], data: Any) -> List[str]:
    errs: List[str] = []
    for path in _collect_required_paths(schema):
        val = _get_at_path(data, path)
        if val is _MISSING or val is None:
            errs.append(f"Missing or null required value at '{path}'")
    return errs


def _value_grounded_in_text(input_text: str, value: Any) -> bool:
    haystack = _normalize_text(input_text)
    if value is None:
        return True
    if isinstance(value, bool):
        if value:
            return "true" in haystack or "yes" in haystack
        return "false" in haystack or "no" in haystack
    if isinstance(value, (int, float)):
        s = str(value)
        if s in haystack.replace(",", ""):
            return True
        if isinstance(value, float) and value.is_integer():
            return str(int(value)) in haystack.replace(",", "")
        return s in haystack
    if isinstance(value, str):
        if not value.strip():
            return False
        return _normalize_text(value) in haystack
    if isinstance(value, dict):
        return all(_value_grounded_in_text(input_text, v) for v in value.values())
    if isinstance(value, list):
        return all(_value_grounded_in_text(input_text, v) for v in value)
    return True


def _rule_errors(schema: Mapping[str, Any], data: Any, path: str = "") -> List[str]:
    errs: List[str] = []
    typ = schema.get("type")

    if typ == "object" and isinstance(schema.get("properties"), dict):
        if not isinstance(data, dict):
            return [f"At {path or '$'}: expected object, got {type(data).__name__}"]
        for name, subschema in schema["properties"].items():
            if name not in data:
                continue
            errs.extend(
                _rule_errors(
                    subschema,
                    data[name],
                    f"{path}.{name}" if path else name,
                )
            )
    elif typ == "array":
        if not isinstance(data, list):
            return [f"At {path or '$'}: expected array"]
        items_s = schema.get("items")
        if isinstance(items_s, dict):
            for i, item in enumerate(data):
                errs.extend(
                    _rule_errors(items_s, item, f"{path}[{i}]" if path else f"[{i}]")
                )
    else:
        if "enum" in schema and isinstance(schema["enum"], list):
            if data not in schema["enum"]:
                errs.append(
                    f"At {path or '$'}: value {data!r} not in enum {schema['enum']}"
                )
        if isinstance(data, str):
            if isinstance(schema.get("minLength"), int) and len(data) < schema["minLength"]:
                errs.append(
                    f"At {path or '$'}: string shorter than minLength {schema['minLength']}"
                )
            if isinstance(schema.get("maxLength"), int) and len(data) > schema["maxLength"]:
                errs.append(
                    f"At {path or '$'}: string longer than maxLength {schema['maxLength']}"
                )
            pat = schema.get("pattern")
            if isinstance(pat, str):
                if not re.search(pat, data):
                    errs.append(f"At {path or '$'}: pattern mismatch for {data!r}")
    return errs


def _grounding_errors(schema: Mapping[str, Any], data: Any, input_text: str) -> List[str]:
    errs: List[str] = []
    typ = schema.get("type")
    if typ == "object" and isinstance(schema.get("properties"), dict):
        if not isinstance(data, dict):
            return errs
        for name, subschema in schema["properties"].items():
            if name not in data:
                continue
            errs.extend(
                _grounding_errors(subschema, data[name], input_text)
            )
    elif typ == "array":
        if isinstance(data, list) and isinstance(schema.get("items"), dict):
            for item in data:
                errs.extend(_grounding_errors(schema["items"], item, input_text))
    else:
        if isinstance(data, str) and data and not _value_grounded_in_text(input_text, data):
            errs.append(
                f"Grounding: value at leaf is not supported by TEXT: {data!r}"
            )
    return errs


def _validate_scope(
    input_text: str,
    base_schema: Mapping[str, Any],
    rules_schema: Mapping[str, Any],
    data: Any,
) -> List[str]:
    """
    Required keys follow the evaluator contract (base_schema). Grounding and rule
    checks use the ARCHITECT-enriched schema (patterns, minLength, etc.).
    """
    errors: List[str] = []
    errors.extend(_missing_required_errors(base_schema, data))
    errors.extend(_grounding_errors(rules_schema, data, input_text))
    errors.extend(_rule_errors(rules_schema, data))
    return errors


@dataclass
class _ArchitectResult:
    optimized_schema: Dict[str, Any]
    raw_response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ParseAgent:
    """
    PARSE-inspired agent: ARCHITECT (schema refine) → SCOPE (strict extract +
    guardrails + reflection) → RELAY (overlay merge guarantees original shape).
    """

    def __init__(self) -> None:
        import os

        timeout_s = float(os.getenv("OPENAI_TIMEOUT_S", "120"))
        self.client = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
            timeout=timeout_s,
        )

    def run(self, task: Task, model: str) -> Dict[str, Any]:
        import os

        from gensie.baseline import (  # noqa: PLC0415 — avoid circular import
            _create_chat_completion,
            _env_bool,
            _env_int,
        )

        skip_architect = _env_bool("GENSIE_PARSE_SKIP_ARCHITECT", False)
        max_retries = _env_int("GENSIE_PARSE_SCOPE_MAX_RETRIES", 3, minimum=0)

        base_schema = task.target_schema
        architect = _ArchitectResult(optimized_schema=dict(base_schema))

        if not skip_architect:
            architect = self._architect_optimize(task, model, base_schema)
            merged = architect.optimized_schema
        else:
            merged = dict(base_schema)

        extraction_schema = merged
        trace = {
            "architect": {
                "skipped": skip_architect,
                "error": architect.error,
                "merged_keys": list((extraction_schema.get("properties") or {}).keys())
                if extraction_schema.get("type") == "object"
                else None,
            }
        }

        user_base = (
            f"{task.instruction}\n\n"
            f"SCHEMA:\n{json.dumps(extraction_schema, indent=2)}\n\n"
            f"TEXT:\n{task.input_text}"
        )

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": _SCOPE_SYSTEM},
            {"role": "user", "content": user_base},
        ]
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "parse_scope_extraction",
                "schema": require_all_json_schema_properties(base_schema),
                "strict": True,
            },
        }

        last_errors: List[str] = []
        last_payload: Optional[Dict[str, Any]] = None
        started_at = datetime.now(timezone.utc)
        perf_start = time.perf_counter()

        for attempt in range(max_retries + 1):
            request_payload = {
                "model": model,
                "messages": messages,
                "response_format": response_format,
                "attempt": attempt,
            }
            try:
                response = _create_chat_completion(
                    self.client,
                    model=model,
                    messages=messages,
                    response_format=response_format,
                )
            except Exception as e:
                err_msg = str(e) or repr(e)
                if os.getenv("OPENAI_BASE_URL"):
                    err_msg = f"{err_msg} (OPENAI_BASE_URL={os.getenv('OPENAI_BASE_URL')})"
                trace_step(
                    task,
                    f"parse_scope_attempt_{attempt + 1:02d}",
                    prompt=user_base,
                    request_payload=request_payload,
                    error=err_msg,
                    metrics={
                        "tokens": {},
                        "timings": {
                            "started_at": started_at.isoformat(),
                            "completed_at": datetime.now(timezone.utc).isoformat(),
                        },
                    },
                )
                return {"error": err_msg}

            raw_response = (
                response.model_dump()
                if hasattr(response, "model_dump")
                else {"raw": str(response)}
            )
            usage = raw_response.get("usage") or {}

            try:
                content = response.choices[0].message.content
                data = json.loads(content)
            except Exception as e:
                last_errors = [f"JSON parse: {e}"]
                trace_step(
                    task,
                    f"parse_scope_attempt_{attempt + 1:02d}",
                    prompt=user_base,
                    request_payload=request_payload,
                    response_payload=raw_response,
                    error=str(e),
                    metrics={
                        "tokens": {"usage": usage},
                        "timings": {},
                    },
                )
                if response.choices[0].message.content:
                    messages.append(
                        {
                            "role": "assistant",
                            "content": response.choices[0].message.content,
                        }
                    )
                messages.append(
                    {
                        "role": "user",
                        "content": _REFLECTION_USER_PREFIX
                        + "\n".join(last_errors),
                    }
                )
                continue

            # SCOPE guardrails: required keys vs base_schema; rules vs enriched schema
            validation_errors = _validate_scope(
                task.input_text, base_schema, extraction_schema, data
            )
            last_payload = data

            trace_step(
                task,
                f"parse_scope_attempt_{attempt + 1:02d}",
                prompt=user_base,
                request_payload=request_payload,
                response_payload={
                    "api_response": raw_response,
                    "parsed": data,
                    "validation_errors": validation_errors,
                    "trace": trace,
                },
                error=None if not validation_errors else "; ".join(validation_errors),
                metrics={
                    "tokens": {
                        "prompt_tokens": usage.get("prompt_tokens"),
                        "completion_tokens": usage.get("completion_tokens"),
                        "total_tokens": usage.get("total_tokens"),
                    },
                    "timings": {
                        "total_duration_ms": round(
                            (time.perf_counter() - perf_start) * 1000, 3
                        ),
                    },
                },
            )

            if not validation_errors:
                relay = self._relay_identity(base_schema, data)
                trace_step(
                    task,
                    "parse_relay",
                    prompt="identity relay (structure preserved)",
                    request_payload={"mode": "identity"},
                    response_payload={"output": relay, "trace": trace},
                    metrics={
                        "request": {"is_model_request": False},
                        "tokens": {},
                        "timings": {},
                    },
                )
                return relay

            last_errors = validation_errors
            messages.append(
                {"role": "assistant", "content": json.dumps(data, ensure_ascii=False)}
            )
            messages.append(
                {
                    "role": "user",
                    "content": _REFLECTION_USER_PREFIX + "\n".join(validation_errors),
                }
            )

        return last_payload if last_payload is not None else {"error": "; ".join(last_errors)}

    def _relay_identity(self, original_schema: Mapping[str, Any], data: Any) -> Any:
        """RELAY: when shapes align, output already matches the submission schema."""
        if isinstance(data, Mapping):
            return coerce_nullable_string_nulls(dict(data), dict(original_schema))
        return data

    def _architect_optimize(
        self, task: Task, model: str, base_schema: Dict[str, Any]
    ) -> _ArchitectResult:
        from gensie.baseline import _create_chat_completion  # noqa: PLC0415

        user_prompt = (
            f"Task instruction:\n{task.instruction}\n\n"
            f"Original JSON Schema to refine (preserve structure):\n"
            f"{json.dumps(base_schema, indent=2)}"
        )
        messages = [
            {"role": "system", "content": _ARCHITECT_SYSTEM},
            {"role": "user", "content": user_prompt},
        ]
        started_at = datetime.now(timezone.utc)
        try:
            response = _create_chat_completion(
                self.client,
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
            )
            raw = (
                response.model_dump()
                if hasattr(response, "model_dump")
                else {"raw": str(response)}
            )
            content = response.choices[0].message.content
            parsed = json.loads(content)
            opt = parsed.get("optimized_schema")
            if not isinstance(opt, dict):
                return _ArchitectResult(
                    optimized_schema=dict(base_schema),
                    raw_response=raw,
                    error="ARCHITECT output missing optimized_schema object",
                )
            merged = _overlay_rich_schema(base_schema, opt)
            trace_step(
                task,
                "parse_architect",
                prompt=user_prompt,
                request_payload={"model": model, "messages": messages},
                response_payload={"api_response": raw, "optimized_schema": opt, "merged": merged},
                metrics={
                    "tokens": {
                        "prompt_tokens": (raw.get("usage") or {}).get("prompt_tokens"),
                        "completion_tokens": (raw.get("usage") or {}).get(
                            "completion_tokens"
                        ),
                        "total_tokens": (raw.get("usage") or {}).get("total_tokens"),
                    },
                    "timings": {"started_at": started_at.isoformat()},
                },
            )
            return _ArchitectResult(optimized_schema=merged, raw_response=raw, error=None)
        except Exception as e:
            trace_step(
                task,
                "parse_architect",
                prompt=user_prompt,
                request_payload={"model": model, "messages": messages},
                error=str(e),
                metrics={"timings": {"started_at": started_at.isoformat()}},
            )
            return _ArchitectResult(optimized_schema=dict(base_schema), error=str(e))


class ParsePipelineAgent(GenSIEAgent):
    def __init__(self) -> None:
        self._inner = ParseAgent()

    def run(self, task: Task, model: str) -> Dict[str, Any]:
        return self._inner.run(task, model)
