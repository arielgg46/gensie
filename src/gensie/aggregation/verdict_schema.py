from __future__ import annotations

import copy
import json
import unicodedata
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
from gensie.config import env_bool
from gensie.pipeline.records import TrialRecord
from gensie.runtime.unicode import normalize_model_output_strings
from gensie.schemas.inspect import deref
from gensie.task import Task


VerdictKind = Literal["single", "array"]
VerdictCandidateLayout = Literal["array", "slots"]
VERDICT_EVIDENCE_MAX_LENGTH = 240
VERDICT_EVIDENCE_MAX_LENGTH_SCHEMA_ENV = (
    "GENSIE_SC_VERDICT_JUDGE_USE_EVIDENCE_MAX_LENGTH"
)


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
    task: Task,
    plan: VerdictPlan,
    *,
    name: str = "self_consistency_verdict_judge",
    include_evidence_max_length: bool | None = None,
    candidate_layout: VerdictCandidateLayout = "array",
) -> dict[str, Any]:
    if include_evidence_max_length is None:
        include_evidence_max_length = env_bool(
            VERDICT_EVIDENCE_MAX_LENGTH_SCHEMA_ENV, False
        )
    candidate_layout = normalize_candidate_layout(candidate_layout)
    return {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "schema": build_verdict_generation_schema(
                task.target_schema,
                plan,
                include_evidence_max_length=include_evidence_max_length,
                candidate_layout=candidate_layout,
            ),
            "strict": True,
        },
    }


def build_verdict_generation_schema(
    root_schema: JsonDict,
    plan: VerdictPlan,
    *,
    include_evidence_max_length: bool = False,
    candidate_layout: VerdictCandidateLayout = "array",
) -> JsonDict:
    candidate_layout = normalize_candidate_layout(candidate_layout)
    properties: JsonDict = {}
    defs: JsonDict = {}
    original_defs = root_schema.get("$defs")
    if isinstance(original_defs, dict):
        defs.update(_compact_schema_for_generation({"$defs": original_defs}, root_schema).get("$defs", {}))

    candidate_names: dict[str, str] = {}
    verdict_names: dict[str, str] = {}
    used_names: set[str] = set(defs)

    for field in plan.fields:
        candidate_signature = field.kind + ":" + canonical_json(field.value_schema)
        if candidate_signature not in candidate_names:
            base = _definition_base_name(field.value_schema)
            candidate_name = _candidate_definition_name(
                field.kind,
                base,
                used_names,
                candidate_layout=candidate_layout,
            )
            defs[candidate_name] = _candidate_schema(
                field.kind,
                field.value_schema,
                include_evidence_max_length=include_evidence_max_length,
            )
            candidate_names[candidate_signature] = candidate_name
        candidate_name = candidate_names[candidate_signature]

        verdict_signature = ":".join(
            (
                candidate_signature,
                candidate_layout,
                str(len(field.candidates)) if candidate_layout == "slots" else "*",
            )
        )
        if verdict_signature not in verdict_names:
            base = _definition_base_name(field.value_schema)
            verdict_name = _verdict_definition_name(
                field.kind,
                base,
                used_names,
                candidate_layout=candidate_layout,
            )
            defs[verdict_name] = _verdict_schema(
                field.kind,
                field.value_schema,
                candidate_name,
                candidate_count=len(field.candidates),
                candidate_layout=candidate_layout,
            )
            verdict_names[verdict_signature] = verdict_name
        properties[field.name] = {"$ref": f"#/$defs/{verdict_names[verdict_signature]}"}

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
    plan: VerdictPlan,
    scope: JudgeScope,
    raw_output: Any,
    *,
    candidate_layout: VerdictCandidateLayout = "array",
) -> JsonDict:
    return reconstruct_verdict_output_with_report(
        plan,
        scope,
        raw_output,
        enforce_validation=True,
        report_validation=False,
        candidate_layout=candidate_layout,
    ).output


def reconstruct_verdict_output_with_report(
    plan: VerdictPlan,
    scope: JudgeScope,
    raw_output: Any,
    *,
    enforce_validation: bool = True,
    report_validation: bool = True,
    fallback_output: Mapping[str, Any] | None = None,
    candidate_layout: VerdictCandidateLayout = "array",
) -> VerdictReconstruction:
    if not isinstance(raw_output, dict):
        raise ValueError("verdict judge output must be a JSON object")
    candidate_layout = normalize_candidate_layout(candidate_layout)

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
        candidate_entries = _candidate_entries(
            field,
            verdict.get("candidates"),
            candidate_layout=candidate_layout,
            issues=validation_issues,
            enforce_validation=enforce_validation,
            report_validation=report_validation,
        )
        if candidate_entries is None:
            _use_fallback_field(judge_values, fallback, field.name)
            continue

        expected_keys = [
            canonical_json(candidate.value) for candidate in field.candidates
        ]
        expected_by_key = {
            canonical_json(candidate.value): candidate for candidate in field.candidates
        }
        for index, actual in candidate_entries:
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
            value_key = canonical_json(value)
            if value_key not in expected_keys:
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
                if candidate_layout == "slots":
                    slot_value = _slot_expected_value_for_returned_value(
                        field,
                        candidate_entries,
                        value,
                    )
                    if slot_value is not _NO_SLOT_VALUE:
                        value = slot_value
            else:
                value = expected_by_key[value_key].value
            judge_values[field.name] = copy.deepcopy(value)
        else:
            selected_keys: set[str] = set()
            selected_unexpected: list[Any] = []
            for index, actual in candidate_entries:
                if not isinstance(actual, dict):
                    continue
                if actual.get("include") is True:
                    if candidate_layout == "slots" and index <= len(field.candidates):
                        selected_keys.add(
                            canonical_json(field.candidates[index - 1].value)
                        )
                        continue
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
        output=normalize_model_output_strings(merge_judge_output(scope, judge_values)),
        validation_issues=tuple(validation_issues),
    )


_NO_SLOT_VALUE = object()


def _slot_expected_value_for_returned_value(
    field: VerdictField,
    candidate_entries: Sequence[tuple[int, Any]],
    value: Any,
) -> Any:
    value_key = canonical_json(value)
    for index, actual in candidate_entries:
        if index > len(field.candidates) or not isinstance(actual, dict):
            continue
        if canonical_json(actual.get("candidate_value")) == value_key:
            return copy.deepcopy(field.candidates[index - 1].value)
    return _NO_SLOT_VALUE


def normalize_candidate_layout(value: str | None) -> VerdictCandidateLayout:
    return "slots" if value == "slots" else "array"


def _candidate_entries(
    field: VerdictField,
    candidates: Any,
    *,
    candidate_layout: VerdictCandidateLayout,
    issues: list[JsonDict],
    enforce_validation: bool,
    report_validation: bool,
) -> list[tuple[int, Any]] | None:
    if candidate_layout == "array":
        if not isinstance(candidates, list):
            _validation_issue(
                issues,
                enforce_validation=enforce_validation,
                report_validation=report_validation,
                field=field.name,
                code="candidates_not_list",
                message=f"verdict candidates must be a list: {field.name}",
                actual=candidates,
            )
            return None
        if len(candidates) != len(field.candidates):
            _validation_issue(
                issues,
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
        return list(enumerate(candidates, start=1))

    if not isinstance(candidates, dict):
        _validation_issue(
            issues,
            enforce_validation=enforce_validation,
            report_validation=report_validation,
            field=field.name,
            code="candidates_not_object",
            message=f"verdict candidates must be an object: {field.name}",
            actual=candidates,
        )
        return None

    expected_slots = {str(index) for index in range(1, len(field.candidates) + 1)}
    for key in sorted(set(candidates) - expected_slots):
        _validation_issue(
            issues,
            enforce_validation=enforce_validation,
            report_validation=report_validation,
            field=field.name,
            code="extra_candidate_slot",
            message=f"unexpected candidate slot for {field.name}: {key}",
            actual=key,
        )

    entries: list[tuple[int, Any]] = []
    for index in range(1, len(field.candidates) + 1):
        key = str(index)
        if key not in candidates:
            _validation_issue(
                issues,
                enforce_validation=enforce_validation,
                report_validation=report_validation,
                field=field.name,
                code="missing_candidate_slot",
                message=f"missing candidate slot for {field.name}: {key}",
                position=index,
            )
            continue
        entries.append((index, candidates[key]))
    return entries


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
    return _sorted_candidates(
        _merge_normalized_string_entries(groups.values(), total_trials=len(records))
    )


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
    return _sorted_candidates(
        _merge_normalized_string_entries(groups.values(), total_trials=len(records))
    )


def _add_candidate_observation(entry: dict[str, Any], record: TrialRecord) -> None:
    entry["count"] += 1
    entry["trial_indices"].append(record.index + 1)
    groups = entry["groups"]
    groups[record.group_name] = groups.get(record.group_name, 0) + 1


def _merge_normalized_string_entries(
    entries: Sequence[dict[str, Any]], *, total_trials: int
) -> list[dict[str, Any]]:
    string_groups: dict[str, list[dict[str, Any]]] = {}
    merged: list[dict[str, Any]] = []
    for entry in entries:
        key = _normalized_string_candidate_key(entry.get("value"))
        if key is None:
            merged.append(entry)
            continue
        string_groups.setdefault(key, []).append(entry)

    for group_entries in string_groups.values():
        if len(group_entries) == 1:
            merged.append(_entry_with_normalized_string_value(group_entries[0]))
            continue
        representative = sorted(
            group_entries,
            key=lambda entry: (
                -int(entry["count"]),
                entry["trial_indices"][0] if entry["trial_indices"] else 10**9,
                canonical_json(entry["value"]),
            ),
        )[0]
        merged_groups: dict[str, int] = {}
        trial_indices = sorted(
            {
                int(index)
                for entry in group_entries
                for index in entry["trial_indices"]
            }
        )
        for entry in group_entries:
            for group_name, count in entry["groups"].items():
                merged_groups[group_name] = merged_groups.get(group_name, 0) + int(count)
        merged.append(
            {
                "value": _normalized_candidate_value(representative["value"]),
                "count": min(
                    total_trials,
                    sum(int(entry["count"]) for entry in group_entries),
                ),
                "trial_indices": trial_indices,
                "groups": merged_groups,
            }
        )
    return merged


def _entry_with_normalized_string_value(entry: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalized_candidate_value(entry["value"])
    if normalized == entry["value"]:
        return entry
    return {
        **entry,
        "value": normalized,
    }


def _normalized_candidate_value(value: Any) -> Any:
    if isinstance(value, str):
        return normalize_model_output_strings(value)
    return copy.deepcopy(value)


def _normalized_string_candidate_key(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = normalize_model_output_strings(value).strip()
    decomposed = unicodedata.normalize("NFD", normalized)
    without_marks = "".join(
        character
        for character in decomposed
        if unicodedata.category(character) != "Mn"
    )
    collapsed = " ".join(without_marks.split())
    return collapsed.casefold()


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


def _candidate_schema(
    kind: VerdictKind,
    value_schema: JsonDict,
    *,
    include_evidence_max_length: bool,
) -> JsonDict:
    evidence_schema: JsonDict = {"type": "string"}
    if include_evidence_max_length:
        evidence_schema["maxLength"] = VERDICT_EVIDENCE_MAX_LENGTH
    properties: JsonDict = {
        "candidate_value": copy.deepcopy(value_schema),
        "evidence": evidence_schema,
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
    kind: VerdictKind,
    value_schema: JsonDict,
    candidate_def_name: str,
    *,
    candidate_count: int,
    candidate_layout: VerdictCandidateLayout,
) -> JsonDict:
    if candidate_layout == "slots":
        candidate_keys = [str(index) for index in range(1, candidate_count + 1)]
        candidates_schema: JsonDict = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                key: {"$ref": f"#/$defs/{candidate_def_name}"}
                for key in candidate_keys
            },
            "required": candidate_keys,
        }
    else:
        candidates_schema = {
            "type": "array",
            "items": {"$ref": f"#/$defs/{candidate_def_name}"},
        }
    properties: JsonDict = {
        "field": {"type": "string"},
        "candidates": candidates_schema,
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


def _candidate_definition_name(
    kind: VerdictKind,
    base: str,
    used: set[str],
    *,
    candidate_layout: VerdictCandidateLayout,
) -> str:
    if candidate_layout == "slots":
        return _short_definition_name(used)
    return _unique_name(
        f"Verdict{base}{'Array' if kind == 'array' else 'Single'}Candidate",
        used,
    )


def _verdict_definition_name(
    kind: VerdictKind,
    base: str,
    used: set[str],
    *,
    candidate_layout: VerdictCandidateLayout,
) -> str:
    if candidate_layout == "slots":
        return _short_definition_name(used)
    return _unique_name(
        f"Verdict{base}{'Array' if kind == 'array' else 'Single'}",
        used,
    )


def _short_definition_name(used: set[str]) -> str:
    for name in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz":
        if name not in used:
            used.add(name)
            return name
    return _unique_name("D", used)


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
