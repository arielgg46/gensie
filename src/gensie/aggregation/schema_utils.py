from __future__ import annotations

import json
from typing import Any

from gensie.schemas.inspect import deref, resolve_local_ref

JsonDict = dict[str, Any]


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def schema_type(schema: JsonDict) -> str:
    value = schema.get("type")
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        non_null = [item for item in value if item != "null"]
        if len(non_null) == 1 and isinstance(non_null[0], str):
            return non_null[0]
    if "enum" in schema:
        return "enum"
    return ""


def unwrap_nullable_schema(schema: JsonDict, root_schema: JsonDict) -> tuple[JsonDict, bool]:
    schema = deref(schema, root_schema)

    any_of = schema.get("anyOf")
    if isinstance(any_of, list):
        non_null_alts: list[JsonDict] = []
        has_null = False
        for alt in any_of:
            if not isinstance(alt, dict):
                return schema, False
            alt = deref(alt, root_schema)
            if alt.get("type") == "null":
                has_null = True
            else:
                non_null_alts.append(alt)
        if has_null and len(non_null_alts) == 1:
            inner = dict(non_null_alts[0])
            for key in ("description", "title", "default", "examples"):
                if key in schema and key not in inner:
                    inner[key] = schema[key]
            return deref(inner, root_schema), True

    current_type = schema.get("type")
    if isinstance(current_type, list) and "null" in current_type:
        non_null_types = [item for item in current_type if item != "null"]
        if len(non_null_types) == 1:
            inner = dict(schema)
            inner["type"] = non_null_types[0]
            return inner, True

    return schema, False


def is_required(schema: JsonDict, field_name: str) -> bool:
    required = schema.get("required")
    return isinstance(required, list) and field_name in required


def deref_item_schema(schema: JsonDict, root_schema: JsonDict) -> JsonDict:
    item_schema = schema.get("items") if isinstance(schema.get("items"), dict) else {}
    if "$ref" in item_schema and isinstance(item_schema["$ref"], str):
        item_schema = resolve_local_ref(root_schema, item_schema["$ref"])
    item_schema, _ = unwrap_nullable_schema(item_schema, root_schema)
    return deref(item_schema, root_schema)
