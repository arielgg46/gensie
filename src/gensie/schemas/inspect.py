from __future__ import annotations

import keyword
import re
from typing import Any

JsonDict = dict[str, Any]


def is_null_schema(schema: JsonDict) -> bool:
    return schema.get("type") == "null"


def resolve_local_ref(root_schema: JsonDict, ref: str) -> JsonDict:
    if not ref.startswith("#/"):
        return {}
    current: Any = root_schema
    for part in ref[2:].split("/"):
        if not isinstance(current, dict):
            return {}
        current = current.get(part)
        if current is None:
            return {}
    return current if isinstance(current, dict) else {}


def deref(schema: JsonDict, root_schema: JsonDict) -> JsonDict:
    ref = schema.get("$ref")
    if not isinstance(ref, str):
        return schema
    resolved = resolve_local_ref(root_schema, ref)
    if not resolved:
        return schema

    merged = dict(resolved)
    merged.update({key: value for key, value in schema.items() if key != "$ref"})
    return merged


def unwrap_nullable_anyof(schema: JsonDict, root_schema: JsonDict) -> tuple[JsonDict, bool]:
    schema = deref(schema, root_schema)
    any_of = schema.get("anyOf")
    if not isinstance(any_of, list) or not any_of:
        return schema, False

    alternatives: list[JsonDict] = []
    has_null = False
    for alternative in any_of:
        if not isinstance(alternative, dict):
            return schema, False
        alternative = deref(alternative, root_schema)
        if is_null_schema(alternative):
            has_null = True
        else:
            alternatives.append(alternative)

    if has_null and len(alternatives) == 1:
        inner = dict(alternatives[0])
        for key in ("description", "title", "default", "examples"):
            if key in schema and key not in inner:
                inner[key] = schema[key]
        return inner, True

    return schema, False


def schema_type(schema: JsonDict) -> str:
    value = schema.get("type")
    return value if isinstance(value, str) else ""


def safe_name(value: str) -> str:
    name = re.sub(r"[^0-9a-zA-Z_]+", "_", value).strip("_")
    if not name:
        name = "field"
    if name[0].isdigit():
        name = f"f_{name}"
    if keyword.iskeyword(name):
        name = f"{name}_"
    return name


def pascal_case(value: str) -> str:
    parts = [part for part in re.split(r"[^0-9a-zA-Z]+", value) if part]
    if not parts:
        return "Model"
    name = "".join(part[:1].upper() + part[1:] for part in parts)
    if name[0].isdigit():
        return f"M{name}"
    return name
