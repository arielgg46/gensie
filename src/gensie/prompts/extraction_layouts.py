from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from gensie.fsp.base import FSPExample
from gensie.fsp.render_extraction import (
    render_full_extraction_fsp_example,
    render_same_schema_extraction_fsp_example,
)
from gensie.fsp.selection import FspSelection
from gensie.pipeline.context import PipelineContext
from gensie.pipeline.specs import (
    ExtractionSpec,
    FewShotMode,
    ReasoningMode,
    SchemaPromptMode,
)
from gensie.prompts.schema_views import SchemaView
from gensie.prompts.system import EXTRACTION_RULES_HEADER, STRICT_ANCHORING_RULE
from gensie.schemas.reasoning import has_reasoning_output_fields

DEFAULT_EXTRACTION_LAYOUT = "default"
SAME_SCHEMA_RAG_COMPACT_LAYOUT = "same_schema_rag_compact"


@dataclass(frozen=True)
class ExtractionPromptLayoutResult:
    name: str
    system: str
    user: str
    fsp_metadata: list[dict[str, Any]]


def build_extraction_prompt_layout(
    *,
    context: PipelineContext,
    extraction: ExtractionSpec,
    schema_view: SchemaView,
    default_system: str,
    default_rules: Sequence[str],
    include_default_rules: bool,
    fsp_examples: tuple[FSPExample, ...] = (),
    fsp_selection: FspSelection | None = None,
) -> ExtractionPromptLayoutResult:
    rules = tuple(default_rules)
    if should_use_same_schema_rag_compact_layout(extraction, fsp_selection):
        assert fsp_selection is not None
        return _build_same_schema_rag_compact_layout(
            context=context,
            extraction=extraction,
            schema_view=schema_view,
            default_system=default_system,
            default_rules=rules,
            include_default_rules=include_default_rules,
            fsp_selection=fsp_selection,
        )

    return _build_default_layout(
        context=context,
        extraction=extraction,
        schema_view=schema_view,
        system=default_system,
        default_rules=rules,
        include_default_rules=include_default_rules,
        fsp_examples=fsp_examples,
        fsp_selection=fsp_selection,
    )


def build_default_extraction_user_prompt(
    *,
    context: PipelineContext,
    extraction: ExtractionSpec,
    schema_view: SchemaView,
    default_rules: Sequence[str],
    include_default_rules: bool,
    fsp_examples: tuple[FSPExample, ...] = (),
    fsp_selection: FspSelection | None = None,
) -> str:
    return _build_default_user_prompt(
        context=context,
        extraction=extraction,
        schema_view=schema_view,
        default_rules=tuple(default_rules),
        include_default_rules=include_default_rules,
        fsp_examples=fsp_examples,
        fsp_selection=fsp_selection,
    )


def _build_default_layout(
    *,
    context: PipelineContext,
    extraction: ExtractionSpec,
    schema_view: SchemaView,
    system: str,
    default_rules: Sequence[str],
    include_default_rules: bool,
    fsp_examples: tuple[FSPExample, ...],
    fsp_selection: FspSelection | None,
) -> ExtractionPromptLayoutResult:
    user = _build_default_user_prompt(
        context=context,
        extraction=extraction,
        schema_view=schema_view,
        default_rules=default_rules,
        include_default_rules=include_default_rules,
        fsp_examples=fsp_examples,
        fsp_selection=fsp_selection,
    )
    return ExtractionPromptLayoutResult(
        name=DEFAULT_EXTRACTION_LAYOUT,
        system=system,
        user=user,
        fsp_metadata=_fsp_metadata(fsp_examples, fsp_selection),
    )


def _build_same_schema_rag_compact_layout(
    *,
    context: PipelineContext,
    extraction: ExtractionSpec,
    schema_view: SchemaView,
    default_system: str,
    default_rules: Sequence[str],
    include_default_rules: bool,
    fsp_selection: FspSelection,
) -> ExtractionPromptLayoutResult:
    system = _build_same_schema_system_prompt(
        context=context,
        extraction=extraction,
        schema_view=schema_view,
        default_system=default_system,
        default_rules=default_rules,
        include_default_rules=include_default_rules,
    )
    user = _build_same_schema_user_prompt(
        context=context,
        extraction=extraction,
        fsp_selection=fsp_selection,
    )
    return ExtractionPromptLayoutResult(
        name=SAME_SCHEMA_RAG_COMPACT_LAYOUT,
        system=system,
        user=user,
        fsp_metadata=fsp_selection.metadata(),
    )


def _build_default_user_prompt(
    *,
    context: PipelineContext,
    extraction: ExtractionSpec,
    schema_view: SchemaView,
    default_rules: Sequence[str],
    include_default_rules: bool,
    fsp_examples: tuple[FSPExample, ...],
    fsp_selection: FspSelection | None,
) -> str:
    task = context.task
    sections: list[str] = [
        "TAREA:",
        "Extrae información estructurada del TEXTO FUENTE.",
        "",
        "INSTRUCCIÓN:",
        task.instruction,
    ]

    if schema_view.root_description:
        sections.extend(["", "DESCRIPCIÓN DEL SCHEMA:", schema_view.root_description])

    if include_default_rules:
        sections.extend(["", EXTRACTION_RULES_HEADER, *default_rules])

    fsp_block = _render_default_fsp_block(
        extraction=extraction,
        fsp_examples=fsp_examples,
        fsp_selection=fsp_selection,
    )
    if fsp_block:
        sections.extend(["", fsp_block])

    phase_block = _render_phase_context(context.metadata.get("phase_results"))
    if phase_block:
        sections.extend(["", phase_block])

    sections.extend(
        [
            "",
            f"{schema_view.heading}:",
            schema_view.content.rstrip(),
            "",
            "TEXTO FUENTE:",
            task.input_text,
        ]
    )
    return "\n".join(sections)


def _build_same_schema_system_prompt(
    *,
    context: PipelineContext,
    extraction: ExtractionSpec,
    schema_view: SchemaView,
    default_system: str,
    default_rules: Sequence[str],
    include_default_rules: bool,
) -> str:
    sections: list[str] = [_system_without_strict_anchor(default_system).rstrip()]

    if include_default_rules:
        sections.extend(["", EXTRACTION_RULES_HEADER, *default_rules])

    if schema_view.root_description:
        sections.extend(["", "DESCRIPCIÓN DEL SCHEMA:", schema_view.root_description])

    example_guidance = (
        "Los ejemplos del mensaje de usuario usan este mismo schema. "
        "Úsalos para interpretar campos, nulls, listas, enums y el formato "
        "de salida; no copies sus valores al nuevo TEXTO FUENTE."
    )
    if (
        extraction.reasoning is not ReasoningMode.NONE
        and has_reasoning_output_fields(context.task.target_schema, extraction.reasoning)
    ):
        example_guidance = (
            "Los ejemplos del mensaje de usuario usan este mismo schema. "
            "Úsalos para interpretar campos, nulls, listas, enums y el estilo "
            "de reasoning; no copies sus valores al nuevo TEXTO FUENTE."
        )

    sections.extend(
        [
            "",
            f"{schema_view.heading}:",
            schema_view.content.rstrip(),
            "",
            example_guidance,
        ]
    )
    return "\n".join(sections)


def _build_same_schema_user_prompt(
    *,
    context: PipelineContext,
    extraction: ExtractionSpec,
    fsp_selection: FspSelection,
) -> str:
    sections: list[str] = [
        _render_selection_fsp_block(
            extraction=extraction,
            fsp_selection=fsp_selection,
            same_schema=True,
        )
    ]

    phase_block = _render_phase_context(context.metadata.get("phase_results"))
    if phase_block:
        sections.extend(["", phase_block])

    sections.extend(
        [
            "",
            "TAREA NUEVA:",
            "",
            "INSTRUCCIÓN:",
            context.task.instruction,
            "",
            "TEXTO FUENTE:",
            context.task.input_text,
        ]
    )
    return "\n".join(sections)


def _render_default_fsp_block(
    *,
    extraction: ExtractionSpec,
    fsp_examples: tuple[FSPExample, ...],
    fsp_selection: FspSelection | None,
) -> str:
    if fsp_selection is not None:
        return _render_selection_fsp_block(
            extraction=extraction,
            fsp_selection=fsp_selection,
            same_schema=False,
        )
    return _render_fsp_examples(fsp_examples)


def _render_selection_fsp_block(
    *,
    extraction: ExtractionSpec,
    fsp_selection: FspSelection,
    same_schema: bool,
) -> str:
    if not fsp_selection.cases:
        return ""

    renderer = (
        render_same_schema_extraction_fsp_example
        if same_schema
        else render_full_extraction_fsp_example
    )
    blocks = ["EJEMPLOS FEW-SHOT:"]
    for index, selected in enumerate(fsp_selection.cases, start=1):
        blocks.append(f"Ejemplo {index}: {selected.name}")
        blocks.append(
            renderer(
                selected.case,
                extraction,
                labels=fsp_selection.labels,
            ).rstrip()
        )
    return "\n".join(blocks)


def _render_fsp_examples(examples: tuple[FSPExample, ...]) -> str:
    if not examples:
        return ""

    blocks = ["EJEMPLOS FEW-SHOT:"]
    for index, example in enumerate(examples, start=1):
        blocks.append(f"Ejemplo {index}: {example.name}")
        blocks.append(example.prompt.rstrip())
        if example.output:
            blocks.append("SALIDA:")
            blocks.append(json.dumps(example.output, ensure_ascii=False, indent=2))
    return "\n".join(blocks)


def _render_phase_context(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, Mapping):
        serializable = value
    else:
        serializable = {"elementos": value}
    return (
        "CONTEXTO PREVIO A LA EXTRACCIÓN:\n"
        + json.dumps(serializable, ensure_ascii=False, indent=2)
    )


def _fsp_metadata(
    examples: tuple[FSPExample, ...],
    selection: FspSelection | None,
) -> list[dict[str, Any]]:
    if selection is not None:
        return selection.metadata()
    return [{"name": example.name, **dict(example.metadata)} for example in examples]


def _system_without_strict_anchor(system: str) -> str:
    return system.replace(STRICT_ANCHORING_RULE, "").rstrip()


def _should_use_same_schema_layout(
    extraction: ExtractionSpec,
    selection: FspSelection | None,
) -> bool:
    return should_use_same_schema_rag_compact_layout(extraction, selection)


def should_use_same_schema_rag_compact_layout(
    extraction: ExtractionSpec,
    selection: FspSelection | None,
) -> bool:
    supported_reasoning = {
        ReasoningMode.NONE,
        ReasoningMode.TOP_LEVEL,
        ReasoningMode.SELECTIVE_TOP_LEVEL,
    }
    supported_schema_prompts = {
        SchemaPromptMode.PYDANTIC,
        SchemaPromptMode.REASONED_PYDANTIC,
    }
    return (
        extraction.few_shot is FewShotMode.RAG
        and extraction.reasoning in supported_reasoning
        and extraction.schema_prompt in supported_schema_prompts
        and selection is not None
        and selection.all_schema_match
    )
