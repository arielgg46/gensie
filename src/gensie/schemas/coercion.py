from __future__ import annotations

import copy
from typing import Any, Mapping

from gensie.schemas.inspect import JsonDict, deref, is_null_schema


def coerce_nullable_string_nulls(
    value: Mapping[str, Any],
    schema: JsonDict,
) -> JsonDict:
    """Convert string null markers to JSON null where the schema permits null."""
    return _coerce_value(copy.deepcopy(dict(value)), schema, schema)


def _coerce_value(value: Any, schema: JsonDict, root_schema: JsonDict) -> Any:
    schema, nullable = _nullable_schema(schema, root_schema)

    if isinstance(value, str) and nullable and _is_null_marker(value):
        return None
    if value is None:
        return None

    current_type = _schema_type(schema)
    if current_type == "object" and isinstance(value, dict):
        properties = schema.get("properties")
        if not isinstance(properties, dict):
            return value
        return {
            key: _coerce_value(item, properties[key], root_schema)
            if key in properties and isinstance(properties[key], dict)
            else item
            for key, item in value.items()
        }

    if current_type == "array" and isinstance(value, list):
        item_schema = schema.get("items")
        if not isinstance(item_schema, dict):
            return value
        return [_coerce_value(item, item_schema, root_schema) for item in value]

    return value


def _nullable_schema(schema: JsonDict, root_schema: JsonDict) -> tuple[JsonDict, bool]:
    schema = deref(schema, root_schema)

    for key in ("anyOf", "oneOf"):
        alternatives = schema.get(key)
        if not isinstance(alternatives, list):
            continue

        non_null_alternatives: list[JsonDict] = []
        has_null = False
        for alternative in alternatives:
            if not isinstance(alternative, dict):
                return schema, False
            alternative = deref(alternative, root_schema)
            if is_null_schema(alternative):
                has_null = True
            else:
                non_null_alternatives.append(alternative)

        if has_null:
            if len(non_null_alternatives) == 1:
                inner = dict(non_null_alternatives[0])
                for inherited_key in ("description", "title", "default", "examples"):
                    if inherited_key in schema and inherited_key not in inner:
                        inner[inherited_key] = schema[inherited_key]
                return deref(inner, root_schema), True
            return schema, True

    current_type = schema.get("type")
    if isinstance(current_type, list) and "null" in current_type:
        non_null_types = [item for item in current_type if item != "null"]
        if len(non_null_types) == 1:
            inner = dict(schema)
            inner["type"] = non_null_types[0]
            return deref(inner, root_schema), True
        return schema, True

    return schema, False


def _schema_type(schema: JsonDict) -> str:
    current_type = schema.get("type")
    return current_type if isinstance(current_type, str) else ""


def _is_null_marker(value: str) -> bool:
    return value.strip().lower() == "null"
