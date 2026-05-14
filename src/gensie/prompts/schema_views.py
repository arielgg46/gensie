from __future__ import annotations

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
) -> SchemaView:
    prompt_mode = SchemaPromptMode(mode)
    reasoning_mode = ReasoningMode(reasoning)

    if prompt_mode is SchemaPromptMode.JSON_SCHEMA:
        return SchemaView(
            heading="SCHEMA",
            content=json.dumps(schema, ensure_ascii=False, indent=2),
            root_description=_root_description(schema),
            metadata={"mode": prompt_mode.value, "cleaned": False},
        )

    if prompt_mode is SchemaPromptMode.CLEAN_JSON_SCHEMA:
        clean_schema, root_description = clean_schema_for_prompt(schema)
        return SchemaView(
            heading="SCHEMA",
            content=json.dumps(clean_schema, ensure_ascii=False, indent=2),
            root_description=root_description,
            metadata={"mode": prompt_mode.value, "cleaned": True},
        )

    if prompt_mode is SchemaPromptMode.INLINE_REASONING_WRAPPER:
        return render_inline_prompt_schema_view(schema)

    if prompt_mode is SchemaPromptMode.PYDANTIC:
        return SchemaView(
            heading="SCHEMA PYDANTIC",
            content=render_pydantic_code(schema),
            root_description=_root_description(schema),
            metadata={"mode": prompt_mode.value},
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
            metadata={"mode": prompt_mode.value, "reasoning": reasoning_mode.value},
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
