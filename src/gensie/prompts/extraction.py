from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Mapping

from gensie.fsp import FSPExample, FSPProvider, NoFSPProvider
from gensie.fsp.examples import (
    DEFAULT_REASONING_SECTION_LABELS,
    ReasoningSectionLabels,
)
from gensie.fsp.selection import FspSelection
from gensie.pipeline.context import PipelineContext
from gensie.pipeline.specs import ExtractionSpec, FewShotMode, ReasoningMode
from gensie.prompts.base import PromptBundle, PromptBuilder
from gensie.prompts.extraction_layouts import (
    build_default_extraction_user_prompt,
    build_extraction_prompt_layout,
    should_use_same_schema_rag_compact_layout,
)
from gensie.prompts.schema_views import SchemaView, render_schema_view
from gensie.prompts.system import (
    BASE_EXTRACTION_SYSTEM_PROMPT,
    DEEP_INLINE_REASONING_SYSTEM_PROMPT,
    EXTRACTION_RULES,
    INLINE_REASONING_SYSTEM_PROMPT,
    REASONING_EXTRACTION_RULES,
    STRICT_ANCHORING_RULE,
    strict_reasoning_format_rule,
)

ENRICHED_RAG_FIELD_DESCRIPTIONS_ENV = (
    "GENSIE_FSP_RAG_USE_ENRICHED_DESCRIPTIONS"
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
        system = system_prompt_for_reasoning(extraction.reasoning)
        fsp_selection = _select_fsp_selection(
            context,
            extraction,
            self.fsp_provider,
        )
        rules = _rules_for_reasoning(
            extraction.reasoning,
            labels=_reasoning_labels_for_selection(fsp_selection),
        )
        fsp_examples = (
            ()
            if fsp_selection is not None
            else _select_fsp_examples(context, extraction, self.fsp_provider)
        )
        schema_view = _schema_view_with_enriched_rag_descriptions(
            context=context,
            extraction=extraction,
            schema_view=schema_view,
            fsp_selection=fsp_selection,
        )
        layout = build_extraction_prompt_layout(
            context=context,
            extraction=extraction,
            schema_view=schema_view,
            default_system=system,
            default_rules=rules,
            include_default_rules=self.include_default_rules,
            fsp_examples=fsp_examples,
            fsp_selection=fsp_selection,
        )
        return PromptBundle(
            system=layout.system,
            user=layout.user,
            metadata={
                "schema_view": dict(schema_view.metadata),
                "reasoning": extraction.reasoning.value,
                "layout": layout.name,
                "prompt_layout": layout.name,
                "fsp_examples": layout.fsp_metadata,
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
    fsp_selection: FspSelection | None = None
    if fsp_examples is None:
        fsp_selection = _select_fsp_selection(context, extraction, fsp_provider)
        fsp_examples = (
            ()
            if fsp_selection is not None
            else _select_fsp_examples(context, extraction, fsp_provider)
        )
    return build_default_extraction_user_prompt(
        context=context,
        extraction=extraction,
        schema_view=schema_view,
        default_rules=_rules_for_reasoning(
            extraction.reasoning,
            labels=_reasoning_labels_for_selection(fsp_selection),
        ),
        include_default_rules=include_default_rules,
        fsp_examples=fsp_examples,
        fsp_selection=fsp_selection,
    )


def system_prompt_for_reasoning(reasoning: ReasoningMode | str) -> str:
    mode = ReasoningMode(reasoning)
    if mode is ReasoningMode.TOP_LEVEL:
        return INLINE_REASONING_SYSTEM_PROMPT
    if mode is ReasoningMode.DEEP:
        return DEEP_INLINE_REASONING_SYSTEM_PROMPT
    return BASE_EXTRACTION_SYSTEM_PROMPT


def _rules_for_reasoning(
    reasoning: ReasoningMode,
    *,
    labels: ReasoningSectionLabels = DEFAULT_REASONING_SECTION_LABELS,
) -> list[str]:
    mode = ReasoningMode(reasoning)
    rules = [*EXTRACTION_RULES]
    if mode is not ReasoningMode.NONE:
        rules.extend((REASONING_EXTRACTION_RULES[0], strict_reasoning_format_rule(labels)))
        rules.extend(REASONING_EXTRACTION_RULES[1:])
    rules.append(STRICT_ANCHORING_RULE)
    return rules


def _reasoning_labels_for_selection(
    selection: FspSelection | None,
) -> ReasoningSectionLabels:
    return selection.labels if selection is not None else DEFAULT_REASONING_SECTION_LABELS


def _select_fsp_examples(
    context: PipelineContext, extraction: ExtractionSpec, provider: FSPProvider
) -> tuple[FSPExample, ...]:
    if extraction.few_shot is FewShotMode.NONE:
        return ()
    return provider.examples(context, extraction)


def _select_fsp_selection(
    context: PipelineContext, extraction: ExtractionSpec, provider: FSPProvider
) -> FspSelection | None:
    if extraction.few_shot is FewShotMode.NONE:
        return None
    select = getattr(provider, "select", None)
    if not callable(select):
        return None
    selection = select(context, extraction)
    return selection if isinstance(selection, FspSelection) else None


def _schema_view_with_enriched_rag_descriptions(
    *,
    context: PipelineContext,
    extraction: ExtractionSpec,
    schema_view: SchemaView,
    fsp_selection: FspSelection | None,
) -> SchemaView:
    if not _use_enriched_rag_field_descriptions():
        return schema_view
    if not should_use_same_schema_rag_compact_layout(extraction, fsp_selection):
        return schema_view

    descriptions = _merged_enriched_field_descriptions(fsp_selection)
    if not descriptions:
        return schema_view
    return render_schema_view(
        context.task.target_schema,
        extraction.schema_prompt,
        reasoning=extraction.reasoning,
        field_description_overrides=descriptions,
    )


def _use_enriched_rag_field_descriptions() -> bool:
    value = os.getenv(ENRICHED_RAG_FIELD_DESCRIPTIONS_ENV, "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _merged_enriched_field_descriptions(
    selection: FspSelection | None,
) -> Mapping[str, str]:
    if selection is None:
        return {}
    descriptions: dict[str, str] = {}
    for selected in selection.cases:
        for path, description in selected.case.enriched_field_descriptions.items():
            descriptions.setdefault(path, description)
    return descriptions
