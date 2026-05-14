from __future__ import annotations

import json
from typing import Any, Sequence

from gensie.aggregation.judge_fsp import JudgeFspProvider, NoJudgeFspProvider
from gensie.aggregation.judge_scope import JudgeScope
from gensie.aggregation.schema_utils import JsonDict, canonical_json, schema_type
from gensie.pipeline.records import TrialRecord
from gensie.schemas.inspect import deref
from gensie.schemas.pydantic_render import render_reasoned_pydantic_schema
from gensie.task import Task


SELF_CONSISTENCY_JUDGE_SYSTEM_PROMPT = (
    "Eres un juez experto de extracción de información en español.\n"
    "Recibes varios intentos de extracción, el schema reducido y el texto fuente.\n"
    "Devuelve solo los campos disputados indicados por el schema.\n"
    "Usa solo evidencia del texto fuente; no uses conocimiento externo.\n"
    "Cada campo de primer nivel debe incluir reasoning y value.\n"
    "En reasoning decide la respuesta correcta comparando los intentos, sus soportes y la evidencia textual."
)


def build_self_consistency_judge_prompt(
    task: Task,
    records: Sequence[TrialRecord],
    scope: JudgeScope,
    *,
    fsp_provider: JudgeFspProvider | None = None,
    include_scalar_reasonings: bool = False,
    include_array_reasonings: bool = False,
    include_stable_fields: bool = False,
    include_support_counts: bool = True,
) -> str:
    schema_code = render_reasoned_pydantic_schema(scope.reduced_schema)
    fsp = (fsp_provider or NoJudgeFspProvider()).build(
        scope,
        include_stable_fields=include_stable_fields,
        include_support_counts=include_support_counts,
    )
    votes = build_judge_vote_summary(
        task,
        records,
        scope,
        include_scalar_reasonings=include_scalar_reasonings,
        include_array_reasonings=include_array_reasonings,
    )
    votes_text = render_judge_vote_summary(
        votes,
        include_support_counts=include_support_counts,
    )
    stable_section = _render_stable_fields_section(scope) if include_stable_fields else ""
    disputed_text = ", ".join(f"`{field}`" for field in scope.disputed_fields)
    count_rule = (
        "Los conteos indican estabilidad entre trials, pero no reemplazan al grounding textual.\n"
        if include_support_counts
        else ""
    )
    reasoning_rule = (
        "En cada reasoning explica brevemente qué candidatos consideraste, qué soporte tuvieron y por qué el value final es correcto.\n"
        if include_support_counts
        else "En cada reasoning explica brevemente qué candidatos consideraste y por qué el value final es correcto.\n"
    )
    stable_instruction = (
        "No devuelvas campos ya consensuados; esos se reconstruyen fuera de esta llamada.\n"
        if include_stable_fields
        else ""
    )

    return (
        "TAREA DEL JUEZ:\n"
        "Decide la extracción final solo para los campos disputados usando el TEXTO FUENTE y los intentos previos como evidencia auxiliar.\n"
        f"{count_rule}"
        "Si la mayoría contradice el texto fuente o inventa información, corrige hacia el texto o usa null cuando el schema lo permita.\n"
        "Para arrays, decide item por item a partir de los elementos candidatos, no por lista completa.\n"
        f"{reasoning_rule}"
        "Reasoned[T] significa que el campo se genera como {\"reasoning\": str, \"value\": T}.\n"
        "Nullable[T] significa que value puede ser null, pero el campo no se puede omitir.\n\n"
        f"{fsp}\n"
        "INSTRUCCIÓN ORIGINAL:\n"
        f"{task.instruction}\n\n"
        "INSTRUCCIÓN DEL JUEZ:\n"
        f"Razona y da un veredicto solo sobre estos campos: {disputed_text}.\n"
        f"{stable_instruction}\n"
        "SCHEMA PYDANTIC DE SALIDA REDUCIDO:\n"
        f"{schema_code}\n"
        "TEXTO FUENTE:\n"
        f"{task.input_text}\n\n"
        f"{stable_section}"
        "VALORES CANDIDATOS POR CAMPO:\n"
        f"{votes_text}"
    )


def build_judge_vote_summary(
    task: Task,
    records: Sequence[TrialRecord],
    scope: JudgeScope,
    *,
    include_scalar_reasonings: bool = False,
    include_array_reasonings: bool = False,
) -> JsonDict:
    root_schema = task.target_schema
    schema = deref(root_schema, root_schema)
    properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    valid_records = [record for record in records if record.result.is_valid]

    fields: JsonDict = {}
    for field_name in scope.disputed_fields:
        field_schema = properties.get(field_name)
        if not isinstance(field_schema, dict):
            continue
        value_schema = deref(field_schema, root_schema)
        if schema_type(value_schema) == "array":
            fields[field_name] = _array_field_votes(
                field_name,
                valid_records,
                include_reasonings=include_array_reasonings,
            )
        else:
            fields[field_name] = _scalar_field_votes(
                field_name,
                valid_records,
                include_reasonings=include_scalar_reasonings,
            )

    return {
        "trial_count": len(valid_records),
        "scalar_reasonings_included": include_scalar_reasonings,
        "array_reasonings_included": include_array_reasonings,
        "fields": fields,
    }


def render_judge_vote_summary(
    summary: JsonDict,
    *,
    include_support_counts: bool = True,
) -> str:
    total = int(summary.get("trial_count") or 0)
    fields = summary.get("fields") if isinstance(summary.get("fields"), dict) else {}
    lines = [f"Trials válidos: {total}"] if include_support_counts else []

    for field_name, field in fields.items():
        if not isinstance(field, dict):
            continue
        if field.get("kind") == "array_items":
            lines.extend(
                _render_array_field_votes(
                    field_name,
                    field,
                    total,
                    include_support_counts=include_support_counts,
                )
            )
        else:
            lines.extend(
                _render_scalar_field_votes(
                    field_name,
                    field,
                    total,
                    include_support_counts=include_support_counts,
                )
            )
    return "\n".join(lines).rstrip()


def _scalar_field_votes(
    field_name: str,
    records: Sequence[TrialRecord],
    *,
    include_reasonings: bool,
) -> JsonDict:
    groups: dict[str, JsonDict] = {}
    missing_count = 0
    for record in records:
        output = record.result.output or {}
        if field_name not in output:
            missing_count += 1
            continue
        value = output[field_name]
        key = canonical_json(value)
        entry = groups.setdefault(
            key,
            {
                "value": value,
                "count": 0,
                "trial_indices": [],
                "groups": {},
            },
        )
        entry["count"] += 1
        entry["trial_indices"].append(record.index + 1)
        entry["groups"][record.group_name] = entry["groups"].get(record.group_name, 0) + 1
        if include_reasonings:
            entry.setdefault("reasonings", []).append(
                {
                    "trial_index": record.index + 1,
                    "reasoning": _field_reasoning(record, field_name),
                }
            )

    return {
        "kind": "value",
        "missing_count": missing_count,
        "distinct_values": _sorted_group_entries(groups.values()),
    }


def _array_field_votes(
    field_name: str,
    records: Sequence[TrialRecord],
    *,
    include_reasonings: bool,
) -> JsonDict:
    item_groups: dict[str, JsonDict] = {}
    null_count = 0
    empty_list_count = 0
    non_empty_list_count = 0
    invalid_value_count = 0
    missing_count = 0
    trial_reasonings: list[JsonDict] = []

    for record in records:
        output = record.result.output or {}
        trial_number = record.index + 1
        if field_name not in output:
            missing_count += 1
            continue

        value = output[field_name]
        if value is None:
            null_count += 1
        elif isinstance(value, list):
            if value:
                non_empty_list_count += 1
            else:
                empty_list_count += 1
            seen_in_trial: set[str] = set()
            for item in value:
                key = canonical_json(item)
                if key in seen_in_trial:
                    continue
                seen_in_trial.add(key)
                entry = item_groups.setdefault(
                    key,
                    {
                        "value": item,
                        "count": 0,
                        "trial_indices": [],
                        "groups": {},
                    },
                )
                entry["count"] += 1
                entry["trial_indices"].append(trial_number)
                entry["groups"][record.group_name] = (
                    entry["groups"].get(record.group_name, 0) + 1
                )
        else:
            invalid_value_count += 1

        if include_reasonings:
            trial_reasonings.append(
                {
                    "trial_index": trial_number,
                    "value": value,
                    "reasoning": _field_reasoning(record, field_name),
                }
            )

    out: JsonDict = {
        "kind": "array_items",
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


def _render_scalar_field_votes(
    field_name: str,
    field: JsonDict,
    total: int,
    *,
    include_support_counts: bool,
) -> list[str]:
    lines = ["", f"CAMPO `{field_name}`", "Valores candidatos:"]
    values = field.get("distinct_values")
    if not isinstance(values, list) or not values:
        lines.append("- Ningún valor candidato.")
        return lines
    for entry in values:
        if not isinstance(entry, dict):
            continue
        lines.append(_format_vote_line(entry, total, include_support_counts))
        reasonings = entry.get("reasonings")
        if isinstance(reasonings, list) and reasonings:
            lines.append("  Razones de trials con este valor:")
            for reasoning_entry in reasonings:
                reasoning = reasoning_entry.get("reasoning")
                if isinstance(reasoning, str) and reasoning.strip():
                    lines.append(f"  - {reasoning.strip()}")
    return lines


def _render_array_field_votes(
    field_name: str,
    field: JsonDict,
    total: int,
    *,
    include_support_counts: bool,
) -> list[str]:
    lines = ["", f"CAMPO `{field_name}` (lista)", "Elementos candidatos:"]
    items = field.get("distinct_items")
    if isinstance(items, list) and items:
        for entry in items:
            if isinstance(entry, dict):
                lines.append(_format_vote_line(entry, total, include_support_counts))
    else:
        lines.append("- Ningún elemento candidato.")

    empty_count = int(field.get("empty_list_count") or 0)
    null_count = int(field.get("null_count") or 0)
    invalid_count = int(field.get("invalid_value_count") or 0)
    if empty_count:
        lines.append(
            f"- Lista vacía en {empty_count}/{total} trials."
            if include_support_counts
            else "- Lista vacía."
        )
    if null_count:
        lines.append(
            f"- Valor null en {null_count}/{total} trials."
            if include_support_counts
            else "- Valor null."
        )
    if invalid_count:
        lines.append(
            f"- Valor no-lista inválido en {invalid_count}/{total} trials."
            if include_support_counts
            else "- Valor no-lista inválido."
        )

    trial_reasonings = field.get("trial_reasonings")
    if isinstance(trial_reasonings, list) and trial_reasonings:
        lines.append("Razones de trials para este campo:")
        for reasoning_entry in trial_reasonings:
            reasoning = reasoning_entry.get("reasoning")
            if isinstance(reasoning, str) and reasoning.strip():
                lines.append(f"- {reasoning.strip()}")
    return lines


def _format_vote_line(
    entry: JsonDict, total: int, include_support_counts: bool
) -> str:
    count = int(entry.get("count") or 0)
    value = json.dumps(entry.get("value"), ensure_ascii=False, sort_keys=True)
    if not include_support_counts:
        return f"- {value}"
    return f"- {count}/{total}: {value}"


def _sorted_group_entries(entries: Sequence[JsonDict]) -> list[JsonDict]:
    return sorted(
        entries,
        key=lambda entry: (
            -int(entry["count"]),
            entry["trial_indices"][0] if entry["trial_indices"] else 10**9,
            canonical_json(entry["value"]),
        ),
    )


def _field_reasoning(record: TrialRecord, field_name: str) -> str:
    reasoning = (record.result.reasoning or {}).get(field_name)
    return reasoning if isinstance(reasoning, str) else ""


def _render_stable_fields_section(scope: JudgeScope) -> str:
    if not scope.stable_fields:
        return "CAMPOS YA CONSENSUADOS:\n- Ningún campo consensuado.\n\n"
    lines = []
    for field_name, value in scope.stable_fields.items():
        value_json = json.dumps(value, ensure_ascii=False, sort_keys=True)
        lines.append(f"- {field_name}: {value_json}")
    return "CAMPOS YA CONSENSUADOS:\n" + "\n".join(lines) + "\n\n"
