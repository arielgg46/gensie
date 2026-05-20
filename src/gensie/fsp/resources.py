from __future__ import annotations

import json
from importlib import resources
from typing import Any, Mapping

from gensie.fsp.examples import (
    FieldExample,
    FieldReasoning,
    JudgeCandidateExample,
    JudgeExample,
    JudgeFieldExample,
    StructuredFspCase,
)


def load_fsp_case_resource(name: str) -> StructuredFspCase:
    resource = resources.files("gensie.fsp").joinpath("resources", "cases", name)
    with resource.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"FSP case resource must be a JSON object: {name}")
    return structured_fsp_case_from_mapping(data)


def structured_fsp_case_from_mapping(data: Mapping[str, Any]) -> StructuredFspCase:
    schema = data.get("schema")
    if not isinstance(schema, dict):
        raise ValueError("FSP case requires object schema")
    if schema.get("type") != "object" or not isinstance(schema.get("properties"), dict):
        raise ValueError("FSP case schema must be a root object with properties")

    return StructuredFspCase(
        id=_string(data, "id"),
        domain=_string(data, "domain"),
        language=_string(data, "language"),
        source_text=_string(data, "source_text"),
        instruction=_string(data, "instruction"),
        schema=dict(schema),
        field_examples=_field_examples(data.get("field_examples")),
        tags=tuple(_strings(data.get("tags"))),
        judge=_judge_example(data.get("judge")),
    )


def _field_examples(value: Any) -> dict[str, FieldExample]:
    if not isinstance(value, dict):
        raise ValueError("FSP case requires field_examples object")
    out: dict[str, FieldExample] = {}
    for name, raw_field in value.items():
        if not isinstance(name, str) or not isinstance(raw_field, dict):
            continue
        if "value" not in raw_field:
            raise ValueError(f"FSP field example missing value: {name}")
        out[name] = FieldExample(
            value=raw_field["value"],
            tags=tuple(_strings(raw_field.get("tags"))),
            reasoning=_field_reasoning(raw_field.get("reasoning")),
        )
    return out


def _field_reasoning(value: Any) -> FieldReasoning | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("FSP field reasoning must be an object")
    return FieldReasoning(
        field_asks=_string(value, "field_asks"),
        relevant_fragments=_string(value, "relevant_fragments"),
        final_value=_string(value, "final_value"),
        exact_text=value.get("exact_text") if isinstance(value.get("exact_text"), str) else None,
    )


def _judge_example(value: Any) -> JudgeExample | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("FSP judge example must be an object")
    total_trials = value.get("total_trials")
    if not isinstance(total_trials, int):
        raise ValueError("FSP judge example requires integer total_trials")
    stable_fields = value.get("stable_fields")
    fields = value.get("fields")
    return JudgeExample(
        total_trials=total_trials,
        stable_fields=dict(stable_fields) if isinstance(stable_fields, dict) else {},
        fields=_judge_fields(fields),
    )


def _judge_fields(value: Any) -> dict[str, JudgeFieldExample]:
    if not isinstance(value, dict):
        raise ValueError("FSP judge example requires fields object")
    out: dict[str, JudgeFieldExample] = {}
    for name, raw_field in value.items():
        if not isinstance(name, str) or not isinstance(raw_field, dict):
            continue
        out[name] = JudgeFieldExample(
            kind=_string(raw_field, "kind"),  # type: ignore[arg-type]
            candidates=tuple(_judge_candidates(raw_field.get("candidates"))),
            value=raw_field.get("value"),
            reasoned_output=dict(raw_field["reasoned_output"])
            if isinstance(raw_field.get("reasoned_output"), dict)
            else None,
            empty_trial_count=_non_negative_int(raw_field, "empty_trial_count", 0),
            null_trial_count=_non_negative_int(raw_field, "null_trial_count", 0),
            invalid_value_count=_non_negative_int(raw_field, "invalid_value_count", 0),
            field_description=raw_field.get("field_description")
            if isinstance(raw_field.get("field_description"), str)
            else None,
            tags=tuple(_strings(raw_field.get("tags"))),
        )
    return out


def _judge_candidates(value: Any) -> list[JudgeCandidateExample]:
    if not isinstance(value, list):
        raise ValueError("FSP judge field requires candidates list")
    candidates: list[JudgeCandidateExample] = []
    for raw_candidate in value:
        if not isinstance(raw_candidate, dict):
            continue
        if "value" not in raw_candidate:
            raise ValueError("FSP judge candidate missing value")
        candidates.append(
            JudgeCandidateExample(
                value=raw_candidate["value"],
                support=_non_negative_int(raw_candidate, "support", 0),
                evidence=_string(raw_candidate, "evidence"),
                include=raw_candidate.get("include")
                if isinstance(raw_candidate.get("include"), bool)
                else None,
                first_seen=_non_negative_int(raw_candidate, "first_seen", 0)
                if "first_seen" in raw_candidate
                else None,
            )
        )
    return candidates


def _string(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise ValueError(f"FSP case field must be string: {key}")
    return value


def _strings(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("FSP string list field must be an array")
    return [item for item in value if isinstance(item, str)]


def _non_negative_int(data: Mapping[str, Any], key: str, default: int) -> int:
    value = data.get(key, default)
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"FSP case field must be a non-negative integer: {key}")
    return value
