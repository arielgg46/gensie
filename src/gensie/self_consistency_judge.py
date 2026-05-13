from __future__ import annotations

import json
from typing import Any, Dict, List, Sequence, Tuple

from gensie.enriched_inline_reasoning import render_reasoned_pydantic_schema
from gensie.schema_enrichment import _deref
from gensie.task import Task


JsonDict = Dict[str, Any]


SELF_CONSISTENCY_JUDGE_SYSTEM_PROMPT = (
    "Eres un juez experto de extracción de información en español.\n"
    "Recibes varios intentos de extracción, el schema y el texto fuente.\n"
    "Devuelve solo el objeto JSON requerido por el schema.\n"
    "Usa solo evidencia del texto fuente; no uses conocimiento externo.\n"
    "Cada campo de primer nivel debe incluir reasoning y value.\n"
    "En reasoning decide la respuesta correcta comparando los intentos, sus soportes y la evidencia textual."
)


def build_self_consistency_judge_prompt(
    task: Task,
    trial_responses: Sequence[JsonDict],
    *,
    include_scalar_reasonings: bool = False,
    include_array_reasonings: bool = False,
) -> str:
    """Build the final judge prompt from unwrapped candidates and trial reasonings."""
    schema_code = render_reasoned_pydantic_schema(task.target_schema)
    votes = build_judge_vote_summary(
        task,
        trial_responses,
        include_scalar_reasonings=include_scalar_reasonings,
        include_array_reasonings=include_array_reasonings,
    )
    votes_text = render_judge_vote_summary(votes)

    return (
        "TAREA DEL JUEZ:\n"
        "Decide la extracción final usando el TEXTO FUENTE y los intentos previos como evidencia auxiliar.\n"
        "Los conteos indican estabilidad entre trials, pero no reemplazan al grounding textual.\n"
        "Si la mayoría contradice el texto fuente o inventa información, corrige hacia el texto o usa null cuando el schema lo permita.\n"
        "Para arrays, decide item por item a partir de los elementos candidatos, no por lista completa.\n"
        "En cada reasoning explica brevemente qué candidatos consideraste, qué soporte tuvieron y por qué el value final es correcto.\n"
        "Reasoned[T] significa que el campo se genera como {\"reasoning\": str, \"value\": T}.\n"
        "Nullable[T] significa que value puede ser null, pero el campo no se puede omitir.\n\n"
        "INSTRUCCIÓN:\n"
        f"{task.instruction}\n\n"
        "SCHEMA PYDANTIC DE SALIDA:\n"
        f"{schema_code}\n"
        "TEXTO FUENTE:\n"
        f"{task.input_text}\n\n"
        "VALORES CANDIDATOS POR CAMPO:\n"
        f"{votes_text}"
    )


def build_judge_vote_summary(
    task: Task,
    trial_responses: Sequence[JsonDict],
    *,
    include_scalar_reasonings: bool = False,
    include_array_reasonings: bool = False,
) -> JsonDict:
    """Summarize trial candidates per field for an SLM judge."""
    root_schema = task.target_schema
    schema = _deref(root_schema, root_schema)
    properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    trials = _valid_trials(trial_responses)

    fields: JsonDict = {}
    for field_name, field_schema in properties.items():
        if not isinstance(field_schema, dict):
            continue
        value_schema, nullable = _unwrap_nullable_schema(field_schema, root_schema)
        value_schema = _deref(value_schema, root_schema)
        if _schema_type(value_schema) == "array":
            fields[field_name] = _array_field_votes(
                field_name,
                trials,
                nullable=nullable,
                include_reasonings=include_array_reasonings,
            )
        else:
            fields[field_name] = _scalar_field_votes(
                field_name,
                trials,
                nullable=nullable,
                include_reasonings=include_scalar_reasonings,
            )

    return {
        "trial_count": len(trials),
        "scalar_reasonings_included": include_scalar_reasonings,
        "array_reasonings_included": include_array_reasonings,
        "fields": fields,
    }


def render_judge_vote_summary(summary: JsonDict) -> str:
    """Render votes as compact text for the judge prompt."""
    total = int(summary.get("trial_count") or 0)
    fields = summary.get("fields") if isinstance(summary.get("fields"), dict) else {}
    lines = [f"Trials válidos: {total}"]

    for field_name, field in fields.items():
        if not isinstance(field, dict):
            continue
        kind = field.get("kind")
        if kind == "array_items":
            lines.extend(_render_array_field_votes(field_name, field, total))
        else:
            lines.extend(_render_scalar_field_votes(field_name, field, total))

    return "\n".join(lines).rstrip()


def _valid_trials(trial_responses: Sequence[JsonDict]) -> List[JsonDict]:
    out: List[JsonDict] = []
    for fallback_index, trial_response in enumerate(trial_responses, start=1):
        final_candidate = trial_response.get("final_candidate")
        inline_output = trial_response.get("inline_reasoning_output")
        if not isinstance(final_candidate, dict) or not isinstance(inline_output, dict):
            continue
        raw_index = trial_response.get("trial_index")
        trial_number = raw_index + 1 if isinstance(raw_index, int) else fallback_index
        out.append(
            {
                "trial_number": trial_number,
                "final_candidate": final_candidate,
                "inline_reasoning_output": inline_output,
            }
        )
    return out


def _scalar_field_votes(
    field_name: str,
    trials: Sequence[JsonDict],
    *,
    nullable: bool,
    include_reasonings: bool,
) -> JsonDict:
    groups: Dict[str, JsonDict] = {}
    missing_count = 0
    for trial in trials:
        final_candidate = trial["final_candidate"]
        if field_name not in final_candidate:
            missing_count += 1
            continue
        value = final_candidate[field_name]
        key = _canonical_json(value)
        entry = groups.setdefault(
            key,
            {
                "value": value,
                "count": 0,
                "trial_indices": [],
            },
        )
        entry["count"] += 1
        entry["trial_indices"].append(trial["trial_number"])
        if include_reasonings:
            entry.setdefault("reasonings", []).append(
                {
                    "trial_index": trial["trial_number"],
                    "reasoning": _field_reasoning(
                        trial["inline_reasoning_output"], field_name
                    ),
                }
            )

    return {
        "kind": "value",
        "nullable": nullable,
        "missing_count": missing_count,
        "distinct_values": _sorted_group_entries(groups.values()),
    }


def _array_field_votes(
    field_name: str,
    trials: Sequence[JsonDict],
    *,
    nullable: bool,
    include_reasonings: bool,
) -> JsonDict:
    item_groups: Dict[str, JsonDict] = {}
    null_count = 0
    empty_list_count = 0
    non_empty_list_count = 0
    invalid_value_count = 0
    missing_count = 0
    trial_reasonings: List[JsonDict] = []

    for trial in trials:
        final_candidate = trial["final_candidate"]
        trial_number = trial["trial_number"]
        if field_name not in final_candidate:
            missing_count += 1
            continue

        value = final_candidate[field_name]
        if value is None:
            null_count += 1
        elif isinstance(value, list):
            if value:
                non_empty_list_count += 1
            else:
                empty_list_count += 1
            seen_in_trial: set[str] = set()
            for item in value:
                key = _canonical_json(item)
                if key in seen_in_trial:
                    continue
                seen_in_trial.add(key)
                entry = item_groups.setdefault(
                    key,
                    {
                        "value": item,
                        "count": 0,
                        "trial_indices": [],
                    },
                )
                entry["count"] += 1
                entry["trial_indices"].append(trial_number)
        else:
            invalid_value_count += 1

        if include_reasonings:
            trial_reasonings.append(
                {
                    "trial_index": trial_number,
                    "value": value,
                    "reasoning": _field_reasoning(
                        trial["inline_reasoning_output"], field_name
                    ),
                }
            )

    out: JsonDict = {
        "kind": "array_items",
        "nullable": nullable,
        "missing_count": missing_count,
        "null_count": null_count,
        "empty_list_count": empty_list_count,
        "non_empty_list_count": non_empty_list_count,
        "invalid_value_count": invalid_value_count,
        "distinct_items": _sorted_group_entries(item_groups.values()),
    }
    if include_reasonings:
        out["trial_reasonings"] = sorted(
            trial_reasonings, key=lambda entry: entry["trial_index"]
        )
    return out


def _render_scalar_field_votes(field_name: str, field: JsonDict, total: int) -> List[str]:
    lines = ["", f"CAMPO `{field_name}`", "Valores candidatos:"]
    values = field.get("distinct_values")
    if not isinstance(values, list) or not values:
        lines.append("- Ningún valor candidato.")
        return lines

    for entry in values:
        if not isinstance(entry, dict):
            continue
        lines.append(_format_vote_line(entry, total))
        reasonings = entry.get("reasonings")
        if isinstance(reasonings, list) and reasonings:
            lines.append("  Razones de trials con este valor:")
            for reasoning_entry in reasonings:
                if not isinstance(reasoning_entry, dict):
                    continue
                reasoning = reasoning_entry.get("reasoning")
                if not isinstance(reasoning, str) or not reasoning.strip():
                    continue
                lines.append(f"  - {reasoning.strip()}")
    return lines


def _render_array_field_votes(field_name: str, field: JsonDict, total: int) -> List[str]:
    lines = ["", f"CAMPO `{field_name}` (lista)", "Elementos candidatos:"]
    items = field.get("distinct_items")
    if isinstance(items, list) and items:
        for entry in items:
            if not isinstance(entry, dict):
                continue
            lines.append(_format_vote_line(entry, total))
    else:
        lines.append("- Ningún elemento candidato.")

    empty_count = int(field.get("empty_list_count") or 0)
    null_count = int(field.get("null_count") or 0)
    invalid_count = int(field.get("invalid_value_count") or 0)
    if empty_count:
        lines.append(f"- Lista vacía en {empty_count}/{total} trials.")
    if null_count:
        lines.append(f"- Valor null en {null_count}/{total} trials.")
    if invalid_count:
        lines.append(f"- Valor no-lista inválido en {invalid_count}/{total} trials.")

    trial_reasonings = field.get("trial_reasonings")
    if isinstance(trial_reasonings, list) and trial_reasonings:
        lines.append("Razones de trials para este campo:")
        for reasoning_entry in trial_reasonings:
            if not isinstance(reasoning_entry, dict):
                continue
            reasoning = reasoning_entry.get("reasoning")
            if not isinstance(reasoning, str) or not reasoning.strip():
                continue
            lines.append(f"- {reasoning.strip()}")
    return lines


def _format_vote_line(entry: JsonDict, total: int) -> str:
    count = int(entry.get("count") or 0)
    value = json.dumps(entry.get("value"), ensure_ascii=False, sort_keys=True)
    return f"- {count}/{total}: {value}"


def _sorted_group_entries(entries: Sequence[JsonDict]) -> List[JsonDict]:
    return sorted(
        entries,
        key=lambda entry: (
            -int(entry["count"]),
            entry["trial_indices"][0] if entry["trial_indices"] else 10**9,
            _canonical_json(entry["value"]),
        ),
    )


def _field_reasoning(inline_output: JsonDict, field_name: str) -> str:
    wrapped = inline_output.get(field_name)
    if not isinstance(wrapped, dict):
        return ""
    reasoning = wrapped.get("reasoning")
    return reasoning if isinstance(reasoning, str) else ""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _unwrap_nullable_schema(schema: JsonDict, root_schema: JsonDict) -> Tuple[JsonDict, bool]:
    schema = _deref(schema, root_schema)

    any_of = schema.get("anyOf")
    if isinstance(any_of, list):
        non_null_alts: List[JsonDict] = []
        has_null = False
        for alt in any_of:
            if not isinstance(alt, dict):
                return schema, False
            alt = _deref(alt, root_schema)
            if alt.get("type") == "null":
                has_null = True
            else:
                non_null_alts.append(alt)
        if has_null and len(non_null_alts) == 1:
            inner = dict(non_null_alts[0])
            for key in ("description", "title", "default", "examples"):
                if key in schema and key not in inner:
                    inner[key] = schema[key]
            return _deref(inner, root_schema), True

    schema_type = schema.get("type")
    if isinstance(schema_type, list) and "null" in schema_type:
        non_null_types = [t for t in schema_type if t != "null"]
        if len(non_null_types) == 1:
            inner = dict(schema)
            inner["type"] = non_null_types[0]
            return inner, True

    return schema, False


def _schema_type(schema: JsonDict) -> str:
    schema_type = schema.get("type")
    if isinstance(schema_type, str):
        return schema_type
    if isinstance(schema_type, list):
        non_null = [item for item in schema_type if item != "null"]
        if len(non_null) == 1 and isinstance(non_null[0], str):
            return non_null[0]
    if "enum" in schema:
        return "enum"
    return ""
