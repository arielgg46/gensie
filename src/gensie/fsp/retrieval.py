from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Mapping

from gensie.fsp.examples import StructuredFspCase, canonical_json
from gensie.schemas.fields import FieldInfo, parse_schema_fields
from gensie.schemas.inspect import JsonDict


@dataclass(frozen=True)
class SchemaProfile:
    fingerprint: str
    field_fingerprints: Mapping[str, str]
    field_names: frozenset[str]
    tags: frozenset[str]
    terms: frozenset[str]


@dataclass(frozen=True)
class FspRetrievalResult:
    case: StructuredFspCase
    score: float
    rank: int
    matched_tags: tuple[str, ...]
    matched_terms: tuple[str, ...]
    schema_match: bool
    compatible_fields: tuple[str, ...]
    method: str = "schema_lexical"

    def metadata(self) -> dict[str, object]:
        return {
            "method": self.method,
            "score": round(self.score, 3),
            "rank": self.rank,
            "matched_tags": list(self.matched_tags),
            "matched_terms": list(self.matched_terms),
            "schema_match": self.schema_match,
            "compatible_fields": list(self.compatible_fields),
        }


def rank_fsp_cases(
    *,
    task_schema: JsonDict,
    task_text: str,
    cases: Iterable[StructuredFspCase],
    top_k: int,
) -> tuple[FspRetrievalResult, ...]:
    query = build_schema_profile(task_schema, extra_text=task_text)
    scored: list[tuple[float, int, StructuredFspCase, dict[str, object]]] = []
    for index, case in enumerate(cases):
        case_profile = build_case_profile(case)
        schema_match = query.fingerprint == case_profile.fingerprint
        compatible_fields = tuple(
            field_name
            for field_name, fingerprint in query.field_fingerprints.items()
            if case_profile.field_fingerprints.get(field_name) == fingerprint
        )
        matched_tags = tuple(sorted(query.tags & case_profile.tags))
        matched_terms = tuple(sorted(query.terms & case_profile.terms))
        field_name_overlap = query.field_names & case_profile.field_names

        score = 0.0
        if schema_match:
            score += 100.0
        score += len(compatible_fields) * 8.0
        score += len(matched_tags) * 4.0
        score += len(field_name_overlap) * 2.0
        score += min(len(matched_terms), 12) * 0.5
        if _domain_matches(case.domain, query.terms):
            score += 2.0
        score -= min(len(case.source_text) / 10000.0, 2.0)

        if score <= 0:
            continue
        scored.append(
            (
                score,
                index,
                case,
                {
                    "matched_tags": matched_tags,
                    "matched_terms": matched_terms,
                    "schema_match": schema_match,
                    "compatible_fields": compatible_fields,
                },
            )
        )

    scored.sort(key=lambda item: (-item[0], item[1]))
    results: list[FspRetrievalResult] = []
    for rank, (score, _index, case, details) in enumerate(
        scored[: max(1, top_k)],
        start=1,
    ):
        results.append(
            FspRetrievalResult(
                case=case,
                score=score,
                rank=rank,
                matched_tags=details["matched_tags"],  # type: ignore[arg-type]
                matched_terms=details["matched_terms"],  # type: ignore[arg-type]
                schema_match=bool(details["schema_match"]),
                compatible_fields=details["compatible_fields"],  # type: ignore[arg-type]
            )
        )
    return tuple(results)


def build_case_profile(case: StructuredFspCase) -> SchemaProfile:
    schema_profile = build_schema_profile(
        case.schema,
        extra_text=" ".join((case.id, case.domain, case.instruction)),
    )
    resource_tags = set(case.tags)
    field_tags = {
        tag
        for field in case.field_examples.values()
        for tag in field.tags
    }
    judge_tags = (
        {
            tag
            for field in case.judge.fields.values()
            for tag in field.tags
        }
        if case.judge is not None
        else set()
    )
    terms = set(schema_profile.terms)
    terms.update(_tokens(case.id))
    terms.update(_tokens(case.domain))
    return SchemaProfile(
        fingerprint=schema_profile.fingerprint,
        field_fingerprints=schema_profile.field_fingerprints,
        field_names=schema_profile.field_names,
        tags=frozenset(schema_profile.tags | resource_tags | field_tags | judge_tags),
        terms=frozenset(terms),
    )


def build_schema_profile(schema: JsonDict, *, extra_text: str = "") -> SchemaProfile:
    fields = parse_schema_fields(schema)
    field_fingerprints = {
        name: canonical_json({"required": field.required, "schema": property_schema})
        for name, field, property_schema in _top_level_field_schemas(schema, fields)
    }
    text_parts = [extra_text, str(schema.get("description") or "")]
    for field in fields:
        text_parts.append(field.name)
        if field.description:
            text_parts.append(field.description)
    tags = set(_schema_tags(fields))
    terms = set(_tokens(" ".join(text_parts)))
    return SchemaProfile(
        fingerprint=canonical_json(schema),
        field_fingerprints=field_fingerprints,
        field_names=frozenset(field.name for field in fields),
        tags=frozenset(tags),
        terms=frozenset(terms),
    )


def _top_level_field_schemas(
    schema: JsonDict, fields: Iterable[FieldInfo]
) -> Iterable[tuple[str, FieldInfo, object]]:
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return ()
    return (
        (field.name, field, properties[field.name])
        for field in fields
        if field.name in properties
    )


def _schema_tags(fields: Iterable[FieldInfo]) -> set[str]:
    tags: set[str] = set()
    for field in fields:
        tags.update(_field_tags(field))
    return tags


def _field_tags(field: FieldInfo) -> set[str]:
    tags: set[str] = set()
    text = " ".join(part for part in (field.name, field.description or "") if part)
    terms = _tokens(text)

    if field.nullable:
        tags.add("grounded_null")
        tags.add("nullable")
    if field.enum is not None:
        tags.add("enum_classification")
    if field.json_type in {"integer", "number"}:
        tags.add("numeric_normalization")
    if field.json_type == "boolean":
        tags.add("boolean_inference")
        if field.nullable:
            tags.add("nullable_boolean")
    if field.json_type == "string":
        tags.add("direct_string")

    if field.minimum is not None or field.maximum is not None:
        tags.add("bounded_score")

    if terms & {"date", "fecha", "year", "año", "ano"}:
        tags.add("date_normalization")
    if terms & {
        "verbatim",
        "source",
        "evidence",
        "fragment",
        "fragmento",
        "span",
        "texto",
        "evidencia",
    }:
        tags.add("long_verbatim_evidence")
    if terms & {
        "sentinel",
        "marker",
        "code",
        "codigo",
        "código",
        "registry",
        "registro",
    }:
        tags.add("sentinel_pattern")

    if field.json_type == "array":
        tags.add("simple_array")
        if field.items is not None:
            item = field.items
            if item.enum is not None:
                tags.add("enum_array")
            if item.json_type == "object":
                tags.discard("simple_array")
                tags.add("complex_object_array")
                if any(
                    child.json_type in {"integer", "number"}
                    for child in item.properties or ()
                ):
                    tags.add("nested_numeric_object_array")
            if terms & {
                "entity",
                "entities",
                "entidad",
                "entidades",
                "person",
                "persona",
                "organization",
                "organizacion",
                "organización",
            }:
                tags.add("entity_array")

    return tags


def _tokens(value: str) -> frozenset[str]:
    return frozenset(
        token.lower()
        for token in re.findall(r"[^\W_]+", value)
        if len(token) >= 2
    )


def _domain_matches(domain: str, terms: frozenset[str]) -> bool:
    return bool(_tokens(domain.replace("_", " ")) & terms)
