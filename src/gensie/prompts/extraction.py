from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from gensie.fsp import FSPProvider, NoFSPProvider
from gensie.pipeline.context import PipelineContext
from gensie.pipeline.specs import ExtractionSpec, FewShotMode, ReasoningMode
from gensie.prompts.base import PromptBundle, PromptBuilder
from gensie.prompts.schema_views import SchemaView, render_schema_view
from gensie.prompts.system import (
    BASE_EXTRACTION_SYSTEM_PROMPT,
    DEEP_INLINE_REASONING_SYSTEM_PROMPT,
    INLINE_REASONING_SYSTEM_PROMPT,
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
        user = build_extraction_prompt(
            context=context,
            extraction=extraction,
            schema_view=schema_view,
            fsp_provider=self.fsp_provider,
            include_default_rules=self.include_default_rules,
        )
        return PromptBundle(
            system=system_prompt_for_reasoning(extraction.reasoning),
            user=user,
            metadata={
                "schema_view": dict(schema_view.metadata),
                "reasoning": extraction.reasoning.value,
            },
        )


def build_extraction_prompt(
    *,
    context: PipelineContext,
    extraction: ExtractionSpec,
    schema_view: SchemaView,
    fsp_provider: FSPProvider,
    include_default_rules: bool = True,
) -> str:
    task = context.task
    sections: list[str] = [
        "TASK:",
        "Extract structured information from the SOURCE TEXT.",
        "",
        "INSTRUCTION:",
        task.instruction,
    ]

    if schema_view.root_description:
        sections.extend(["", "SCHEMA DESCRIPTION:", schema_view.root_description])

    if include_default_rules:
        sections.extend(["", "RULES:", *_rules_for_reasoning(extraction.reasoning)])

    fsp_block = _render_fsp_examples(context, extraction, fsp_provider)
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
            "SOURCE TEXT:",
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
        "- Ground every non-null value in the source text.",
        "- Use null only when the schema allows it and evidence is absent.",
        "- Use [] for arrays when no supported items are found.",
        "- Do not add external facts.",
    ]
    if reasoning is ReasoningMode.TOP_LEVEL:
        return [
            "- For each top-level field, fill reasoning before value.",
            "- reasoning should cite exact evidence or explain why evidence is absent.",
            "- value contains only the final answer.",
            *common,
        ]
    if reasoning is ReasoningMode.DEEP:
        return [
            "- For every field, nested field, and array item, fill reasoning before value.",
            "- reasoning should cite exact evidence or explain why evidence is absent.",
            "- value contains only the final answer for that wrapper.",
            *common,
        ]
    return common


def _render_fsp_examples(
    context: PipelineContext, extraction: ExtractionSpec, provider: FSPProvider
) -> str:
    if extraction.few_shot is FewShotMode.NONE:
        return ""
    examples = provider.examples(context, extraction)
    if not examples:
        return ""

    blocks = ["FEW-SHOT EXAMPLES:"]
    for index, example in enumerate(examples, start=1):
        blocks.append(f"Example {index}: {example.name}")
        blocks.append(example.prompt.rstrip())
        if example.output:
            blocks.append("OUTPUT:")
            blocks.append(json.dumps(example.output, ensure_ascii=False, indent=2))
    return "\n".join(blocks)


def _render_phase_context(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, Mapping):
        serializable = value
    else:
        serializable = {"items": value}
    return (
        "PRE-EXTRACTION CONTEXT:\n"
        + json.dumps(serializable, ensure_ascii=False, indent=2)
    )
