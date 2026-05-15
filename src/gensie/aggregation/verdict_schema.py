from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, Sequence

from gensie.aggregation.judge_scope import JudgeScope, merge_judge_output
from gensie.aggregation.schema_utils import (
    JsonDict,
    canonical_json,
    deref_item_schema,
    schema_type,
    unwrap_nullable_schema,
)
from gensie.pipeline.records import TrialRecord
from gensie.schemas.inspect import deref
from gensie.task import Task


VerdictKind = Literal["single", "array"]


@dataclass(frozen=True)
class VerdictCandidate:
    value: Any
    count: int
    trial_indices: tuple[int, ...]
    groups: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class VerdictField:
    name: str
    kind: VerdictKind
    value_schema: JsonDict
    field_schema: JsonDict
    candidates: tuple[VerdictCandidate, ...]


@dataclass(frozen=True)
class VerdictPlan:
    fields: tuple[VerdictField, ...]
    total_trials: int

    @property
    def field_names(self) -> tuple[str, ...]:
        return tuple(field.name for field in self.fields)


@dataclass(frozen=True)
class VerdictReconstruction:
    output: JsonDict
    validation_issues: tuple[JsonDict, ...] = ()


class VerdictValidationError(ValueError):
    def __init__(self, message: str, issues: Sequence[JsonDict] = ()):
        super().__init__(message)
        self.issues = tuple(copy.deepcopy(dict(issue)) for issue in issues)


def build_verdict_plan(
    task: Task, records: Sequence[TrialRecord], scope: JudgeScope
) -> VerdictPlan:
    valid_records = [record for record in records if record.result.is_valid]
    root_schema = task.target_schema
    resolved_schema = deref(root_schema, root_schema)
    properties = (
        resolved_schema.get("properties")
        if isinstance(resolved_schema.get("properties"), dict)
        else {}
    )

    fields: list[VerdictField] = []
    for field_name in scope.disputed_fields:
        field_schema = properties.get(field_name)
        if not isinstance(field_schema, dict):
            continue
        resolved_field_schema, _ = unwrap_nullable_schema(field_schema, root_schema)
        resolved_field_schema = deref(resolved_field_schema, root_schema)
        if schema_type(resolved_field_schema) == "array":
            value_schema = _compact_schema_for_generation(
                field_schema.get("items") if isinstance(field_schema.get("items"), dict) else {},
                root_schema,
            )
            if not value_schema:
                value_schema = _compact_schema_for_generation(
                    deref_item_schema(field_schema, root_schema), root_schema
                )
            fields.append(
                VerdictField(
                    name=field_name,
                    kind="array",
                    value_schema=value_schema or {},
                    field_schema=copy.deepcopy(field_schema),
                    candidates=_array_candidates(field_name, valid_records),
                )
            )
        else:
            fields.append(
                VerdictField(
                    name=field_name,
                    kind="single",
                    value_schema=_compact_schema_for_generation(field_schema, root_schema),
                    field_schema=copy.deepcopy(field_schema),
                    candidates=_scalar_candidates(field_name, valid_records),
                )
            )

    return VerdictPlan(fields=tuple(fields), total_trials=len(valid_records))


def build_verdict_response_format(
    task: Task, plan: VerdictPlan, *, name: str = "self_consistency_verdict_judge"
) -> dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "schema": build_verdict_generation_schema(task.target_schema, plan),
            "strict": True,
        },
    }


def build_verdict_generation_schema(root_schema: JsonDict, plan: VerdictPlan) -> JsonDict:
    properties: JsonDict = {}
    defs: JsonDict = {}
    original_defs = root_schema.get("$defs")
    if isinstance(original_defs, dict):
        defs.update(_compact_schema_for_generation({"$defs": original_defs}, root_schema).get("$defs", {}))

    signature_names: dict[str, tuple[str, str]] = {}
    used_names: set[str] = set(defs)

    for field in plan.fields:
        signature = field.kind + ":" + canonical_json(field.value_schema)
        if signature not in signature_names:
            base = _definition_base_name(field.value_schema)
            candidate_name = _unique_name(
                f"Verdict{base}{'Array' if field.kind == 'array' else 'Single'}Candidate",
                used_names,
            )
            verdict_name = _unique_name(
                f"Verdict{base}{'Array' if field.kind == 'array' else 'Single'}",
                used_names,
            )
            defs[candidate_name] = _candidate_schema(field.kind, field.value_schema)
            defs[verdict_name] = _verdict_schema(
                field.kind, field.value_schema, candidate_name
            )
            signature_names[signature] = (candidate_name, verdict_name)
        properties[field.name] = {"$ref": f"#/$defs/{signature_names[signature][1]}"}

    schema: JsonDict = {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties),
    }
    if defs:
        schema["$defs"] = defs
    return schema


def reconstruct_verdict_output(
    plan: VerdictPlan, scope: JudgeScope, raw_output: Any
) -> JsonDict:
    return reconstruct_verdict_output_with_report(
        plan,
        scope,
        raw_output,
        enforce_validation=True,
        report_validation=False,
    ).output


def reconstruct_verdict_output_with_report(
    plan: VerdictPlan,
    scope: JudgeScope,
    raw_output: Any,
    *,
    enforce_validation: bool = True,
    report_validation: bool = True,
    fallback_output: Mapping[str, Any] | None = None,
) -> VerdictReconstruction:
    if not isinstance(raw_output, dict):
        raise ValueError("verdict judge output must be a JSON object")

    fallback = dict(fallback_output or {})
    validation_issues: list[JsonDict] = []
    judge_values: JsonDict = {}
    for field in plan.fields:
        verdict = raw_output.get(field.name)
        if not isinstance(verdict, dict):
            _validation_issue(
                validation_issues,
                enforce_validation=enforce_validation,
                report_validation=report_validation,
                field=field.name,
                code="missing_verdict",
                message=f"missing verdict for field: {field.name}",
                actual=verdict,
            )
            _use_fallback_field(judge_values, fallback, field.name)
            continue
        candidates = verdict.get("candidates")
        if not isinstance(candidates, list):
            _validation_issue(
                validation_issues,
                enforce_validation=enforce_validation,
                report_validation=report_validation,
                field=field.name,
                code="candidates_not_list",
                message=f"verdict candidates must be a list: {field.name}",
                actual=candidates,
            )
            _use_fallback_field(judge_values, fallback, field.name)
            continue
        if len(candidates) != len(field.candidates):
            _validation_issue(
                validation_issues,
                enforce_validation=enforce_validation,
                report_validation=report_validation,
                field=field.name,
                code="candidate_count_mismatch",
                message=(
                    f"candidate count mismatch for {field.name}: "
                    f"expected {len(field.candidates)}, got {len(candidates)}"
                ),
                expected=len(field.candidates),
                actual=len(candidates),
            )

        expected_keys = [
            canonical_json(candidate.value) for candidate in field.candidates
        ]
        expected_by_key = {
            canonical_json(candidate.value): candidate for candidate in field.candidates
        }
        for index, actual in enumerate(candidates, start=1):
            if not isinstance(actual, dict):
                _validation_issue(
                    validation_issues,
                    enforce_validation=enforce_validation,
                    report_validation=report_validation,
                    field=field.name,
                    code="candidate_not_object",
                    message=f"candidate {index} for {field.name} must be an object",
                    position=index,
                    actual=actual,
                )
                continue
            if index > len(field.candidates):
                _validation_issue(
                    validation_issues,
                    enforce_validation=enforce_validation,
                    report_validation=report_validation,
                    field=field.name,
                    code="extra_candidate",
                    message=f"unexpected extra candidate for {field.name} at position {index}",
                    position=index,
                    actual=actual.get("candidate_value"),
                )
                continue
            expected = field.candidates[index - 1]
            if canonical_json(actual.get("candidate_value")) != canonical_json(
                expected.value
            ):
                _validation_issue(
                    validation_issues,
                    enforce_validation=enforce_validation,
                    report_validation=report_validation,
                    field=field.name,
                    code="candidate_value_mismatch",
                    message=(
                        f"candidate value mismatch for {field.name} "
                        f"at position {index}"
                    ),
                    position=index,
                    expected=expected.value,
                    actual=actual.get("candidate_value"),
                )

        if field.kind == "single":
            if "value" not in verdict:
                _validation_issue(
                    validation_issues,
                    enforce_validation=enforce_validation,
                    report_validation=report_validation,
                    field=field.name,
                    code="missing_value",
                    message=f"missing value for single verdict: {field.name}",
                )
                _use_fallback_field(judge_values, fallback, field.name)
                continue
            value = verdict.get("value")
            if canonical_json(value) not in expected_keys:
                _validation_issue(
                    validation_issues,
                    enforce_validation=enforce_validation,
                    report_validation=report_validation,
                    field=field.name,
                    code="value_not_expected_candidate",
                    message=f"value is not one of the candidates for {field.name}",
                    expected=[candidate.value for candidate in field.candidates],
                    actual=value,
                )
            judge_values[field.name] = copy.deepcopy(value)
        else:
            selected_keys: set[str] = set()
            selected_unexpected: list[Any] = []
            for index, actual in enumerate(candidates, start=1):
                if not isinstance(actual, dict):
                    continue
                if actual.get("include") is True:
                    if "candidate_value" not in actual:
                        _validation_issue(
                            validation_issues,
                            enforce_validation=enforce_validation,
                            report_validation=report_validation,
                            field=field.name,
                            code="missing_candidate_value",
                            message=(
                                f"missing candidate_value for {field.name} "
                                f"at position {index}"
                            ),
                            position=index,
                        )
                        if index <= len(field.candidates):
                            selected_keys.add(
                                canonical_json(field.candidates[index - 1].value)
                            )
                        continue
                    value = actual.get("candidate_value")
                    key = canonical_json(value)
                    if key in expected_by_key:
                        selected_keys.add(key)
                    else:
                        selected_unexpected.append(copy.deepcopy(value))
                elif actual.get("include") is not False:
                    _validation_issue(
                        validation_issues,
                        enforce_validation=enforce_validation,
                        report_validation=report_validation,
                        field=field.name,
                        code="include_not_boolean",
                        message=f"include must be boolean for {field.name}",
                        position=index,
                        actual=actual.get("include"),
                    )
            selected: list[Any] = [
                copy.deepcopy(candidate.value)
                for candidate in field.candidates
                if canonical_json(candidate.value) in selected_keys
            ]
            selected.extend(selected_unexpected)
            judge_values[field.name] = selected

    return VerdictReconstruction(
        output=merge_judge_output(scope, judge_values),
        validation_issues=tuple(validation_issues),
    )


def _validation_issue(
    issues: list[JsonDict],
    *,
    enforce_validation: bool,
    report_validation: bool,
    field: str,
    code: str,
    message: str,
    position: int | None = None,
    expected: Any = None,
    actual: Any = None,
) -> None:
    issue: JsonDict = {
        "field": field,
        "code": code,
        "message": message,
    }
    if position is not None:
        issue["position"] = position
    if expected is not None:
        issue["expected"] = copy.deepcopy(expected)
    if actual is not None:
        issue["actual"] = copy.deepcopy(actual)
    if report_validation:
        issues.append(issue)
    if enforce_validation:
        raise VerdictValidationError(message, issues)


def _use_fallback_field(
    judge_values: JsonDict, fallback_output: Mapping[str, Any], field_name: str
) -> None:
    if field_name in fallback_output:
        judge_values[field_name] = copy.deepcopy(fallback_output[field_name])


def _scalar_candidates(
    field_name: str, records: Sequence[TrialRecord]
) -> tuple[VerdictCandidate, ...]:
    groups: dict[str, dict[str, Any]] = {}
    for record in records:
        output = record.result.output or {}
        if field_name not in output:
            continue
        value = output[field_name]
        key = canonical_json(value)
        entry = groups.setdefault(
            key,
            {
                "value": copy.deepcopy(value),
                "count": 0,
                "trial_indices": [],
                "groups": {},
            },
        )
        _add_candidate_observation(entry, record)
    return _sorted_candidates(groups.values())


def _array_candidates(
    field_name: str, records: Sequence[TrialRecord]
) -> tuple[VerdictCandidate, ...]:
    groups: dict[str, dict[str, Any]] = {}
    for record in records:
        output = record.result.output or {}
        value = output.get(field_name)
        if not isinstance(value, list):
            continue
        seen_in_trial: set[str] = set()
        for item in value:
            key = canonical_json(item)
            if key in seen_in_trial:
                continue
            seen_in_trial.add(key)
            entry = groups.setdefault(
                key,
                {
                    "value": copy.deepcopy(item),
                    "count": 0,
                    "trial_indices": [],
                    "groups": {},
                },
            )
            _add_candidate_observation(entry, record)
    return _sorted_candidates(groups.values())


def _add_candidate_observation(entry: dict[str, Any], record: TrialRecord) -> None:
    entry["count"] += 1
    entry["trial_indices"].append(record.index + 1)
    groups = entry["groups"]
    groups[record.group_name] = groups.get(record.group_name, 0) + 1


def _sorted_candidates(entries: Sequence[dict[str, Any]]) -> tuple[VerdictCandidate, ...]:
    ordered = sorted(
        entries,
        key=lambda entry: (
            -int(entry["count"]),
            entry["trial_indices"][0] if entry["trial_indices"] else 10**9,
            canonical_json(entry["value"]),
        ),
    )
    return tuple(
        VerdictCandidate(
            value=entry["value"],
            count=int(entry["count"]),
            trial_indices=tuple(int(index) for index in entry["trial_indices"]),
            groups=dict(entry["groups"]),
        )
        for entry in ordered
    )


def _candidate_schema(kind: VerdictKind, value_schema: JsonDict) -> JsonDict:
    properties: JsonDict = {
        "candidate_value": copy.deepcopy(value_schema),
        "evidence": {"type": "string"},
    }
    required = ["candidate_value", "evidence"]
    if kind == "array":
        properties["include"] = {"type": "boolean"}
        required.append("include")
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": required,
    }


def _verdict_schema(
    kind: VerdictKind, value_schema: JsonDict, candidate_def_name: str
) -> JsonDict:
    properties: JsonDict = {
        "field": {"type": "string"},
        "candidates": {
            "type": "array",
            "items": {"$ref": f"#/$defs/{candidate_def_name}"},
        },
    }
    required = ["field", "candidates"]
    if kind == "single":
        properties["value"] = copy.deepcopy(value_schema)
        required.append("value")
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": required,
    }


def _compact_schema_for_generation(schema: JsonDict, root_schema: JsonDict) -> JsonDict:
    if not isinstance(schema, dict):
        return {}
    out: JsonDict = {}
    for key, value in schema.items():
        if key in {"description", "title", "default", "examples"}:
            continue
        if key == "$defs" and isinstance(value, dict):
            out[key] = {
                name: _compact_schema_for_generation(def_schema, root_schema)
                for name, def_schema in value.items()
                if isinstance(def_schema, dict)
            }
        elif key in {"properties"} and isinstance(value, dict):
            out[key] = {
                name: _compact_schema_for_generation(prop_schema, root_schema)
                for name, prop_schema in value.items()
                if isinstance(prop_schema, dict)
            }
        elif key in {"items"} and isinstance(value, dict):
            out[key] = _compact_schema_for_generation(value, root_schema)
        elif key in {"anyOf", "oneOf", "allOf"} and isinstance(value, list):
            out[key] = [
                _compact_schema_for_generation(item, root_schema)
                if isinstance(item, dict)
                else copy.deepcopy(item)
                for item in value
            ]
        else:
            out[key] = copy.deepcopy(value)
    return out


def _definition_base_name(schema: JsonDict) -> str:
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/$defs/"):
        return _pascal(ref.rsplit("/", 1)[-1])

    unwrapped, nullable = unwrap_nullable_schema(schema, {"$defs": {}})
    current_type = schema_type(unwrapped)
    if isinstance(unwrapped.get("enum"), list):
        base = "Enum"
    elif current_type == "string":
        base = "String"
    elif current_type == "integer":
        base = "Integer"
    elif current_type == "number":
        base = "Number"
    elif current_type == "boolean":
        base = "Boolean"
    elif current_type == "object":
        base = "Object"
    elif current_type == "array":
        base = "Array"
    elif current_type == "null":
        base = "Null"
    else:
        base = "Value"
    return f"Nullable{base}" if nullable else base


def _unique_name(base: str, used: set[str]) -> str:
    name = base
    index = 2
    while name in used:
        name = f"{base}{index}"
        index += 1
    used.add(name)
    return name


def _pascal(value: str) -> str:
    parts = [part for part in value.replace("-", "_").split("_") if part]
    return "".join(part[:1].upper() + part[1:] for part in parts) or "Value"


def json_value(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
