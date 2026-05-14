from __future__ import annotations

from gensie.fsp import FSPProvider, NoFSPProvider, fixed_reasoning_provider, super_static_provider
from gensie.pipeline.registry import PipelineRegistry
from gensie.pipeline.specs import (
    ExtractionSpec,
    FewShotMode,
    PipelineSpec,
    ReasoningMode,
    SchemaPromptMode,
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
