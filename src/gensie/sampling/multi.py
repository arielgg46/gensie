from __future__ import annotations

import dataclasses
import time
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from gensie.aggregation import (
    HeuristicSelfConsistencyAggregator,
    JudgeAggregator,
    PassthroughAggregator,
    VerdictJudgeAggregator,
)
from gensie.aggregation.base import Aggregator
from gensie.aggregation.verdict_fsp import RagVerdictJudgeFspProvider
from gensie.pipeline.context import PipelineContext
from gensie.pipeline.records import AggregationResult, TrialRecord
from gensie.pipeline.specs import (
    AggregationMode,
    PipelineSpec,
    SamplingSpec,
)
from gensie.runtime import ChatClient, messages_payload
from gensie.runtime.response_format import build_json_schema_response_format
from gensie.sampling.budget import (
    TrialBudgetEstimate,
    TrialBudgetPlanner,
    build_trial_budget_config_from_env,
)
from gensie.sampling.plans import resolve_trial_plan
from gensie.sampling.single import SingleExtractionRunner


@dataclass
class PipelineExecutionRunner:
    chat_client: ChatClient
    single_runner: SingleExtractionRunner = field(init=False)
    trial_planner: TrialBudgetPlanner = field(init=False)

    def __post_init__(self) -> None:
        self.single_runner = SingleExtractionRunner(chat_client=self.chat_client)
        self.trial_planner = TrialBudgetPlanner(build_trial_budget_config_from_env())

    def run(
        self, spec: PipelineSpec, context: PipelineContext
    ) -> Mapping[str, Any] | AggregationResult:
        if not spec.requires_aggregation:
            return self.single_runner.run(spec, context)

        records = self.run_trials(spec, context)
        aggregator = self._aggregator_for(spec)
        return aggregator.aggregate(records, context)

    def run_trials(
        self, spec: PipelineSpec, context: PipelineContext
    ) -> tuple[TrialRecord, ...]:
        sampling, initial_estimate, prompt_token_fallback = self._sampling_for_budget(
            spec, context
        )
        plan = resolve_trial_plan(sampling, default_extraction=spec.extraction)
        allowed_trials = initial_estimate.allowed_trials
        budget_estimates: list[dict[str, Any]] = [dataclasses.asdict(initial_estimate)]
        prompt_token_samples: list[int] = []
        completion_token_samples: list[int] = []
        trial_duration_samples_s: list[float] = []
        records: list[TrialRecord] = []

        for item in plan:
            if item.index >= allowed_trials:
                break

            generation_options = {
                **_generation_options_for_trial(item.index),
                **dict(item.options or {}),
            }
            started = time.perf_counter()
            result = self.single_runner.run_extraction(
                spec,
                context,
                extraction_override=item.extraction,
                step_name=f"self_consistency_trial_{item.index + 1:02d}",
                generation_options=generation_options,
            )
            duration_s = time.perf_counter() - started
            trial_duration_samples_s.append(duration_s)

            response_usage = (
                (result.metadata.get("response") or {}).get("usage")
                if isinstance(result.metadata, dict)
                else None
            )
            if isinstance(response_usage, dict):
                prompt_tokens = response_usage.get("prompt_tokens")
                completion_tokens = response_usage.get("completion_tokens")
                if isinstance(prompt_tokens, int):
                    prompt_token_samples.append(prompt_tokens)
                if isinstance(completion_tokens, int):
                    completion_token_samples.append(completion_tokens)

            current_estimate = self.trial_planner.estimate(
                prompt_tokens=max(prompt_token_samples) if prompt_token_samples else None,
                prompt_token_fallback=prompt_token_fallback,
                completion_token_samples=completion_token_samples,
                trial_duration_samples_s=trial_duration_samples_s,
            )
            allowed_trials = current_estimate.allowed_trials
            budget_estimates.append(dataclasses.asdict(current_estimate))
            records.append(
                TrialRecord(
                    index=item.index,
                    group_name=item.group_name,
                    extraction=item.extraction,
                    result=result,
                    metadata={
                        "group_index": item.group_index,
                        "group_trial_index": item.group_trial_index,
                        "generation_options": generation_options,
                        "budget_estimate_after_trial": dataclasses.asdict(
                            current_estimate
                        ),
                    },
                )
            )

        context.metadata["self_consistency"] = {
            "initial_budget_estimate": dataclasses.asdict(initial_estimate),
            "budget_estimates": budget_estimates,
            "trial_count": len(records),
            "allowed_trials": allowed_trials,
        }
        return tuple(records)

    def _sampling_for_budget(
        self, spec: PipelineSpec, context: PipelineContext
    ) -> tuple[SamplingSpec, TrialBudgetEstimate, int]:
        prompt = self.single_runner.prompt_builder.build(context, spec.extraction)
        response_format = build_json_schema_response_format(
            context.task.target_schema, spec.extraction.reasoning
        )
        prompt_token_fallback = self.trial_planner.estimate_prompt_tokens(
            messages=messages_payload(prompt.messages()),
            response_format=response_format,
        )
        estimate = self.trial_planner.estimate(
            prompt_tokens=None,
            prompt_token_fallback=prompt_token_fallback,
            completion_token_samples=[],
            trial_duration_samples_s=[],
        )
        minimum_trials = _minimum_trials_for_sampling(spec.sampling)
        total_trials = min(spec.sampling.total_trials, estimate.allowed_trials)
        total_trials = max(minimum_trials, total_trials, 1)
        return (
            SamplingSpec(
                total_trials=total_trials,
                groups=spec.sampling.groups,
                interleave=spec.sampling.interleave,
                options=spec.sampling.options,
            ),
            estimate,
            prompt_token_fallback,
        )

    def _aggregator_for(self, spec: PipelineSpec) -> Aggregator:
        if spec.aggregation.mode is AggregationMode.HEURISTIC_SELF_CONSISTENCY:
            return HeuristicSelfConsistencyAggregator()
        if spec.aggregation.mode is AggregationMode.JUDGE:
            if spec.aggregation.options.get("variant") == "candidate_verdicts":
                candidate_layout = str(
                    spec.aggregation.options.get("candidate_layout") or "array"
                )
                if spec.aggregation.options.get("judge_fsp") == "rag":
                    return VerdictJudgeAggregator(
                        self.chat_client,
                        judge_model=spec.aggregation.judge_model,
                        fsp_provider=RagVerdictJudgeFspProvider(),
                        candidate_layout=candidate_layout,
                    )
                return VerdictJudgeAggregator(
                    self.chat_client,
                    judge_model=spec.aggregation.judge_model,
                    candidate_layout=candidate_layout,
                )
            return JudgeAggregator(
                self.chat_client,
                judge_model=spec.aggregation.judge_model,
            )
        return PassthroughAggregator()


def _generation_options_for_trial(trial_index: int) -> dict[str, Any]:
    from gensie.config import env_float, env_optional_float, env_optional_int

    temperature = env_float("GENSIE_SC_TEMPERATURE", 0.5, minimum=0.0)
    first_temperature = env_optional_float("GENSIE_SC_FIRST_TEMPERATURE")
    if trial_index == 0 and first_temperature is not None:
        temperature = max(first_temperature, 0.0)

    options: dict[str, Any] = {"temperature": temperature}
    top_p = env_optional_float("GENSIE_SC_TOP_P")
    if top_p is not None:
        options["top_p"] = top_p
    max_tokens = env_optional_int("GENSIE_SC_MAX_TOKENS")
    if max_tokens is not None:
        options["max_tokens"] = max_tokens
    top_k = env_optional_int("GENSIE_SC_TOP_K")
    if top_k is not None:
        options["top_k"] = top_k
    return options


def _minimum_trials_for_sampling(sampling: SamplingSpec) -> int:
    if not sampling.groups:
        return 1
    total = 0
    for group in sampling.groups:
        if group.count is not None:
            total += group.count
        else:
            total += group.min_count
    return max(1, total)
