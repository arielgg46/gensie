from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Sequence

from gensie.aggregation.schema_utils import JsonDict, canonical_json, schema_type
from gensie.pipeline.records import TrialRecord
from gensie.schemas.inspect import deref


MISSING = object()


@dataclass(frozen=True)
class JudgeScope:
    stable_fields: JsonDict
    disputed_fields: tuple[str, ...]
    reduced_schema: JsonDict
    stable_sources: dict[str, JsonDict] = field(default_factory=dict)

    @property
    def has_disputes(self) -> bool:
        return bool(self.disputed_fields)


def build_judge_scope(records: Sequence[TrialRecord], schema: JsonDict) -> JudgeScope:
    valid_records = [record for record in records if record.result.is_valid]
    root_schema = schema
    resolved_schema = deref(schema, root_schema)
    properties = (
        resolved_schema.get("properties")
        if isinstance(resolved_schema.get("properties"), dict)
        else {}
    )
    required = set(resolved_schema.get("required") or [])

    stable_fields: JsonDict = {}
    stable_sources: dict[str, JsonDict] = {}
    disputed_fields: list[str] = []

    for field_name, field_schema in properties.items():
        if not isinstance(field_schema, dict):
            continue
        observations = [
            _field_value(record, field_name) for record in valid_records
        ]
        if not observations:
            disputed_fields.append(field_name)
            continue

        if all(value is MISSING for value in observations):
            if field_name in required:
                disputed_fields.append(field_name)
            continue

        if any(value is MISSING for value in observations):
            disputed_fields.append(field_name)
            continue

        keys = [_field_stability_key(value, field_schema, root_schema) for value in observations]
        if len(set(keys)) == 1:
            stable_fields[field_name] = copy.deepcopy(observations[0])
            stable_sources[field_name] = {
                "trial_indices": [record.index for record in valid_records],
                "groups": sorted({record.group_name for record in valid_records}),
            }
        else:
            disputed_fields.append(field_name)

    return JudgeScope(
        stable_fields=stable_fields,
        disputed_fields=tuple(disputed_fields),
        reduced_schema=build_reduced_schema(schema, disputed_fields),
        stable_sources=stable_sources,
    )


def build_reduced_schema(schema: JsonDict, field_names: Sequence[str]) -> JsonDict:
    field_set = set(field_names)
    reduced = copy.deepcopy(schema)
    properties = reduced.get("properties")
    if isinstance(properties, dict):
        reduced["properties"] = {
            name: value for name, value in properties.items() if name in field_set
        }
    else:
        reduced["properties"] = {}

    required = reduced.get("required")
    if isinstance(required, list):
        reduced["required"] = [name for name in required if name in field_set]
    else:
        reduced["required"] = list(field_names)
    return reduced


def merge_judge_output(scope: JudgeScope, judge_output: JsonDict) -> JsonDict:
    merged: JsonDict = {}
    reduced_properties = (
        scope.reduced_schema.get("properties")
        if isinstance(scope.reduced_schema.get("properties"), dict)
        else {}
    )
    original_fields = list(scope.stable_fields.keys()) + [
        name for name in reduced_properties if name not in scope.stable_fields
    ]
    for field_name in original_fields:
        if field_name in judge_output:
            merged[field_name] = copy.deepcopy(judge_output[field_name])
        elif field_name in scope.stable_fields:
            merged[field_name] = copy.deepcopy(scope.stable_fields[field_name])

    for field_name, value in judge_output.items():
        if field_name not in merged:
            merged[field_name] = copy.deepcopy(value)
    return merged


def _field_value(record: TrialRecord, field_name: str) -> Any:
    output = record.result.output
    if not isinstance(output, dict) or field_name not in output:
        return MISSING
    return output[field_name]


def _field_stability_key(value: Any, field_schema: JsonDict, root_schema: JsonDict) -> str:
    field_schema = deref(field_schema, root_schema)
    if schema_type(field_schema) == "array" and isinstance(value, list):
        return canonical_json(sorted(canonical_json(item) for item in value))
    return canonical_json(value)
