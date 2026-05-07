import os
import json
import time
import threading
from datetime import datetime, timezone
from typing import Any, Dict
from openai import OpenAI
from gensie.agent import GenSIEAgent, Participant, ParticipantInfo, PipelineInfo
from gensie.task import Task
from gensie.tracing import trace_step
from gensie.schema_enrichment import build_enriched_prompt
from gensie.prompting import (
    SIMPLE_CLEAN_SCHEMA_SYSTEM_PROMPT,
    build_simple_clean_schema_prompt,
)
from gensie.inline_reasoning import (
    INLINE_REASONING_SYSTEM_PROMPT,
    build_inline_reasoning_prompt,
    build_inline_reasoning_schema,
    unwrap_inline_reasoning_output,
)
from gensie.enriched_inline_reasoning import (
    ENRICHED_INLINE_REASONING_SYSTEM_PROMPT,
    build_enriched_inline_reasoning_prompt,
)
from gensie.self_consistency import (
    SchemaAwareSelfConsistencyAggregator,
    SelfConsistencyConfig,
    TrialBudgetConfig,
    TrialBudgetPlanner,
    build_string_similarity_from_env,
)
from dotenv import load_dotenv
from logging import getLogger

load_dotenv()
logger = getLogger("gensie")

DEFAULT_OPENAI_REQUEST_DELAY_S = 3.0
_OPENAI_REQUEST_LOCK = threading.Lock()
_OPENAI_LAST_REQUEST_STARTED_AT = 0.0


def _get_openai_request_delay_s() -> float:
    raw_value = os.getenv(
        "OPENAI_REQUEST_DELAY_S", str(DEFAULT_OPENAI_REQUEST_DELAY_S)
    )
    try:
        return max(float(raw_value), 0.0)
    except ValueError:
        logger.warning(
            "Invalid OPENAI_REQUEST_DELAY_S=%r; using %.1f seconds.",
            raw_value,
            DEFAULT_OPENAI_REQUEST_DELAY_S,
        )
        return DEFAULT_OPENAI_REQUEST_DELAY_S


def _create_chat_completion(client: OpenAI, **kwargs: Any) -> Any:
    delay_s = _get_openai_request_delay_s()
    if delay_s > 0:
        global _OPENAI_LAST_REQUEST_STARTED_AT
        with _OPENAI_REQUEST_LOCK:
            now = time.monotonic()
            wait_s = (_OPENAI_LAST_REQUEST_STARTED_AT + delay_s) - now
            if wait_s > 0:
                time.sleep(wait_s)
            _OPENAI_LAST_REQUEST_STARTED_AT = time.monotonic()

    return client.chat.completions.create(**kwargs)


def _env_int(name: str, default: int, *, minimum: int = 0) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return max(int(raw_value), minimum)
    except ValueError:
        logger.warning("Invalid %s=%r; using %r.", name, raw_value, default)
        return default


def _env_float(name: str, default: float, *, minimum: float = 0.0) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return max(float(raw_value), minimum)
    except ValueError:
        logger.warning("Invalid %s=%r; using %r.", name, raw_value, default)
        return default


def _env_optional_float(name: str) -> float | None:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return None
    try:
        return float(raw_value)
    except ValueError:
        logger.warning("Invalid %s=%r; ignoring it.", name, raw_value)
        return None


def _env_optional_int(name: str) -> int | None:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return None
    try:
        return int(raw_value)
    except ValueError:
        logger.warning("Invalid %s=%r; ignoring it.", name, raw_value)
        return None


def _env_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


class BasicAgent(GenSIEAgent):
    """
    Reference implementation using OpenAI Structured Outputs.
    Configurable via environment variables:
    - OPENAI_BASE_URL: (Optional) Custom endpoint for local LLMs.
    - OPENAI_API_KEY: (Required) Your API key.
    """

    def __init__(self):
        self.client = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
        )

    def run(self, task: Task, model: str) -> Dict[str, Any]:
        """
        Executes the extraction using OpenAI's response_format for strict schema compliance.
        """
        prompt = task.get_input_prompt()
        messages = [
            {
                "role": "system",
                "content": "You are a precise data extraction agent.",
            },
            {"role": "user", "content": prompt},
        ]
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "extraction",
                "schema": task.target_schema,
                "strict": True,
            },
        }
        request_payload = {
            "model": model,
            "messages": messages,
            "response_format": response_format,
        }

        started_at = datetime.now(timezone.utc)
        started_perf = time.perf_counter()

        try:
            # Call OpenAI with the task's JSON schema
            response = _create_chat_completion(
                self.client,
                model=model,
                messages=messages,
                response_format=response_format,
            )
            completed_at = datetime.now(timezone.utc)
            duration_ms = (time.perf_counter() - started_perf) * 1000
            raw_response = (
                response.model_dump()
                if hasattr(response, "model_dump")
                else {"raw": str(response)}
            )
            usage = raw_response.get("usage") or {}
            trace_step(
                task,
                "extract",
                prompt=prompt,
                request_payload=request_payload,
                response_payload=raw_response,
                metrics={
                    "tokens": {
                        "prompt_tokens": usage.get("prompt_tokens"),
                        "completion_tokens": usage.get("completion_tokens"),
                        "total_tokens": usage.get("total_tokens"),
                    },
                    "timings": {
                        "started_at": started_at.isoformat(),
                        "completed_at": completed_at.isoformat(),
                        "total_duration_ms": round(duration_ms, 3),
                        "time_to_first_token_ms": None,
                        "time_to_first_token_note": "Not captured by the current non-streaming baseline.",
                    },
                },
            )
        except Exception as e:
            completed_at = datetime.now(timezone.utc)
            duration_ms = (time.perf_counter() - started_perf) * 1000
            trace_step(
                task,
                "extract",
                prompt=prompt,
                request_payload=request_payload,
                error=str(e),
                metrics={
                    "tokens": {
                        "prompt_tokens": None,
                        "completion_tokens": None,
                        "total_tokens": None,
                    },
                    "timings": {
                        "started_at": started_at.isoformat(),
                        "completed_at": completed_at.isoformat(),
                        "total_duration_ms": round(duration_ms, 3),
                        "time_to_first_token_ms": None,
                        "time_to_first_token_note": "Not captured by the current non-streaming baseline.",
                    },
                },
            )
            raise

        # Parse the structured JSON response
        try:
            content = response.choices[0].message.content
            return json.loads(content)
        except (json.JSONDecodeError, AttributeError, IndexError) as e:
            # Fallback for unexpected API errors
            return {"error": f"Failed to parse model response: {str(e)}"}
        except Exception as e:
            logger.error(str(e))
            return {"error": str(e)}


class EnrichedSchemaAgent(GenSIEAgent):
    """
    A variant of the baseline that injects an enriched schema representation
    (field cards + pydantic-like code + raw schema) into the user prompt.
    The response_format schema remains the original task.target_schema.
    """

    def __init__(self):
        timeout_s = float(os.getenv("OPENAI_TIMEOUT_S", "120"))
        self.client = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
            timeout=timeout_s,
        )

    def run(self, task: Task, model: str) -> Dict[str, Any]:
        prompt = build_enriched_prompt(
            instruction=task.instruction,
            input_text=task.input_text,
            target_schema=task.target_schema,
            rules=[],
        )
        system_prompt = "\n".join(
            [
                "You are a precise, grounded data extraction agent.",
                "",
                "Primary objective: maximize schema coverage WITHOUT hallucinating.",
                "",
                "Rules:",
                "- Include EVERY required field (never omit required keys).",
                "- For optional fields: include the key if the TEXT supports a value; otherwise follow schema nullability:",
                "  - If the field allows null: use null when not supported by TEXT.",
                "  - If the field does NOT allow null: omit the key when not supported by TEXT.",
                "- Enums: output must match exactly one of the allowed literals (case-sensitive).",
                "- Numbers/booleans/dates: do not guess; if not supported by TEXT => null (only if allowed) or omit.",
                "- Output ONLY a valid JSON object (no markdown, no extra keys).",
            ]
        )
        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {"role": "user", "content": prompt},
        ]
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "extraction",
                "schema": task.target_schema,
                "strict": True,
            },
        }
        request_payload = {
            "model": model,
            "messages": messages,
            "response_format": response_format,
        }

        started_at = datetime.now(timezone.utc)
        started_perf = time.perf_counter()

        try:
            response = _create_chat_completion(
                self.client,
                model=model,
                messages=messages,
                response_format=response_format,
            )
            completed_at = datetime.now(timezone.utc)
            duration_ms = (time.perf_counter() - started_perf) * 1000
            raw_response = (
                response.model_dump()
                if hasattr(response, "model_dump")
                else {"raw": str(response)}
            )
            usage = raw_response.get("usage") or {}
            trace_step(
                task,
                "extract",
                prompt=prompt,
                request_payload=request_payload,
                response_payload=raw_response,
                metrics={
                    "tokens": {
                        "prompt_tokens": usage.get("prompt_tokens"),
                        "completion_tokens": usage.get("completion_tokens"),
                        "total_tokens": usage.get("total_tokens"),
                    },
                    "timings": {
                        "started_at": started_at.isoformat(),
                        "completed_at": completed_at.isoformat(),
                        "total_duration_ms": round(duration_ms, 3),
                        "time_to_first_token_ms": None,
                        "time_to_first_token_note": "Not captured by the current non-streaming baseline.",
                    },
                },
            )
        except Exception as e:
            base_url = os.getenv("OPENAI_BASE_URL")
            err_msg = str(e) or repr(e)
            if base_url:
                err_msg = f"{err_msg} (OPENAI_BASE_URL={base_url})"
            completed_at = datetime.now(timezone.utc)
            duration_ms = (time.perf_counter() - started_perf) * 1000
            trace_step(
                task,
                "extract",
                prompt=prompt,
                request_payload=request_payload,
                error=err_msg,
                metrics={
                    "tokens": {
                        "prompt_tokens": None,
                        "completion_tokens": None,
                        "total_tokens": None,
                    },
                    "timings": {
                        "started_at": started_at.isoformat(),
                        "completed_at": completed_at.isoformat(),
                        "total_duration_ms": round(duration_ms, 3),
                        "time_to_first_token_ms": None,
                        "time_to_first_token_note": "Not captured by the current non-streaming baseline.",
                    },
                },
            )
            raise RuntimeError(err_msg) from e

        try:
            content = response.choices[0].message.content
            return json.loads(content)
        except (json.JSONDecodeError, AttributeError, IndexError) as e:
            return {"error": f"Failed to parse model response: {str(e)}"}
        except Exception as e:
            logger.error(str(e))
            return {"error": str(e)}


class SimpleCleanSchemaAgent(GenSIEAgent):
    """
    Cheap baseline-plus pipeline: one model call, original schema for structured
    output, and a cleaned schema representation in the prompt.
    """

    def __init__(self):
        timeout_s = float(os.getenv("OPENAI_TIMEOUT_S", "120"))
        self.client = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
            timeout=timeout_s,
        )

    def run(self, task: Task, model: str) -> Dict[str, Any]:
        prompt = build_simple_clean_schema_prompt(task)
        messages = [
            {
                "role": "system",
                "content": SIMPLE_CLEAN_SCHEMA_SYSTEM_PROMPT,
            },
            {"role": "user", "content": prompt},
        ]
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "extraction",
                "schema": task.target_schema,
                "strict": True,
            },
        }
        request_payload = {
            "model": model,
            "messages": messages,
            "response_format": response_format,
        }

        started_at = datetime.now(timezone.utc)
        started_perf = time.perf_counter()

        try:
            response = _create_chat_completion(
                self.client,
                model=model,
                messages=messages,
                response_format=response_format,
            )
            completed_at = datetime.now(timezone.utc)
            duration_ms = (time.perf_counter() - started_perf) * 1000
            raw_response = (
                response.model_dump()
                if hasattr(response, "model_dump")
                else {"raw": str(response)}
            )
            usage = raw_response.get("usage") or {}
            trace_step(
                task,
                "extract",
                prompt=prompt,
                request_payload=request_payload,
                response_payload=raw_response,
                metrics={
                    "tokens": {
                        "prompt_tokens": usage.get("prompt_tokens"),
                        "completion_tokens": usage.get("completion_tokens"),
                        "total_tokens": usage.get("total_tokens"),
                    },
                    "timings": {
                        "started_at": started_at.isoformat(),
                        "completed_at": completed_at.isoformat(),
                        "total_duration_ms": round(duration_ms, 3),
                        "time_to_first_token_ms": None,
                        "time_to_first_token_note": "Not captured by the current non-streaming pipeline.",
                    },
                },
            )
        except Exception as e:
            base_url = os.getenv("OPENAI_BASE_URL")
            err_msg = str(e) or repr(e)
            if base_url:
                err_msg = f"{err_msg} (OPENAI_BASE_URL={base_url})"
            completed_at = datetime.now(timezone.utc)
            duration_ms = (time.perf_counter() - started_perf) * 1000
            trace_step(
                task,
                "extract",
                prompt=prompt,
                request_payload=request_payload,
                error=err_msg,
                metrics={
                    "tokens": {
                        "prompt_tokens": None,
                        "completion_tokens": None,
                        "total_tokens": None,
                    },
                    "timings": {
                        "started_at": started_at.isoformat(),
                        "completed_at": completed_at.isoformat(),
                        "total_duration_ms": round(duration_ms, 3),
                        "time_to_first_token_ms": None,
                        "time_to_first_token_note": "Not captured by the current non-streaming pipeline.",
                    },
                },
            )
            raise RuntimeError(err_msg) from e

        try:
            content = response.choices[0].message.content
            return json.loads(content)
        except (json.JSONDecodeError, AttributeError, IndexError) as e:
            return {"error": f"Failed to parse model response: {str(e)}"}
        except Exception as e:
            logger.error(str(e))
            return {"error": str(e)}


class InlineReasoningAgent(GenSIEAgent):
    """
    One-call pipeline that constrains generation to top-level field wrappers
    with reasoning plus final value, then returns only the values.
    """

    def __init__(self):
        timeout_s = float(os.getenv("OPENAI_TIMEOUT_S", "120"))
        self.client = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
            timeout=timeout_s,
        )

    def run(self, task: Task, model: str) -> Dict[str, Any]:
        prompt = build_inline_reasoning_prompt(task)
        reasoning_schema = build_inline_reasoning_schema(task.target_schema)
        messages = [
            {
                "role": "system",
                "content": INLINE_REASONING_SYSTEM_PROMPT,
            },
            {"role": "user", "content": prompt},
        ]
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "inline_reasoning_extraction",
                "schema": reasoning_schema,
                "strict": True,
            },
        }
        request_payload = {
            "model": model,
            "messages": messages,
            "response_format": response_format,
        }

        started_at = datetime.now(timezone.utc)
        started_perf = time.perf_counter()
        response = None
        raw_response = None

        try:
            response = _create_chat_completion(
                self.client,
                model=model,
                messages=messages,
                response_format=response_format,
            )
            completed_at = datetime.now(timezone.utc)
            duration_ms = (time.perf_counter() - started_perf) * 1000
            raw_response = (
                response.model_dump()
                if hasattr(response, "model_dump")
                else {"raw": str(response)}
            )
            usage = raw_response.get("usage") or {}
        except Exception as e:
            base_url = os.getenv("OPENAI_BASE_URL")
            err_msg = str(e) or repr(e)
            if base_url:
                err_msg = f"{err_msg} (OPENAI_BASE_URL={base_url})"
            completed_at = datetime.now(timezone.utc)
            duration_ms = (time.perf_counter() - started_perf) * 1000
            trace_step(
                task,
                "extract",
                prompt=prompt,
                request_payload=request_payload,
                error=err_msg,
                metrics={
                    "tokens": {
                        "prompt_tokens": None,
                        "completion_tokens": None,
                        "total_tokens": None,
                    },
                    "timings": {
                        "started_at": started_at.isoformat(),
                        "completed_at": completed_at.isoformat(),
                        "total_duration_ms": round(duration_ms, 3),
                        "time_to_first_token_ms": None,
                        "time_to_first_token_note": "Not captured by the current non-streaming pipeline.",
                    },
                },
            )
            raise RuntimeError(err_msg) from e

        try:
            content = response.choices[0].message.content
            inline_output = json.loads(content)
            final_output = unwrap_inline_reasoning_output(
                inline_output, task.target_schema
            )
        except (json.JSONDecodeError, AttributeError, IndexError, ValueError) as e:
            trace_step(
                task,
                "extract",
                prompt=prompt,
                request_payload=request_payload,
                response_payload=raw_response,
                error=str(e),
                metrics={
                    "tokens": {
                        "prompt_tokens": usage.get("prompt_tokens"),
                        "completion_tokens": usage.get("completion_tokens"),
                        "total_tokens": usage.get("total_tokens"),
                    },
                    "timings": {
                        "started_at": started_at.isoformat(),
                        "completed_at": completed_at.isoformat(),
                        "total_duration_ms": round(duration_ms, 3),
                        "time_to_first_token_ms": None,
                        "time_to_first_token_note": "Not captured by the current non-streaming pipeline.",
                    },
                },
            )
            return {"error": f"Failed to parse inline reasoning response: {str(e)}"}
        except Exception as e:
            logger.error(str(e))
            return {"error": str(e)}

        trace_step(
            task,
            "extract",
            prompt=prompt,
            request_payload=request_payload,
            response_payload={
                "api_response": raw_response,
                "inline_reasoning_output": inline_output,
                "final_output": final_output,
            },
            metrics={
                "tokens": {
                    "prompt_tokens": usage.get("prompt_tokens"),
                    "completion_tokens": usage.get("completion_tokens"),
                    "total_tokens": usage.get("total_tokens"),
                },
                "timings": {
                    "started_at": started_at.isoformat(),
                    "completed_at": completed_at.isoformat(),
                    "total_duration_ms": round(duration_ms, 3),
                    "time_to_first_token_ms": None,
                    "time_to_first_token_note": "Not captured by the current non-streaming pipeline.",
                },
            },
        )
        return final_output


class EnrichedInlineReasoningAgent(GenSIEAgent):
    """
    One-call pipeline that combines inline reasoning wrappers with a compact
    Pydantic-like schema representation using Reasoned[T] and Nullable[T].
    """

    def __init__(self):
        timeout_s = float(os.getenv("OPENAI_TIMEOUT_S", "120"))
        self.client = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
            timeout=timeout_s,
        )

    def run(self, task: Task, model: str) -> Dict[str, Any]:
        prompt = build_enriched_inline_reasoning_prompt(task)
        reasoning_schema = build_inline_reasoning_schema(task.target_schema)
        messages = [
            {
                "role": "system",
                "content": ENRICHED_INLINE_REASONING_SYSTEM_PROMPT,
            },
            {"role": "user", "content": prompt},
        ]
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "enriched_inline_reasoning_extraction",
                "schema": reasoning_schema,
                "strict": True,
            },
        }
        request_payload = {
            "model": model,
            "messages": messages,
            "response_format": response_format,
        }

        started_at = datetime.now(timezone.utc)
        started_perf = time.perf_counter()
        response = None
        raw_response = None

        try:
            response = _create_chat_completion(
                self.client,
                model=model,
                messages=messages,
                response_format=response_format,
            )
            completed_at = datetime.now(timezone.utc)
            duration_ms = (time.perf_counter() - started_perf) * 1000
            raw_response = (
                response.model_dump()
                if hasattr(response, "model_dump")
                else {"raw": str(response)}
            )
            usage = raw_response.get("usage") or {}
        except Exception as e:
            base_url = os.getenv("OPENAI_BASE_URL")
            err_msg = str(e) or repr(e)
            if base_url:
                err_msg = f"{err_msg} (OPENAI_BASE_URL={base_url})"
            completed_at = datetime.now(timezone.utc)
            duration_ms = (time.perf_counter() - started_perf) * 1000
            trace_step(
                task,
                "extract",
                prompt=prompt,
                request_payload=request_payload,
                error=err_msg,
                metrics={
                    "tokens": {
                        "prompt_tokens": None,
                        "completion_tokens": None,
                        "total_tokens": None,
                    },
                    "timings": {
                        "started_at": started_at.isoformat(),
                        "completed_at": completed_at.isoformat(),
                        "total_duration_ms": round(duration_ms, 3),
                        "time_to_first_token_ms": None,
                        "time_to_first_token_note": "Not captured by the current non-streaming pipeline.",
                    },
                },
            )
            raise RuntimeError(err_msg) from e

        try:
            content = response.choices[0].message.content
            inline_output = json.loads(content)
            final_output = unwrap_inline_reasoning_output(
                inline_output, task.target_schema
            )
        except (json.JSONDecodeError, AttributeError, IndexError, ValueError) as e:
            trace_step(
                task,
                "extract",
                prompt=prompt,
                request_payload=request_payload,
                response_payload=raw_response,
                error=str(e),
                metrics={
                    "tokens": {
                        "prompt_tokens": usage.get("prompt_tokens"),
                        "completion_tokens": usage.get("completion_tokens"),
                        "total_tokens": usage.get("total_tokens"),
                    },
                    "timings": {
                        "started_at": started_at.isoformat(),
                        "completed_at": completed_at.isoformat(),
                        "total_duration_ms": round(duration_ms, 3),
                        "time_to_first_token_ms": None,
                        "time_to_first_token_note": "Not captured by the current non-streaming pipeline.",
                    },
                },
            )
            return {
                "error": f"Failed to parse enriched inline reasoning response: {str(e)}"
            }
        except Exception as e:
            logger.error(str(e))
            return {"error": str(e)}

        trace_step(
            task,
            "extract",
            prompt=prompt,
            request_payload=request_payload,
            response_payload={
                "api_response": raw_response,
                "inline_reasoning_output": inline_output,
                "final_output": final_output,
            },
            metrics={
                "tokens": {
                    "prompt_tokens": usage.get("prompt_tokens"),
                    "completion_tokens": usage.get("completion_tokens"),
                    "total_tokens": usage.get("total_tokens"),
                },
                "timings": {
                    "started_at": started_at.isoformat(),
                    "completed_at": completed_at.isoformat(),
                    "total_duration_ms": round(duration_ms, 3),
                    "time_to_first_token_ms": None,
                    "time_to_first_token_note": "Not captured by the current non-streaming pipeline.",
                },
            },
        )
        return final_output


class EnrichedInlineReasoningSelfConsistencyAgent(GenSIEAgent):
    """
    Multi-sample variant of enriched-inline-reasoning.

    Each trial uses the same strict inline reasoning schema. Final values are
    aggregated field-by-field with a schema-aware self-consistency aggregator.
    """

    def __init__(self):
        timeout_s = float(os.getenv("OPENAI_TIMEOUT_S", "120"))
        self.client = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
            timeout=timeout_s,
        )
        self.aggregator = SchemaAwareSelfConsistencyAggregator(
            config=self._build_aggregation_config(),
            string_similarity=build_string_similarity_from_env(),
        )
        self.trial_planner = TrialBudgetPlanner(self._build_trial_budget_config())

    def run(self, task: Task, model: str) -> Dict[str, Any]:
        prompt = build_enriched_inline_reasoning_prompt(task)
        reasoning_schema = build_inline_reasoning_schema(task.target_schema)
        messages = [
            {
                "role": "system",
                "content": ENRICHED_INLINE_REASONING_SYSTEM_PROMPT,
            },
            {"role": "user", "content": prompt},
        ]
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "enriched_inline_reasoning_self_consistency",
                "schema": reasoning_schema,
                "strict": True,
            },
        }
        prompt_token_fallback = self.trial_planner.estimate_prompt_tokens(
            messages=messages,
            response_format=response_format,
        )
        initial_budget_estimate = self.trial_planner.estimate(
            prompt_tokens=None,
            prompt_token_fallback=prompt_token_fallback,
            completion_token_samples=[],
            trial_duration_samples_s=[],
        )
        max_trials = self.trial_planner.config.max_trials
        allowed_trials = initial_budget_estimate.allowed_trials
        base_request_payload = {
            "model": model,
            "messages": messages,
            "response_format": response_format,
            "self_consistency": {
                "max_trials": max_trials,
                "initial_allowed_trials": allowed_trials,
                "trial_budget": self.trial_planner.config.__dict__,
                "initial_budget_estimate": initial_budget_estimate.__dict__,
                "string_similarity": self.aggregator.string_similarity.name,
                "config": self.aggregator.config.__dict__,
            },
        }

        trial_payloads = []
        trial_responses = []
        trial_errors = []
        final_candidates = []
        budget_estimates = [initial_budget_estimate.__dict__]
        prompt_token_samples = []
        completion_token_samples = []
        trial_duration_samples_s = []
        usage_totals = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

        for trial_index in range(max_trials):
            if trial_index >= allowed_trials:
                break

            generation_options = self._generation_options_for_trial(trial_index)
            trial_payload = {
                "trial_index": trial_index,
                "generation_options": generation_options,
            }
            trial_payloads.append(trial_payload)
            raw_response = None
            inline_output = None
            final_candidate = None
            usage = {}
            trial_error = None
            trial_started_at = datetime.now(timezone.utc)
            trial_started_perf = time.perf_counter()
            try:
                response = _create_chat_completion(
                    self.client,
                    model=model,
                    messages=messages,
                    response_format=response_format,
                    **generation_options,
                )
                raw_response = (
                    response.model_dump()
                    if hasattr(response, "model_dump")
                    else {"raw": str(response)}
                )
                usage = raw_response.get("usage") or {}
                for key in usage_totals:
                    value = usage.get(key)
                    if isinstance(value, int):
                        usage_totals[key] += value

                content = response.choices[0].message.content
                inline_output = json.loads(content)
                final_candidate = unwrap_inline_reasoning_output(
                    inline_output, task.target_schema
                )
                final_candidates.append(final_candidate)
                trial_responses.append(
                    {
                        "trial_index": trial_index,
                        "api_response": raw_response,
                        "inline_reasoning_output": inline_output,
                        "final_candidate": final_candidate,
                    }
                )
                prompt_tokens = usage.get("prompt_tokens")
                completion_tokens = usage.get("completion_tokens")
                if isinstance(prompt_tokens, int):
                    prompt_token_samples.append(prompt_tokens)
                else:
                    prompt_token_samples.append(prompt_token_fallback)
                if isinstance(completion_tokens, int):
                    completion_token_samples.append(completion_tokens)
                else:
                    completion_token_samples.append(
                        self.trial_planner.estimate_tokens_from_text(content)
                    )
            except Exception as e:
                base_url = os.getenv("OPENAI_BASE_URL")
                err_msg = str(e) or repr(e)
                if base_url:
                    err_msg = f"{err_msg} (OPENAI_BASE_URL={base_url})"
                trial_error = err_msg
                trial_errors.append(
                    {
                        "trial_index": trial_index,
                        "error": err_msg,
                        "api_response": raw_response,
                    }
                )
            finally:
                trial_completed_at = datetime.now(timezone.utc)
                trial_duration_s = time.perf_counter() - trial_started_perf
                trial_duration_samples_s.append(trial_duration_s)
                current_budget_estimate = self.trial_planner.estimate(
                    prompt_tokens=max(prompt_token_samples) if prompt_token_samples else None,
                    prompt_token_fallback=prompt_token_fallback,
                    completion_token_samples=completion_token_samples,
                    trial_duration_samples_s=trial_duration_samples_s,
                )
                allowed_trials = current_budget_estimate.allowed_trials
                budget_estimates.append(current_budget_estimate.__dict__)
                trial_response_payload = {
                    "trial_index": trial_index,
                    "api_response": raw_response,
                    "inline_reasoning_output": inline_output,
                    "final_candidate": final_candidate,
                    "budget_estimate_after_trial": current_budget_estimate.__dict__,
                    "next_allowed_trials": allowed_trials,
                }
                trace_step(
                    task,
                    f"self_consistency_trial_{trial_index + 1:02d}",
                    prompt=prompt,
                    request_payload={
                        **base_request_payload,
                        "trial_index": trial_index,
                        "generation_options": generation_options,
                        "budget_estimate_before_trial": budget_estimates[-2],
                    },
                    response_payload=trial_response_payload,
                    error=trial_error,
                    metrics={
                        "request": {
                            "is_model_request": True,
                            "trial_index": trial_index,
                        },
                        "tokens": {
                            "prompt_tokens": usage.get("prompt_tokens"),
                            "completion_tokens": usage.get("completion_tokens"),
                            "total_tokens": usage.get("total_tokens"),
                        },
                        "timings": {
                            "started_at": trial_started_at.isoformat(),
                            "completed_at": trial_completed_at.isoformat(),
                            "total_duration_ms": round(trial_duration_s * 1000, 3),
                            "time_to_first_token_ms": None,
                            "time_to_first_token_note": "Not captured by the current non-streaming pipeline.",
                        },
                    },
                )

        aggregation_started_at = datetime.now(timezone.utc)
        aggregation_started_perf = time.perf_counter()
        if not final_candidates:
            error_msg = (
                "; ".join(str(error["error"]) for error in trial_errors)
                or "No valid self-consistency trials."
            )
            aggregation_completed_at = datetime.now(timezone.utc)
            aggregation_duration_ms = (time.perf_counter() - aggregation_started_perf) * 1000
            trace_step(
                task,
                "self_consistency_aggregate",
                request_payload={
                    **base_request_payload,
                    "trial_payloads": trial_payloads,
                },
                response_payload={
                    "trials": trial_responses,
                    "trial_errors": trial_errors,
                    "budget_estimates": budget_estimates,
                },
                error=error_msg,
                metrics={
                    "request": {"is_model_request": False},
                    "tokens": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                    },
                    "timings": {
                        "started_at": aggregation_started_at.isoformat(),
                        "completed_at": aggregation_completed_at.isoformat(),
                        "total_duration_ms": round(aggregation_duration_ms, 3),
                        "time_to_first_token_ms": None,
                        "time_to_first_token_note": "Aggregation step; no model stream.",
                    },
                },
            )
            return {"error": f"Failed to run self-consistency: {error_msg}"}

        final_output, aggregation_diagnostics = self.aggregator.aggregate_with_diagnostics(
            final_candidates, task.target_schema
        )
        aggregation_completed_at = datetime.now(timezone.utc)
        aggregation_duration_ms = (time.perf_counter() - aggregation_started_perf) * 1000
        trace_step(
            task,
            "self_consistency_aggregate",
            request_payload={
                **base_request_payload,
                "trial_payloads": trial_payloads,
            },
            response_payload={
                "trials": trial_responses,
                "trial_errors": trial_errors,
                "budget_estimates": budget_estimates,
                "final_candidates": final_candidates,
                "aggregation_diagnostics": aggregation_diagnostics,
                "final_output": final_output,
            },
            error=(
                "; ".join(str(error["error"]) for error in trial_errors)
                if trial_errors
                else None
            ),
            metrics={
                "request": {"is_model_request": False},
                "tokens": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
                "timings": {
                    "started_at": aggregation_started_at.isoformat(),
                    "completed_at": aggregation_completed_at.isoformat(),
                    "total_duration_ms": round(aggregation_duration_ms, 3),
                    "time_to_first_token_ms": None,
                    "time_to_first_token_note": "Aggregation step; no model stream.",
                },
            },
        )
        return final_output

    def _generation_options_for_trial(self, trial_index: int) -> Dict[str, Any]:
        temperature = _env_float("GENSIE_SC_TEMPERATURE", 0.5, minimum=0.0)
        first_temperature = _env_optional_float("GENSIE_SC_FIRST_TEMPERATURE")
        if trial_index == 0 and first_temperature is not None:
            temperature = max(first_temperature, 0.0)

        options: Dict[str, Any] = {"temperature": temperature}
        top_p = _env_optional_float("GENSIE_SC_TOP_P")
        if top_p is not None:
            options["top_p"] = top_p
        max_tokens = _env_optional_int("GENSIE_SC_MAX_TOKENS")
        if max_tokens is not None:
            options["max_tokens"] = max_tokens
        top_k = _env_optional_int("GENSIE_SC_TOP_K")
        if top_k is not None:
            options["extra_body"] = {"top_k": top_k}
        return options

    def _build_aggregation_config(self) -> SelfConsistencyConfig:
        return SelfConsistencyConfig(
            scalar_string_threshold=_env_float(
                "GENSIE_SC_SCALAR_STRING_THRESHOLD", 0.78, minimum=0.0
            ),
            array_string_threshold=_env_float(
                "GENSIE_SC_ARRAY_STRING_THRESHOLD", 0.78, minimum=0.0
            ),
            object_item_threshold=_env_float(
                "GENSIE_SC_OBJECT_ITEM_THRESHOLD", 0.62, minimum=0.0
            ),
            simple_item_support_floor=_env_int(
                "GENSIE_SC_SIMPLE_ITEM_SUPPORT_FLOOR", 2, minimum=1
            ),
            object_item_support_floor=_env_int(
                "GENSIE_SC_OBJECT_ITEM_SUPPORT_FLOOR", 2, minimum=1
            ),
            optional_property_support_ratio=_env_float(
                "GENSIE_SC_OPTIONAL_PROPERTY_SUPPORT_RATIO", 0.50, minimum=0.0
            ),
            intra_trial_dedupe_threshold=_env_float(
                "GENSIE_SC_INTRA_TRIAL_DEDUPE_THRESHOLD", 0.96, minimum=0.0
            ),
            include_greedy_array_candidate=_env_bool(
                "GENSIE_SC_INCLUDE_GREEDY_ARRAY_CANDIDATE", True
            ),
            include_threshold_array_candidates=_env_bool(
                "GENSIE_SC_INCLUDE_THRESHOLD_ARRAY_CANDIDATES", True
            ),
            include_original_array_candidates=_env_bool(
                "GENSIE_SC_INCLUDE_ORIGINAL_ARRAY_CANDIDATES", False
            ),
            use_identity_clustering=_env_bool(
                "GENSIE_SC_USE_IDENTITY_CLUSTERING", True
            ),
            identity_min_score=_env_float(
                "GENSIE_SC_IDENTITY_MIN_SCORE", 8.0, minimum=0.0
            ),
            identity_min_margin=_env_float(
                "GENSIE_SC_IDENTITY_MIN_MARGIN", 3.0, minimum=0.0
            ),
            identity_string_threshold=_env_float(
                "GENSIE_SC_IDENTITY_STRING_THRESHOLD", 0.62, minimum=0.0
            ),
            array_selector_mode=os.getenv(
                "GENSIE_SC_ARRAY_SELECTOR", "recall_biased_mbr"
            ),
            recall_mbr_tolerance=_env_float(
                "GENSIE_SC_RECALL_MBR_TOLERANCE", 0.06, minimum=0.0
            ),
            null_wins_ties=_env_bool("GENSIE_SC_NULL_WINS_TIES", False),
        )

    def _build_trial_budget_config(self) -> TrialBudgetConfig:
        legacy_trials = _env_optional_int("GENSIE_SC_TRIALS")
        default_max_trials = (
            legacy_trials if legacy_trials is not None else TrialBudgetConfig().max_trials
        )
        max_trials = _env_int(
            "GENSIE_SC_MAX_TRIALS", default_max_trials, minimum=1
        )
        min_trials = min(
            _env_int("GENSIE_SC_MIN_TRIALS", 1, minimum=1),
            max_trials,
        )
        return TrialBudgetConfig(
            max_trials=max_trials,
            min_trials=min_trials,
            dynamic_trials=_env_bool("GENSIE_SC_DYNAMIC_TRIALS", True),
            token_budget=_env_int("GENSIE_SC_TOKEN_BUDGET", 32000, minimum=1),
            token_budget_ratio=_env_float(
                "GENSIE_SC_TOKEN_BUDGET_RATIO", 0.85, minimum=0.0
            ),
            time_budget_s=_env_float("GENSIE_SC_TIME_BUDGET_S", 60.0, minimum=0.001),
            time_budget_ratio=_env_float(
                "GENSIE_SC_TIME_BUDGET_RATIO", 0.85, minimum=0.0
            ),
            completion_token_safety_factor=_env_float(
                "GENSIE_SC_COMPLETION_TOKEN_SAFETY_FACTOR", 1.5, minimum=1.0
            ),
            time_safety_factor=_env_float(
                "GENSIE_SC_TIME_SAFETY_FACTOR", 1.15, minimum=1.0
            ),
            chars_per_token=_env_float("GENSIE_SC_CHARS_PER_TOKEN", 4.0, minimum=1.0),
            inter_trial_delay_s=_get_openai_request_delay_s(),
        )


class OfficialParticipant(Participant):
    """
    Standard entry point for the competition.
    Participants can configure up to 3 pipelines here.
    """

    def __init__(self):
        # Default pipeline using the reference BasicAgent
        self.pipelines = {
            "baseline": BasicAgent(),
            "enriched-schema": EnrichedSchemaAgent(),
            "simple-clean-schema": SimpleCleanSchemaAgent(),
            "inline-reasoning": InlineReasoningAgent(),
            "enriched-inline-reasoning": EnrichedInlineReasoningAgent(),
            "enriched-inline-reasoning-self-consistency": EnrichedInlineReasoningSelfConsistencyAgent(),
            # "pipeline2": MyCustomAgent(arg1, arg2...),
            # "pipeline3": AnotherAgent(...),
        }

    def get_info(self) -> ParticipantInfo:
        return ParticipantInfo(
            team_name="GenSIE Baseline Team",
            institution="Official",
            pipelines=[
                PipelineInfo(
                    name="baseline",
                    description="Standard OpenAI agent using structured outputs.",
                ),
                PipelineInfo(
                    name="enriched-schema",
                    description="Baseline + enriched schema prompt (field cards + Pydantic-like code).",
                ),
                PipelineInfo(
                    name="simple-clean-schema",
                    description="One-call baseline-plus with improved prompting and cleaned prompt schema; original schema is still used for structured output.",
                ),
                PipelineInfo(
                    name="inline-reasoning",
                    description="One-call pipeline with top-level field reasoning wrappers in the generation schema, unwrapped to final values. Optional one-shot example.",
                ),
                PipelineInfo(
                    name="enriched-inline-reasoning",
                    description="Inline reasoning wrappers plus compact Pydantic-like schema prompt with Reasoned[T]/Nullable[T].",
                ),
                PipelineInfo(
                    name="enriched-inline-reasoning-self-consistency",
                    description="Multi-sample enriched inline reasoning with modular schema-aware self-consistency over scalars, objects, and arrays.",
                ),
                # Add descriptions for your other pipelines here:
                # PipelineInfo(name="pipeline2", description="My advanced RAG agent"),
            ],
        )

    def get_agent(self, pipeline_name: str) -> GenSIEAgent:
        if pipeline_name not in self.pipelines:
            # Fallback to default if pipeline not found, or raise error
            return self.pipelines["baseline"]
        return self.pipelines[pipeline_name]
