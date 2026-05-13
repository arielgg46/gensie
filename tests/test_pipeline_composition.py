import pytest

from gensie.aggregation import PassthroughAggregator
from gensie.pipeline import (
    AggregationMode,
    AggregationResult,
    ComposablePipelineAgent,
    ExtractionResult,
    ExtractionSpec,
    PipelineContext,
    PipelineRegistry,
    PipelineSpec,
    ReasoningMode,
    SamplingSpec,
    SchemaPromptMode,
    TrialGroupSpec,
    TrialRecord,
)
from gensie.sampling import resolve_group_counts, resolve_trial_plan
from gensie.task import Task
from gensie.usage import UsageTracker


def _task() -> Task:
    return Task(
        id="unit",
        input_text="text",
        instruction="extract",
        target_schema={"type": "object", "properties": {}},
    )


def test_reasoned_pydantic_requires_inline_reasoning():
    with pytest.raises(ValueError, match="requires inline reasoning"):
        ExtractionSpec(schema_prompt=SchemaPromptMode.REASONED_PYDANTIC)


def test_mixed_trial_groups_resolve_counts_and_interleaved_plan():
    baseline = ExtractionSpec(name="baseline")
    enriched = ExtractionSpec(
        name="enriched-deep",
        reasoning=ReasoningMode.DEEP,
        schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
    )
    sampling = SamplingSpec(
        total_trials=10,
        groups=(
            TrialGroupSpec(name="baseline", extraction=baseline, ratio=0.4),
            TrialGroupSpec(name="enriched", extraction=enriched, ratio=0.6),
        ),
    )

    assert resolve_group_counts(sampling) == (4, 6)

    plan = resolve_trial_plan(sampling, default_extraction=baseline)
    assert len(plan) == 10
    assert [item.group_name for item in plan[:4]] == [
        "baseline",
        "enriched",
        "baseline",
        "enriched",
    ]
    assert sum(item.group_name == "baseline" for item in plan) == 4
    assert sum(item.group_name == "enriched" for item in plan) == 6


def test_trial_groups_can_mix_fixed_counts_and_ratios():
    baseline = ExtractionSpec(name="baseline")
    enriched = ExtractionSpec(name="enriched", reasoning=ReasoningMode.TOP_LEVEL)
    sampling = SamplingSpec(
        total_trials=5,
        groups=(
            TrialGroupSpec(name="baseline", extraction=baseline, count=1),
            TrialGroupSpec(name="enriched", extraction=enriched, ratio=1.0),
        ),
        interleave=False,
    )

    assert resolve_group_counts(sampling) == (1, 4)
    assert [item.group_name for item in resolve_trial_plan(sampling, baseline)] == [
        "baseline",
        "enriched",
        "enriched",
        "enriched",
        "enriched",
    ]


def test_registry_exports_pipeline_info_in_registration_order():
    registry = PipelineRegistry()
    registry.register(PipelineSpec(name="a", description="first pipeline"))
    registry.register(PipelineSpec(name="b", description="second pipeline"))

    assert registry.names() == ("a", "b")
    assert [info.name for info in registry.pipeline_infos()] == ["a", "b"]
    assert registry.get("b").description == "second pipeline"


def test_passthrough_aggregator_selects_first_valid_trial():
    context = PipelineContext(task=_task(), model="model", usage=UsageTracker())
    extraction = ExtractionSpec(name="baseline")
    records = [
        TrialRecord(
            index=0,
            group_name="baseline",
            extraction=extraction,
            result=ExtractionResult(output={"error": "bad"}),
        ),
        TrialRecord(
            index=1,
            group_name="enriched",
            extraction=ExtractionSpec(name="enriched"),
            result=ExtractionResult(output={"answer": "ok"}),
        ),
    ]

    result = PassthroughAggregator().aggregate(records, context)

    assert result.is_valid
    assert result.output == {"answer": "ok"}
    assert result.selected_trial_index == 1
    assert result.mode is AggregationMode.PASSTHROUGH


def test_composable_agent_resets_usage_and_delegates():
    class FakeRunner:
        def run(self, spec, context):
            context.usage.add({"prompt_tokens": 3, "completion_tokens": 4})
            return AggregationResult(
                output={"pipeline": spec.name, "model": context.model},
                mode=AggregationMode.PASSTHROUGH,
            )

    agent = ComposablePipelineAgent(
        PipelineSpec(name="composed", description="composed pipeline"),
        runner=FakeRunner(),
    )
    agent.usage.add({"prompt_tokens": 100, "completion_tokens": 100})

    output = agent.run(_task(), model="demo-model")

    assert output == {"pipeline": "composed", "model": "demo-model"}
    assert agent.usage.snapshot() == {
        "input_tokens": 3,
        "output_tokens": 4,
        "total_tokens": 7,
        "calls": 1,
    }
