from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from gensie.pipeline.specs import ReasoningMode, SchemaPromptMode
from gensie.schemas.clean import clean_schema_for_prompt
from gensie.schemas.pydantic_render import (
    render_deep_reasoned_pydantic_schema,
    render_pydantic_code,
    render_reasoned_pydantic_schema,
)
from gensie.schemas.reasoning import build_inline_reasoning_prompt_schema


@dataclass(frozen=True)
class SchemaView:
    heading: str
    content: str
    root_description: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))


def render_schema_view(
    schema: dict[str, Any],
    mode: SchemaPromptMode | str,
    *,
    reasoning: ReasoningMode | str = ReasoningMode.NONE,
    field_description_overrides: Mapping[str, str] | None = None,
) -> SchemaView:
    schema = _schema_with_field_description_overrides(
        schema,
        field_description_overrides,
    )
    prompt_mode = SchemaPromptMode(mode)
    reasoning_mode = ReasoningMode(reasoning)
    override_metadata = _override_metadata(field_description_overrides)

    if prompt_mode is SchemaPromptMode.JSON_SCHEMA:
        return SchemaView(
            heading="SCHEMA",
            content=json.dumps(schema, ensure_ascii=False, indent=2),
            root_description=_root_description(schema),
            metadata={
                "mode": prompt_mode.value,
                "cleaned": False,
                **override_metadata,
            },
        )

    if prompt_mode is SchemaPromptMode.CLEAN_JSON_SCHEMA:
        clean_schema, root_description = clean_schema_for_prompt(schema)
        return SchemaView(
            heading="SCHEMA",
            content=json.dumps(clean_schema, ensure_ascii=False, indent=2),
            root_description=root_description,
            metadata={
                "mode": prompt_mode.value,
                "cleaned": True,
                **override_metadata,
            },
        )

    if prompt_mode is SchemaPromptMode.INLINE_REASONING_WRAPPER:
        return render_inline_prompt_schema_view(schema)

    if prompt_mode is SchemaPromptMode.PYDANTIC:
        return SchemaView(
            heading="SCHEMA PYDANTIC",
            content=render_pydantic_code(schema),
            root_description=_root_description(schema),
            metadata={"mode": prompt_mode.value, **override_metadata},
        )

    if prompt_mode is SchemaPromptMode.REASONED_PYDANTIC:
        if reasoning_mode is ReasoningMode.NONE:
            raise ValueError("reasoned pydantic schema requires inline reasoning")
        renderer = (
            render_deep_reasoned_pydantic_schema
            if reasoning_mode is ReasoningMode.DEEP
            else render_reasoned_pydantic_schema
        )
        return SchemaView(
            heading="SCHEMA PYDANTIC",
            content=renderer(schema),
            root_description=_root_description(schema),
            metadata={
                "mode": prompt_mode.value,
                "reasoning": reasoning_mode.value,
                **override_metadata,
            },
        )

    raise ValueError(f"unsupported schema prompt mode: {mode}")


def render_inline_prompt_schema_view(schema: dict[str, Any]) -> SchemaView:
    clean_schema, root_description = clean_schema_for_prompt(schema)
    del clean_schema
    return SchemaView(
        heading="SCHEMA",
        content=json.dumps(
            build_inline_reasoning_prompt_schema(schema), ensure_ascii=False, indent=2
        ),
        root_description=root_description,
        metadata={"mode": "inline_reasoning_wrapper"},
    )


def _root_description(schema: dict[str, Any]) -> str | None:
    value = schema.get("description")
    return value if isinstance(value, str) else None


def _schema_with_field_description_overrides(
    schema: dict[str, Any],
    overrides: Mapping[str, str] | None,
) -> dict[str, Any]:
    clean_overrides = {
        path.strip(): description.strip()
        for path, description in (overrides or {}).items()
        if path.strip() and description.strip()
    }
    if not clean_overrides:
        return schema

    patched = copy.deepcopy(schema)
    for path, description in clean_overrides.items():
        _set_field_description(patched, path, description)
    return patched


def _set_field_description(
    root_schema: dict[str, Any],
    field_path: str,
    description: str,
) -> bool:
    current: dict[str, Any] = root_schema
    parts = field_path.split(".")
    for index, raw_part in enumerate(parts):
        is_array_item = raw_part.endswith("[]")
        property_name = raw_part[:-2] if is_array_item else raw_part
        current = _schema_for_traversal(root_schema, current)
        properties = current.get("properties")
        if not property_name or not isinstance(properties, dict):
            return False
        property_schema = properties.get(property_name)
        if not isinstance(property_schema, dict):
            return False

        is_last = index == len(parts) - 1
        if is_last and not is_array_item:
            property_schema["description"] = description
            return True

        next_schema = _schema_for_traversal(root_schema, property_schema)
        if is_array_item:
            items = next_schema.get("items")
            if not isinstance(items, dict):
                return False
            if is_last:
                _schema_for_traversal(root_schema, items)["description"] = description
                return True
            current = items
        else:
            current = property_schema
    return False


def _schema_for_traversal(
    root_schema: dict[str, Any],
    schema: dict[str, Any],
) -> dict[str, Any]:
    ref = schema.get("$ref")
    if isinstance(ref, str):
        resolved = _resolve_ref(root_schema, ref)
        if resolved is not None:
            return resolved

    any_of = schema.get("anyOf")
    if isinstance(any_of, list):
        for option in any_of:
            if not isinstance(option, dict) or option.get("type") == "null":
                continue
            return _schema_for_traversal(root_schema, option)

    return schema


def _resolve_ref(root_schema: dict[str, Any], ref: str) -> dict[str, Any] | None:
    if not ref.startswith("#/$defs/"):
        return None
    name = ref.removeprefix("#/$defs/")
    defs = root_schema.get("$defs")
    if not isinstance(defs, dict):
        return None
    value = defs.get(name)
    return value if isinstance(value, dict) else None


def _override_metadata(overrides: Mapping[str, str] | None) -> dict[str, Any]:
    fields = sorted(path for path, value in (overrides or {}).items() if path and value)
    if not fields:
        return {}
    return {"field_description_overrides": fields}
