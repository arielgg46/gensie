from __future__ import annotations

from gensie.fsp import (
    FSPProvider,
    NoFSPProvider,
    fixed_reasoning_provider,
    super_static_provider,
)
from gensie.pipeline.registry import PipelineRegistry
from gensie.pipeline.specs import (
    AggregationMode,
    AggregationSpec,
    ExtractionSpec,
    FewShotMode,
    PhaseKind,
    PipelineSpec,
    ReasoningMode,
    SamplingSpec,
    SchemaPromptMode,
    TrialGroupSpec,
)


def default_pipeline_specs() -> tuple[PipelineSpec, ...]:
    return (
        PipelineSpec(
            name="baseline",
            description="Standard structured-output extraction using the task JSON schema.",
            extraction=ExtractionSpec(
                name="baseline",
                reasoning=ReasoningMode.NONE,
                schema_prompt=SchemaPromptMode.JSON_SCHEMA,
            ),
        ),
        PipelineSpec(
            name="inline-reasoning",
            description="Top-level reasoning/value wrappers with the reference Spanish inline prompt and fixed Don Quijote FSP.",
            extraction=ExtractionSpec(
                name="inline-reasoning",
                reasoning=ReasoningMode.TOP_LEVEL,
                schema_prompt=SchemaPromptMode.INLINE_REASONING_WRAPPER,
                few_shot=FewShotMode.FIXED,
            ),
        ),
        PipelineSpec(
            name="enriched-inline-reasoning",
            description="Top-level reasoning/value wrappers with a reasoned Pydantic schema prompt and fixed FSP.",
            extraction=ExtractionSpec(
                name="enriched-inline-reasoning",
                reasoning=ReasoningMode.TOP_LEVEL,
                schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
                few_shot=FewShotMode.FIXED,
            ),
        ),
        PipelineSpec(
            name="enriched-schema",
            description="Spanish enriched extraction prompt with a plain Pydantic schema, no FSP, and no inline reasoning.",
            extraction=ExtractionSpec(
                name="enriched-schema",
                reasoning=ReasoningMode.NONE,
                schema_prompt=SchemaPromptMode.PYDANTIC,
                few_shot=FewShotMode.NONE,
            ),
        ),
        PipelineSpec(
            name="verbatim-entities-enriched-inline-reasoning",
            description="Two-call enriched inline reasoning: extract verbatim entities first, then inject the flat entity list into the extraction prompt.",
            extraction=ExtractionSpec(
                name="verbatim-entities-enriched-inline-reasoning",
                reasoning=ReasoningMode.TOP_LEVEL,
                schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
                few_shot=FewShotMode.FIXED,
                phases=(PhaseKind.VERBATIM_ENTITIES,),
            ),
        ),
        PipelineSpec(
            name="enriched-inline-reasoning-deep",
            description="Recursive reasoning/value wrappers with a deep reasoned Pydantic schema prompt and fixed FSP.",
            extraction=ExtractionSpec(
                name="enriched-inline-reasoning-deep",
                reasoning=ReasoningMode.DEEP,
                schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
                few_shot=FewShotMode.FIXED,
            ),
        ),
        PipelineSpec(
            name="enriched-inline-reasoning-super-fsp",
            description="Top-level reasoning/value wrappers with reasoned Pydantic schema and static super FSP.",
            extraction=ExtractionSpec(
                name="enriched-inline-reasoning-super-fsp",
                reasoning=ReasoningMode.TOP_LEVEL,
                schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
                few_shot=FewShotMode.SUPER_STATIC,
            ),
        ),
        PipelineSpec(
            name="enriched-inline-reasoning-self-consistency",
            description="Multi-trial enriched inline reasoning with schema-aware heuristic self-consistency aggregation.",
            extraction=ExtractionSpec(
                name="enriched-inline-reasoning",
                reasoning=ReasoningMode.TOP_LEVEL,
                schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
                few_shot=FewShotMode.FIXED,
            ),
            sampling=SamplingSpec(total_trials=12),
            aggregation=AggregationSpec(
                mode=AggregationMode.HEURISTIC_SELF_CONSISTENCY
            ),
        ),
        PipelineSpec(
            name="enriched-inline-reasoning-super-fsp-self-consistency",
            description="Multi-trial enriched inline reasoning with static super FSP and schema-aware heuristic aggregation.",
            extraction=ExtractionSpec(
                name="enriched-inline-reasoning-super-fsp",
                reasoning=ReasoningMode.TOP_LEVEL,
                schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
                few_shot=FewShotMode.SUPER_STATIC,
            ),
            sampling=SamplingSpec(total_trials=12),
            aggregation=AggregationSpec(
                mode=AggregationMode.HEURISTIC_SELF_CONSISTENCY
            ),
        ),
        PipelineSpec(
            name="enriched-inline-reasoning-self-consistency-judge",
            description="Multi-trial enriched inline reasoning with a scoped structured SLM judge over disputed fields.",
            extraction=ExtractionSpec(
                name="enriched-inline-reasoning",
                reasoning=ReasoningMode.TOP_LEVEL,
                schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
                few_shot=FewShotMode.FIXED,
            ),
            sampling=SamplingSpec(total_trials=12),
            aggregation=AggregationSpec(mode=AggregationMode.JUDGE),
        ),
        PipelineSpec(
            name="enriched-inline-reasoning-self-consistency-verdict-judge",
            description="Multi-trial enriched inline reasoning with a candidate-verdict SLM judge over disputed fields.",
            extraction=ExtractionSpec(
                name="enriched-inline-reasoning",
                reasoning=ReasoningMode.TOP_LEVEL,
                schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
                few_shot=FewShotMode.FIXED,
            ),
            sampling=SamplingSpec(total_trials=12),
            aggregation=AggregationSpec(
                mode=AggregationMode.JUDGE,
                options={"variant": "candidate_verdicts"},
            ),
        ),
        PipelineSpec(
            name="mixed-extractors-self-consistency-judge",
            description=(
                "Heterogeneous self-consistency using baseline, enriched schema, "
                "and enriched inline extraction trials with a scoped SLM judge."
            ),
            extraction=ExtractionSpec(
                name="baseline",
                reasoning=ReasoningMode.NONE,
                schema_prompt=SchemaPromptMode.JSON_SCHEMA,
            ),
            sampling=SamplingSpec(
                total_trials=6,
                interleave=True,
                groups=(
                    TrialGroupSpec(
                        name="baseline",
                        extraction=ExtractionSpec(
                            name="baseline",
                            reasoning=ReasoningMode.NONE,
                            schema_prompt=SchemaPromptMode.JSON_SCHEMA,
                        ),
                        ratio=1.0,
                        min_count=1,
                    ),
                    TrialGroupSpec(
                        name="enriched-schema",
                        extraction=ExtractionSpec(
                            name="enriched-schema",
                            reasoning=ReasoningMode.NONE,
                            schema_prompt=SchemaPromptMode.PYDANTIC,
                            few_shot=FewShotMode.NONE,
                        ),
                        ratio=1.0,
                        min_count=1,
                    ),
                    TrialGroupSpec(
                        name="enriched-inline-reasoning",
                        extraction=ExtractionSpec(
                            name="enriched-inline-reasoning",
                            reasoning=ReasoningMode.TOP_LEVEL,
                            schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
                            few_shot=FewShotMode.FIXED,
                        ),
                        ratio=1.0,
                        min_count=1,
                    ),
                ),
            ),
            aggregation=AggregationSpec(mode=AggregationMode.JUDGE),
        ),
        PipelineSpec(
            name="mixed-extractors-self-consistency-verdict-judge",
            description=(
                "Heterogeneous self-consistency using baseline, enriched schema, "
                "and enriched inline extraction trials with a candidate-verdict SLM judge."
            ),
            extraction=ExtractionSpec(
                name="baseline",
                reasoning=ReasoningMode.NONE,
                schema_prompt=SchemaPromptMode.JSON_SCHEMA,
            ),
            sampling=SamplingSpec(
                total_trials=6,
                interleave=True,
                groups=(
                    TrialGroupSpec(
                        name="baseline",
                        extraction=ExtractionSpec(
                            name="baseline",
                            reasoning=ReasoningMode.NONE,
                            schema_prompt=SchemaPromptMode.JSON_SCHEMA,
                        ),
                        ratio=1.0,
                        min_count=1,
                    ),
                    TrialGroupSpec(
                        name="enriched-schema",
                        extraction=ExtractionSpec(
                            name="enriched-schema",
                            reasoning=ReasoningMode.NONE,
                            schema_prompt=SchemaPromptMode.PYDANTIC,
                            few_shot=FewShotMode.NONE,
                        ),
                        ratio=1.0,
                        min_count=1,
                    ),
                    TrialGroupSpec(
                        name="enriched-inline-reasoning",
                        extraction=ExtractionSpec(
                            name="enriched-inline-reasoning",
                            reasoning=ReasoningMode.TOP_LEVEL,
                            schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
                            few_shot=FewShotMode.FIXED,
                        ),
                        ratio=1.0,
                        min_count=1,
                    ),
                ),
            ),
            aggregation=AggregationSpec(
                mode=AggregationMode.JUDGE,
                options={"variant": "candidate_verdicts"},
            ),
        ),
    )


def build_default_registry() -> PipelineRegistry:
    registry = PipelineRegistry()
    for spec in default_pipeline_specs():
        registry.register(spec)
    return registry


def default_fsp_provider_for(spec: PipelineSpec) -> FSPProvider:
    few_shot = spec.extraction.few_shot
    if few_shot is FewShotMode.FIXED:
        return fixed_reasoning_provider(spec.extraction.reasoning)
    if few_shot is FewShotMode.SUPER_STATIC:
        return super_static_provider()
    return NoFSPProvider()
