from __future__ import annotations

import re

from gensie.schemas.fields import FieldInfo, parse_schema_fields
from gensie.schemas.inspect import JsonDict

SELECTIVE_INLINE_DIRECT_TAGS = frozenset(
    {"entity_array", "enum_classification", "complex_object_array"}
)


def field_tags(field: FieldInfo) -> set[str]:
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


def selective_inline_reasoning_field_names(schema: JsonDict) -> tuple[str, ...]:
    return tuple(
        field.name
        for field in parse_schema_fields(schema)
        if field_tags(field).isdisjoint(SELECTIVE_INLINE_DIRECT_TAGS)
    )


def selective_inline_direct_field_names(schema: JsonDict) -> tuple[str, ...]:
    return tuple(
        field.name
        for field in parse_schema_fields(schema)
        if not field_tags(field).isdisjoint(SELECTIVE_INLINE_DIRECT_TAGS)
    )


def _tokens(value: str) -> frozenset[str]:
    return frozenset(
        token.lower()
        for token in re.findall(r"[^\W_]+", value)
        if len(token) >= 2
    )
