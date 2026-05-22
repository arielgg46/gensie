from __future__ import annotations

import copy
from typing import Any

from gensie.schemas.reasoning import transform_schema_for_reasoning


def build_json_schema_response_format(
    schema: dict[str, Any],
    reasoning: Any,
    *,
    name: str = "extraction",
    require_all_properties: bool = False,
) -> dict[str, Any]:
    generation_schema = transform_schema_for_reasoning(schema, reasoning)
    if require_all_properties:
        generation_schema = require_all_json_schema_properties(generation_schema)
    return {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "schema": generation_schema,
            "strict": True,
        },
    }


def require_all_json_schema_properties(schema: dict[str, Any]) -> dict[str, Any]:
    """Return a schema copy where every object requires all declared properties."""
    return _require_all_properties(copy.deepcopy(schema))


def _require_all_properties(value: Any) -> Any:
    if isinstance(value, dict):
        for key, item in list(value.items()):
            value[key] = _require_all_properties(item)

        properties = value.get("properties")
        if isinstance(properties, dict):
            value["required"] = [
                name for name in properties
                if isinstance(name, str)
            ]
        return value

    if isinstance(value, list):
        return [_require_all_properties(item) for item in value]

    return value
