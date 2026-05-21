from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from gensie.fsp import FSPExample, FSPProvider, NoFSPProvider
from gensie.pipeline.context import PipelineContext
from gensie.pipeline.specs import ExtractionSpec, FewShotMode, ReasoningMode
from gensie.prompts.base import PromptBundle, PromptBuilder
from gensie.prompts.schema_views import SchemaView, render_schema_view
from gensie.prompts.system import (
    BASE_EXTRACTION_SYSTEM_PROMPT,
    DEEP_INLINE_REASONING_SYSTEM_PROMPT,
    INLINE_REASONING_SYSTEM_PROMPT,
    STRICT_ANCHORING_RULE,
)


@dataclass(frozen=True)
class ExtractionPromptBuilder(PromptBuilder):
    fsp_provider: FSPProvider = field(default_factory=NoFSPProvider)
    include_default_rules: bool = True

    def build(
        self, context: PipelineContext, extraction: ExtractionSpec
    ) -> PromptBundle:
        schema_view = render_schema_view(
            context.task.target_schema,
            extraction.schema_prompt,
            reasoning=extraction.reasoning,
        )
        fsp_examples = _select_fsp_examples(context, extraction, self.fsp_provider)
        user = build_extraction_prompt(
            context=context,
            extraction=extraction,
            schema_view=schema_view,
            fsp_provider=self.fsp_provider,
            include_default_rules=self.include_default_rules,
            fsp_examples=fsp_examples,
        )
        return PromptBundle(
            system=system_prompt_for_reasoning(extraction.reasoning),
            user=user,
            metadata={
                "schema_view": dict(schema_view.metadata),
                "reasoning": extraction.reasoning.value,
                "fsp_examples": _fsp_examples_metadata(fsp_examples),
            },
        )


def build_extraction_prompt(
    *,
    context: PipelineContext,
    extraction: ExtractionSpec,
    schema_view: SchemaView,
    fsp_provider: FSPProvider,
    include_default_rules: bool = True,
    fsp_examples: tuple[FSPExample, ...] | None = None,
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
        sections.extend(["", "REGLAS:", *_rules_for_reasoning(extraction.reasoning)])

    if fsp_examples is None:
        fsp_examples = _select_fsp_examples(context, extraction, fsp_provider)
    fsp_block = _render_fsp_examples(fsp_examples)
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


def system_prompt_for_reasoning(reasoning: ReasoningMode | str) -> str:
    mode = ReasoningMode(reasoning)
    if mode is ReasoningMode.TOP_LEVEL:
        return INLINE_REASONING_SYSTEM_PROMPT
    if mode is ReasoningMode.DEEP:
        return DEEP_INLINE_REASONING_SYSTEM_PROMPT
    return BASE_EXTRACTION_SYSTEM_PROMPT


def _rules_for_reasoning(reasoning: ReasoningMode) -> list[str]:
    common = [
        "- Fundamenta cada value no nulo en el texto fuente.",
        "- Usa null solo cuando el schema lo permita y no haya evidencia suficiente.",
        "- Usa [] para arrays cuando no encuentres elementos respaldados por el texto.",
        "- No añadas hechos externos.",
    ]
    if reasoning is ReasoningMode.TOP_LEVEL:
        return [
            "- Para cada campo de primer nivel, escribe reasoning antes de value.",
            "- reasoning debe citar evidencia exacta o explicar por qué no hay evidencia suficiente.",
            "- value contiene solo la respuesta final.",
            *common,
            STRICT_ANCHORING_RULE,
        ]
    if reasoning is ReasoningMode.DEEP:
        return [
            "- Para cada campo, subcampo y elemento de array, escribe reasoning antes de value.",
            "- reasoning debe citar evidencia exacta o explicar por qué no hay evidencia suficiente.",
            "- value contiene solo la respuesta final de ese nodo.",
            *common,
            STRICT_ANCHORING_RULE,
        ]
    return common


def _select_fsp_examples(
    context: PipelineContext, extraction: ExtractionSpec, provider: FSPProvider
) -> tuple[FSPExample, ...]:
    if extraction.few_shot is FewShotMode.NONE:
        return ()
    return provider.examples(context, extraction)


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


def _fsp_examples_metadata(examples: tuple[FSPExample, ...]) -> list[dict[str, Any]]:
    return [
        {
            "name": example.name,
            **dict(example.metadata),
        }
        for example in examples
    ]


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
