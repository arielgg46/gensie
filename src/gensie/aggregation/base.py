from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from gensie.pipeline.context import PipelineContext
from gensie.pipeline.records import AggregationResult, TrialRecord
from gensie.pipeline.specs import AggregationMode
from gensie.schemas import coerce_nullable_string_nulls


class Aggregator(Protocol):
    def aggregate(
        self, records: Sequence[TrialRecord], context: PipelineContext
    ) -> AggregationResult:
        pass


class PassthroughAggregator:
    def aggregate(
        self, records: Sequence[TrialRecord], context: PipelineContext
    ) -> AggregationResult:
        for record in records:
            if record.result.is_valid:
                return AggregationResult(
                    output=coerce_nullable_string_nulls(
                        dict(record.result.output or {}),
                        context.task.target_schema,
                    ),
                    mode=AggregationMode.PASSTHROUGH,
                    selected_trial_index=record.index,
                    metadata={"selected_group": record.group_name},
                )
        return AggregationResult(
            output={"error": "No valid trial outputs to aggregate."},
            mode=AggregationMode.PASSTHROUGH,
            errors=("no_valid_trials",),
        )
