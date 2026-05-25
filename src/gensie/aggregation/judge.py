from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from gensie.aggregation.judge_fsp import FixedJudgeFspProvider, JudgeFspProvider
from gensie.aggregation.judge_prompt import (
    SELF_CONSISTENCY_JUDGE_SYSTEM_PROMPT,
    build_self_consistency_judge_prompt,
)
from gensie.aggregation.judge_scope import (
    JudgeScope,
    build_judge_scope,
    merge_judge_output,
)
from gensie.config import env_bool, env_float, env_optional_float, env_optional_int
from gensie.pipeline.context import PipelineContext
from gensie.pipeline.records import AggregationResult, TrialRecord
from gensie.pipeline.specs import AggregationMode, ReasoningMode
from gensie.runtime import (
    ChatClient,
    ChatMessage,
    ChatRequest,
    build_json_schema_response_format,
    normalize_model_output_strings,
    request_payload,
    response_payload,
    trace_step,
    usage_payload,
)
from gensie.schemas import coerce_nullable_string_nulls
from gensie.schemas.reasoning import unwrap_reasoning_output


@dataclass(frozen=True)
class JudgeGenerationConfig:
    temperature: float = 0.0
    top_p: float | None = None
    max_tokens: int | None = None
    top_k: int | None = None

    @classmethod
    def from_env(cls) -> "JudgeGenerationConfig":
        return cls(
            temperature=env_float(
                "GENSIE_SC_JUDGE_TEMPERATURE", 0.0, minimum=0.0
            ),
            top_p=env_optional_float("GENSIE_SC_JUDGE_TOP_P"),
            max_tokens=env_optional_int("GENSIE_SC_JUDGE_MAX_TOKENS"),
            top_k=env_optional_int("GENSIE_SC_JUDGE_TOP_K"),
        )

    def request_options(self) -> tuple[float, dict[str, Any]]:
        options: dict[str, Any] = {}
        if self.top_p is not None:
            options["top_p"] = self.top_p
        if self.max_tokens is not None:
            options["max_tokens"] = self.max_tokens
        if self.top_k is not None:
            options["extra_body"] = {"top_k": self.top_k}
        return self.temperature, options


@dataclass
class JudgeAggregator:
    chat_client: ChatClient
    judge_model: str | None = None
    fsp_provider: JudgeFspProvider = field(default_factory=FixedJudgeFspProvider)
    generation_config: JudgeGenerationConfig = field(
        default_factory=JudgeGenerationConfig.from_env
    )
    include_scalar_reasonings: bool = field(
        default_factory=lambda: env_bool(
            "GENSIE_SC_JUDGE_INCLUDE_SCALAR_REASONINGS", False
        )
    )
    include_array_reasonings: bool = field(
        default_factory=lambda: env_bool(
            "GENSIE_SC_JUDGE_INCLUDE_ARRAY_REASONINGS", False
        )
    )
    include_stable_fields_in_prompt: bool = field(
        default_factory=lambda: env_bool(
            "GENSIE_SC_JUDGE_INCLUDE_STABLE_FIELDS", False
        )
    )
    include_support_counts: bool = field(
        default_factory=lambda: env_bool(
            "GENSIE_SC_JUDGE_INCLUDE_SUPPORT_COUNTS", True
        )
    )

    def aggregate(
        self, records: Sequence[TrialRecord], context: PipelineContext
    ) -> AggregationResult:
        valid_records = [record for record in records if record.result.is_valid]
        if not valid_records:
            return AggregationResult(
                output={"error": "No valid trial outputs to aggregate."},
                mode=AggregationMode.JUDGE,
                errors=("no_valid_trials",),
            )

        fallback_record = valid_records[0]
        fallback_output = _postprocess_output(
            normalize_model_output_strings(dict(fallback_record.result.output or {})),
            context,
        )
        if len(valid_records) == 1:
            return self._fallback_result(
                context,
                records,
                fallback_output,
                fallback_record.index,
                reason="single_valid_trial",
            )

        scope = build_judge_scope(valid_records, context.task.target_schema)
        if not scope.has_disputes:
            output = _postprocess_output(
                normalize_model_output_strings(merge_judge_output(scope, {})),
                context,
            )
            return self._fallback_result(
                context,
                records,
                output,
                fallback_record.index,
                reason="no_disputed_fields",
                scope=scope,
            )

        started_at = datetime.now(timezone.utc)
        started_perf = time.perf_counter()
        prompt = build_self_consistency_judge_prompt(
            context.task,
            valid_records,
            scope,
            fsp_provider=self.fsp_provider,
            include_scalar_reasonings=self.include_scalar_reasonings,
            include_array_reasonings=self.include_array_reasonings,
            include_stable_fields=self.include_stable_fields_in_prompt,
            include_support_counts=self.include_support_counts,
        )
        temperature, options = self.generation_config.request_options()
        request = ChatRequest(
            model=self.judge_model or context.model,
            messages=(
                ChatMessage(role="system", content=SELF_CONSISTENCY_JUDGE_SYSTEM_PROMPT),
                ChatMessage(role="user", content=prompt),
            ),
            response_format=build_json_schema_response_format(
                scope.reduced_schema,
                ReasoningMode.TOP_LEVEL,
                name="self_consistency_judge",
            ),
            temperature=temperature,
            options=options,
            metadata={
                "aggregation": "self_consistency_judge",
                "disputed_fields": list(scope.disputed_fields),
                "include_stable_fields_in_prompt": self.include_stable_fields_in_prompt,
                "include_support_counts": self.include_support_counts,
            },
        )

        response = None
        raw_output = None
        judge_output = None
        final_output = fallback_output
        error = None
        try:
            response = self.chat_client.complete(request)
            context.usage.add(response.usage)
            raw_output = normalize_model_output_strings(json.loads(response.content))
            judge_output = unwrap_reasoning_output(
                raw_output, scope.reduced_schema, ReasoningMode.TOP_LEVEL
            )
            final_output = _postprocess_output(
                normalize_model_output_strings(merge_judge_output(scope, judge_output)),
                context,
            )
        except Exception as exc:
            error = str(exc) or repr(exc)

        completed_at = datetime.now(timezone.utc)
        duration_ms = (time.perf_counter() - started_perf) * 1000
        result = AggregationResult(
            output=final_output,
            mode=AggregationMode.JUDGE,
            selected_trial_index=fallback_record.index if error else None,
            metadata={
                "judge_scope": _scope_metadata(scope, judge_called=True),
                "fallback_used": error is not None,
                "fallback_reason": "judge_failed" if error else None,
            },
        )
        trace_step(
            context.task,
            "self_consistency_judge",
            prompt_messages=request.messages,
            request_payload={
                **request_payload(request),
                "trial_indices": [record.index for record in valid_records],
                "stable_fields": list(scope.stable_fields),
                "disputed_fields": list(scope.disputed_fields),
                "include_stable_fields_in_prompt": self.include_stable_fields_in_prompt,
                "include_support_counts": self.include_support_counts,
            },
            response_payload={
                "trials": [_trial_record_payload(record) for record in records],
                "raw_judge_output": raw_output,
                "judge_output": judge_output,
                "fallback_used": error is not None,
                "fallback_reason": "judge_failed" if error else None,
                "final_output": final_output,
                "api_response": response_payload(response) if response else None,
            },
            error=error,
            metrics={
                "request": {"is_model_request": True, "role": "judge"},
                "tokens": usage_payload(response.usage if response is not None else None),
                "timings": {
                    "started_at": started_at.isoformat(),
                    "completed_at": completed_at.isoformat(),
                    "total_duration_ms": round(duration_ms, 3),
                    "time_to_first_token_ms": None,
                    "time_to_first_token_note": "Not captured by the current non-streaming pipeline.",
                },
            },
        )
        return result

    def _fallback_result(
        self,
        context: PipelineContext,
        records: Sequence[TrialRecord],
        output: Mapping[str, Any],
        selected_trial_index: int,
        *,
        reason: str,
        scope: JudgeScope | None = None,
    ) -> AggregationResult:
        started_at = datetime.now(timezone.utc)
        started_perf = time.perf_counter()
        completed_at = datetime.now(timezone.utc)
        duration_ms = (time.perf_counter() - started_perf) * 1000
        normalized_output = _postprocess_output(
            normalize_model_output_strings(dict(output)),
            context,
        )
        result = AggregationResult(
            output=normalized_output,
            mode=AggregationMode.JUDGE,
            selected_trial_index=selected_trial_index,
            metadata={
                "judge_scope": _scope_metadata(scope, judge_called=False),
                "fallback_used": True,
                "fallback_reason": reason,
            },
        )
        trace_step(
            context.task,
            "self_consistency_judge_fallback",
            request_payload={
                "trial_indices": [record.index for record in records],
                "fallback_reason": reason,
            },
            response_payload={
                "trials": [_trial_record_payload(record) for record in records],
                "fallback_reason": reason,
                "final_output": normalized_output,
            },
            metrics={
                "request": {
                    "is_model_request": False,
                    "role": f"{reason}_fallback",
                },
                "tokens": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
                "timings": {
                    "started_at": started_at.isoformat(),
                    "completed_at": completed_at.isoformat(),
                    "total_duration_ms": round(duration_ms, 3),
                    "time_to_first_token_note": "Fallback step; no model stream.",
                },
            },
        )
        return result


def _scope_metadata(scope: JudgeScope | None, *, judge_called: bool) -> dict[str, Any]:
    if scope is None:
        return {
            "stable_fields": [],
            "disputed_fields": [],
            "judge_called": judge_called,
        }
    return {
        "stable_fields": list(scope.stable_fields),
        "disputed_fields": list(scope.disputed_fields),
        "stable_sources": scope.stable_sources,
        "judge_called": judge_called,
    }


def _trial_record_payload(record: TrialRecord) -> Mapping[str, Any]:
    return {
        "trial_index": record.index,
        "group_name": record.group_name,
        "extraction": record.extraction.name,
        "final_candidate": record.result.output,
        "structured_output": record.result.raw_output,
        "reasoning_view": record.result.reasoning,
        "errors": list(record.result.errors),
        "metadata": dict(record.metadata),
    }


def _postprocess_output(
    output: Mapping[str, Any], context: PipelineContext
) -> dict[str, Any]:
    return coerce_nullable_string_nulls(dict(output), context.task.target_schema)
