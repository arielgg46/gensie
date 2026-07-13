from __future__ import annotations

from gensie.fsp import (
    FSPProvider,
    NoFSPProvider,
    RagExtractionFspProvider,
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
from gensie.fsp.rag import (
    RAG_SELECTION_DEFAULT,
    RAG_SELECTION_FIELD_TOP2_INDEPENDENT,
    RAG_SELECTION_MODE_OPTION,
    RAG_SELECTION_SAME_SCHEMA_FIRST,
    RAG_SELECTION_SAME_SCHEMA_SECOND,
    RAG_SKIP_MODE_OPTION,
    RAG_SKIP_NON_SAME_SCHEMA,
    RAG_SKIP_SAME_SCHEMA,
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
            name="enriched-inline-reasoning-rag",
            description="Top-level reasoning/value wrappers with a reasoned Pydantic schema prompt and retrieved structured FSP.",
            extraction=ExtractionSpec(
                name="enriched-inline-reasoning-rag",
                reasoning=ReasoningMode.TOP_LEVEL,
                schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
                few_shot=FewShotMode.RAG,
            ),
        ),
        PipelineSpec(
            name="selective-inline-reasoning-rag",
            description=(
                "RAG extraction with reasoned Pydantic prompt, but direct "
                "top-level outputs for entity arrays, enum classifications, "
                "and complex object arrays."
            ),
            extraction=ExtractionSpec(
                name="selective-inline-reasoning-rag",
                reasoning=ReasoningMode.SELECTIVE_TOP_LEVEL,
                schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
                few_shot=FewShotMode.RAG,
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
            name="enriched-schema-rag",
            description="Spanish enriched extraction prompt with a plain Pydantic schema and two retrieved structured FSP examples.",
            extraction=ExtractionSpec(
                name="enriched-schema-rag",
                reasoning=ReasoningMode.NONE,
                schema_prompt=SchemaPromptMode.PYDANTIC,
                few_shot=FewShotMode.RAG,
            ),
        ),
        *_component_ablation_pipeline_specs(),
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
            name="mixed-extractors-self-consistency-rag",
            description=(
                "Four-trial RAG self-consistency alternating enriched inline "
                "reasoning RAG and enriched schema RAG extractors."
            ),
            extraction=ExtractionSpec(
                name="enriched-inline-reasoning-rag",
                reasoning=ReasoningMode.TOP_LEVEL,
                schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
                few_shot=FewShotMode.RAG,
            ),
            sampling=SamplingSpec(
                total_trials=4,
                interleave=True,
                groups=(
                    TrialGroupSpec(
                        name="enriched-inline-reasoning-rag",
                        extraction=ExtractionSpec(
                            name="enriched-inline-reasoning-rag",
                            reasoning=ReasoningMode.TOP_LEVEL,
                            schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
                            few_shot=FewShotMode.RAG,
                        ),
                        count=2,
                    ),
                    TrialGroupSpec(
                        name="enriched-schema-rag",
                        extraction=ExtractionSpec(
                            name="enriched-schema-rag",
                            reasoning=ReasoningMode.NONE,
                            schema_prompt=SchemaPromptMode.PYDANTIC,
                            few_shot=FewShotMode.RAG,
                        ),
                        count=2,
                    ),
                ),
            ),
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
        PipelineSpec(
            name="mixed-extractors-self-consistency-verdict-judge-rag",
            description=(
                "Heterogeneous self-consistency using baseline, enriched schema, "
                "and enriched inline extraction trials with a RAG-backed "
                "candidate-verdict SLM judge."
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
                options={"variant": "candidate_verdicts", "judge_fsp": "rag"},
            ),
        ),
        PipelineSpec(
            name="mixed-extractors-self-consistency-verdict-judge-rag-slots",
            description=(
                "Heterogeneous self-consistency using baseline, enriched schema, "
                "and enriched inline extraction trials with a RAG-backed "
                "candidate-verdict SLM judge whose candidate slots are fixed."
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
                options={
                    "variant": "candidate_verdicts",
                    "judge_fsp": "rag",
                    "candidate_layout": "slots",
                },
            ),
        ),
    )


def _component_ablation_pipeline_specs() -> tuple[PipelineSpec, ...]:
    bases = (
        (
            "enriched-schema-rag",
            ReasoningMode.NONE,
            SchemaPromptMode.PYDANTIC,
            "plain Pydantic schema prompt",
        ),
        (
            "enriched-inline-reasoning-rag",
            ReasoningMode.TOP_LEVEL,
            SchemaPromptMode.REASONED_PYDANTIC,
            "reasoned Pydantic schema prompt",
        ),
    )
    specs: list[PipelineSpec] = []
    for base_name, reasoning, schema_prompt, prompt_description in bases:
        specs.extend(
            (
                PipelineSpec(
                    name=f"{base_name}-zero-shot",
                    description=(
                        f"Component ablation of {base_name}: {prompt_description} "
                        "without FSP examples."
                    ),
                    extraction=ExtractionSpec(
                        name=f"{base_name}-zero-shot",
                        reasoning=reasoning,
                        schema_prompt=schema_prompt,
                        few_shot=FewShotMode.NONE,
                    ),
                    metadata={"component_analysis": "rag_zero_shot"},
                ),
                PipelineSpec(
                    name=f"{base_name}-rag-field-top2-independent-non-same-schema",
                    description=(
                        f"Component ablation of {base_name}: skip same-schema "
                        "tasks and use the two highest independent field-RAG "
                        "scores for non-same-schema tasks."
                    ),
                    extraction=ExtractionSpec(
                        name=(
                            f"{base_name}-rag-field-top2-independent-non-same-schema"
                        ),
                        reasoning=reasoning,
                        schema_prompt=schema_prompt,
                        few_shot=FewShotMode.RAG,
                        options={
                            RAG_SELECTION_MODE_OPTION: (
                                RAG_SELECTION_FIELD_TOP2_INDEPENDENT
                            ),
                            RAG_SKIP_MODE_OPTION: RAG_SKIP_SAME_SCHEMA,
                        },
                    ),
                    metadata={"component_analysis": "rag_field_top2_independent"},
                ),
                PipelineSpec(
                    name=f"{base_name}-rag-same-schema-first",
                    description=(
                        f"Component ablation of {base_name}: skip non-same-schema "
                        "tasks and use only the first same-schema corpus example."
                    ),
                    extraction=ExtractionSpec(
                        name=f"{base_name}-rag-same-schema-first",
                        reasoning=reasoning,
                        schema_prompt=schema_prompt,
                        few_shot=FewShotMode.RAG,
                        options={
                            RAG_SELECTION_MODE_OPTION: RAG_SELECTION_SAME_SCHEMA_FIRST,
                            RAG_SKIP_MODE_OPTION: RAG_SKIP_NON_SAME_SCHEMA,
                        },
                    ),
                    metadata={"component_analysis": "rag_same_schema_first"},
                ),
                PipelineSpec(
                    name=f"{base_name}-rag-same-schema-second",
                    description=(
                        f"Component ablation of {base_name}: skip non-same-schema "
                        "tasks and use only the second same-schema corpus example."
                    ),
                    extraction=ExtractionSpec(
                        name=f"{base_name}-rag-same-schema-second",
                        reasoning=reasoning,
                        schema_prompt=schema_prompt,
                        few_shot=FewShotMode.RAG,
                        options={
                            RAG_SELECTION_MODE_OPTION: RAG_SELECTION_SAME_SCHEMA_SECOND,
                            RAG_SKIP_MODE_OPTION: RAG_SKIP_NON_SAME_SCHEMA,
                        },
                    ),
                    metadata={"component_analysis": "rag_same_schema_second"},
                ),
                PipelineSpec(
                    name=f"{base_name}-free-json",
                    description=(
                        f"Constrained-decoding ablation of {base_name}: free text "
                        "generation followed by extraction of the first complete "
                        "valid JSON value in the response."
                    ),
                    extraction=ExtractionSpec(
                        name=f"{base_name}-free-json",
                        reasoning=reasoning,
                        schema_prompt=schema_prompt,
                        few_shot=FewShotMode.RAG,
                        options={"constrained_decoding": False},
                    ),
                    metadata={"component_analysis": "free_json_decoding"},
                ),
            )
        )
    return tuple(specs)


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
    if few_shot is FewShotMode.RAG:
        return RagExtractionFspProvider(
            top_k=2,
            selection_mode=str(
                spec.extraction.options.get(
                    RAG_SELECTION_MODE_OPTION, RAG_SELECTION_DEFAULT
                )
            ),
        )
    return NoFSPProvider()
