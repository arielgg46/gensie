from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from gensie.aggregation.config import build_self_consistency_config_from_env
from gensie.aggregation.self_consistency import SchemaAwareSelfConsistencyAggregator
from gensie.aggregation.similarity import build_string_similarity_from_env
from gensie.pipeline.context import PipelineContext
from gensie.pipeline.records import AggregationResult, TrialRecord
from gensie.pipeline.specs import AggregationMode
from gensie.runtime import trace_step


class HeuristicSelfConsistencyAggregator:
    def __init__(
        self,
        *,
        aggregator: SchemaAwareSelfConsistencyAggregator | None = None,
    ):
        self.aggregator = aggregator or SchemaAwareSelfConsistencyAggregator(
            config=build_self_consistency_config_from_env(),
            string_similarity=build_string_similarity_from_env(),
        )

    def aggregate(
        self, records: Sequence[TrialRecord], context: PipelineContext
    ) -> AggregationResult:
        started_at = datetime.now(timezone.utc)
        started_perf = time.perf_counter()
        valid_records = [record for record in records if record.result.is_valid]
        if not valid_records:
            error = "; ".join(
                error
                for record in records
                for error in record.result.errors
                if error
            ) or "No valid self-consistency trials."
            result = AggregationResult(
                output={"error": f"Failed to run self-consistency: {error}"},
                mode=AggregationMode.HEURISTIC_SELF_CONSISTENCY,
                errors=("no_valid_trials",),
            )
            self._trace(context, records, result, started_at, started_perf, error=error)
            return result

        candidates = [dict(record.result.output or {}) for record in valid_records]
        output, diagnostics = self.aggregator.aggregate_with_diagnostics(
            candidates, context.task.target_schema
        )
        result = AggregationResult(
            output=output,
            mode=AggregationMode.HEURISTIC_SELF_CONSISTENCY,
            metadata={
                "valid_trial_indices": [record.index for record in valid_records],
                "aggregation_diagnostics": diagnostics,
            },
        )
        self._trace(context, records, result, started_at, started_perf)
        return result

    def _trace(
        self,
        context: PipelineContext,
        records: Sequence[TrialRecord],
        result: AggregationResult,
        started_at: datetime,
        started_perf: float,
        *,
        error: str | None = None,
    ) -> None:
        completed_at = datetime.now(timezone.utc)
        duration_ms = (time.perf_counter() - started_perf) * 1000
        trace_step(
            context.task,
            "self_consistency_aggregate",
            request_payload={
                "trial_indices": [record.index for record in records],
                "valid_trial_indices": [
                    record.index for record in records if record.result.is_valid
                ],
                "aggregation": "schema_aware_self_consistency",
            },
            response_payload={
                "trials": [_trial_record_payload(record) for record in records],
                "final_output": result.output,
                "aggregation_diagnostics": result.metadata.get(
                    "aggregation_diagnostics"
                ),
            },
            error=error,
            metrics={
                "request": {"is_model_request": False},
                "tokens": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
                "timings": {
                    "started_at": started_at.isoformat(),
                    "completed_at": completed_at.isoformat(),
                    "total_duration_ms": round(duration_ms, 3),
                    "time_to_first_token_ms": None,
                    "time_to_first_token_note": "Aggregation step; no model stream.",
                },
            },
        )


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
