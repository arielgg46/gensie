from __future__ import annotations

from dataclasses import dataclass, field

from gensie.fsp import FSPExample, FSPProvider, NoFSPProvider
from gensie.fsp.selection import FspSelection
from gensie.pipeline.context import PipelineContext
from gensie.pipeline.specs import ExtractionSpec, FewShotMode, ReasoningMode
from gensie.prompts.base import PromptBundle, PromptBuilder
from gensie.prompts.extraction_layouts import (
    build_default_extraction_user_prompt,
    build_extraction_prompt_layout,
)
from gensie.prompts.schema_views import SchemaView, render_schema_view
from gensie.prompts.system import (
    BASE_EXTRACTION_SYSTEM_PROMPT,
    DEEP_INLINE_REASONING_SYSTEM_PROMPT,
    EXTRACTION_RULES,
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
        system = system_prompt_for_reasoning(extraction.reasoning)
        rules = _rules_for_reasoning(extraction.reasoning)
        fsp_selection = _select_fsp_selection(
            context,
            extraction,
            self.fsp_provider,
        )
        fsp_examples = (
            ()
            if fsp_selection is not None
            else _select_fsp_examples(context, extraction, self.fsp_provider)
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
        default_rules=_rules_for_reasoning(extraction.reasoning),
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


def _rules_for_reasoning(reasoning: ReasoningMode) -> list[str]:
    del reasoning
    return [*EXTRACTION_RULES, STRICT_ANCHORING_RULE]


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
