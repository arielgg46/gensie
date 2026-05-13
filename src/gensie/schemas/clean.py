from __future__ import annotations

import copy
from typing import Any

PROMPT_SCHEMA_DROP_KEYS = {"additionalProperties", "default", "required", "title"}


def clean_schema_for_prompt(schema: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    schema_copy = copy.deepcopy(schema)
    root_description = schema_copy.get("description")
    clean_schema = _clean_schema_node(schema_copy, is_root=True)
    return clean_schema, root_description if isinstance(root_description, str) else None


def _clean_schema_node(value: Any, *, is_root: bool = False) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, child in value.items():
            if key in PROMPT_SCHEMA_DROP_KEYS:
                continue
            if is_root and key == "description":
                continue
            cleaned[key] = _clean_schema_node(child)
        return cleaned

    if isinstance(value, list):
        return [_clean_schema_node(item) for item in value]

    return value
