from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from gensie.aggregation.judge import (
    JudgeGenerationConfig,
    _scope_metadata,
    _trial_record_payload,
)
from gensie.aggregation.judge_scope import JudgeScope, build_judge_scope, merge_judge_output
from gensie.aggregation.verdict_fsp import (
    FixedVerdictJudgeFspProvider,
    VerdictJudgeFspProvider,
)
from gensie.aggregation.verdict_prompt import (
    VERDICT_JUDGE_SYSTEM_PROMPT,
    build_verdict_judge_prompt,
)
from gensie.aggregation.verdict_schema import (
    VERDICT_EVIDENCE_MAX_LENGTH_SCHEMA_ENV,
    VerdictCandidateLayout,
    VerdictValidationError,
    build_verdict_plan,
    build_verdict_response_format,
    normalize_candidate_layout,
    reconstruct_verdict_output_with_report,
)
from gensie.config import env_bool
from gensie.pipeline.context import PipelineContext
from gensie.pipeline.records import AggregationResult, TrialRecord
from gensie.pipeline.specs import AggregationMode
from gensie.runtime import (
    ChatClient,
    ChatMessage,
    ChatRequest,
    normalize_model_output_strings,
    request_payload,
    response_payload,
    trace_step,
    usage_payload,
)


@dataclass
class VerdictJudgeAggregator:
    chat_client: ChatClient
    judge_model: str | None = None
    fsp_provider: VerdictJudgeFspProvider = field(
        default_factory=FixedVerdictJudgeFspProvider
    )
    generation_config: JudgeGenerationConfig = field(
        default_factory=JudgeGenerationConfig.from_env
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
    enforce_validation: bool = field(
        default_factory=lambda: env_bool(
            "GENSIE_SC_VERDICT_JUDGE_ENFORCE_VALIDATION", False
        )
    )
    report_validation: bool = field(
        default_factory=lambda: env_bool(
            "GENSIE_SC_VERDICT_JUDGE_REPORT_VALIDATION", True
        )
    )
    candidate_layout: VerdictCandidateLayout = "array"

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
        fallback_output = normalize_model_output_strings(
            dict(fallback_record.result.output or {})
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
            output = normalize_model_output_strings(merge_judge_output(scope, {}))
            return self._fallback_result(
                context,
                records,
                output,
                fallback_record.index,
                reason="no_disputed_fields",
                scope=scope,
            )

        plan = build_verdict_plan(context.task, valid_records, scope)
        candidate_layout = normalize_candidate_layout(self.candidate_layout)
        started_at = datetime.now(timezone.utc)
        started_perf = time.perf_counter()
        prompt = build_verdict_judge_prompt(
            context.task,
            scope,
            plan,
            fsp_provider=self.fsp_provider,
            include_stable_fields=self.include_stable_fields_in_prompt,
            include_support_counts=self.include_support_counts,
            candidate_layout=candidate_layout,
        )
        temperature, options = self.generation_config.request_options()
        include_evidence_max_length = env_bool(
            VERDICT_EVIDENCE_MAX_LENGTH_SCHEMA_ENV, False
        )
        request = ChatRequest(
            model=self.judge_model or context.model,
            messages=(
                ChatMessage(role="system", content=VERDICT_JUDGE_SYSTEM_PROMPT),
                ChatMessage(role="user", content=prompt),
            ),
            response_format=build_verdict_response_format(
                context.task,
                plan,
                include_evidence_max_length=include_evidence_max_length,
                candidate_layout=candidate_layout,
            ),
            temperature=temperature,
            options=options,
            metadata={
                "aggregation": "self_consistency_verdict_judge",
                "variant": "candidate_verdicts",
                "disputed_fields": list(scope.disputed_fields),
                "include_stable_fields_in_prompt": self.include_stable_fields_in_prompt,
                "include_support_counts": self.include_support_counts,
                "enforce_validation": self.enforce_validation,
                "report_validation": self.report_validation,
                "judge_fsp_provider": self.fsp_provider.__class__.__name__,
                "include_evidence_max_length": include_evidence_max_length,
                "candidate_layout": candidate_layout,
            },
        )

        response = None
        raw_output = None
        final_output = fallback_output
        error = None
        validation_issues = ()
        try:
            response = self.chat_client.complete(request)
            context.usage.add(response.usage)
            raw_output = normalize_model_output_strings(json.loads(response.content))
            reconstruction = reconstruct_verdict_output_with_report(
                plan,
                scope,
                raw_output,
                enforce_validation=self.enforce_validation,
                report_validation=self.report_validation,
                fallback_output=fallback_output,
                candidate_layout=candidate_layout,
            )
            final_output = normalize_model_output_strings(reconstruction.output)
            validation_issues = reconstruction.validation_issues
        except VerdictValidationError as exc:
            error = str(exc) or repr(exc)
            validation_issues = exc.issues
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
                "variant": "candidate_verdicts",
                "validation_enforced": self.enforce_validation,
                "validation_reported": self.report_validation,
                "validation_issue_count": len(validation_issues),
                "validation_issues": list(validation_issues),
                "judge_fsp_provider": self.fsp_provider.__class__.__name__,
                "include_evidence_max_length": include_evidence_max_length,
                "candidate_layout": candidate_layout,
            },
        )
        trace_step(
            context.task,
            "self_consistency_verdict_judge",
            prompt_messages=request.messages,
            request_payload={
                **request_payload(request),
                "trial_indices": [record.index for record in valid_records],
                "stable_fields": list(scope.stable_fields),
                "disputed_fields": list(scope.disputed_fields),
                "include_stable_fields_in_prompt": self.include_stable_fields_in_prompt,
                "include_support_counts": self.include_support_counts,
                "enforce_validation": self.enforce_validation,
                "report_validation": self.report_validation,
                "include_evidence_max_length": include_evidence_max_length,
                "candidate_layout": candidate_layout,
            },
            response_payload={
                "trials": [_trial_record_payload(record) for record in records],
                "raw_judge_output": raw_output,
                "fallback_used": error is not None,
                "fallback_reason": "judge_failed" if error else None,
                "validation_issues": list(validation_issues),
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
        candidate_layout = normalize_candidate_layout(self.candidate_layout)
        normalized_output = normalize_model_output_strings(dict(output))
        result = AggregationResult(
            output=normalized_output,
            mode=AggregationMode.JUDGE,
            selected_trial_index=selected_trial_index,
            metadata={
                "judge_scope": _scope_metadata(scope, judge_called=False),
                "fallback_used": True,
                "fallback_reason": reason,
                "variant": "candidate_verdicts",
                "candidate_layout": candidate_layout,
            },
        )
        trace_step(
            context.task,
            "self_consistency_verdict_judge_fallback",
            request_payload={
                "trial_indices": [record.index for record in records],
                "fallback_reason": reason,
                "candidate_layout": candidate_layout,
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
