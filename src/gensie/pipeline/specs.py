from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping


class ReasoningMode(StrEnum):
    NONE = "none"
    TOP_LEVEL = "top_level"
    DEEP = "deep"


class SchemaPromptMode(StrEnum):
    JSON_SCHEMA = "json_schema"
    PYDANTIC = "pydantic"
    REASONED_PYDANTIC = "reasoned_pydantic"


class FewShotMode(StrEnum):
    NONE = "none"
    FIXED = "fixed"
    SUPER_STATIC = "super_static"
    SUPER_DYNAMIC = "super_dynamic"
    RAG = "rag"


class PhaseKind(StrEnum):
    VERBATIM_ENTITIES = "verbatim_entities"
    SELF_REFINE = "self_refine"
    SUBEXTRACTION = "subextraction"


class AggregationMode(StrEnum):
    PASSTHROUGH = "passthrough"
    HEURISTIC_SELF_CONSISTENCY = "heuristic_self_consistency"
    JUDGE = "judge"


def _options(value: Mapping[str, Any] | None) -> dict[str, Any]:
    return dict(value or {})


@dataclass(frozen=True)
class ExtractionSpec:
    name: str = "baseline"
    reasoning: ReasoningMode = ReasoningMode.NONE
    schema_prompt: SchemaPromptMode = SchemaPromptMode.JSON_SCHEMA
    few_shot: FewShotMode = FewShotMode.NONE
    phases: tuple[PhaseKind, ...] = ()
    options: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "reasoning", ReasoningMode(self.reasoning))
        object.__setattr__(self, "schema_prompt", SchemaPromptMode(self.schema_prompt))
        object.__setattr__(self, "few_shot", FewShotMode(self.few_shot))
        object.__setattr__(
            self, "phases", tuple(PhaseKind(phase) for phase in self.phases)
        )
        object.__setattr__(self, "options", _options(self.options))
        if not self.name.strip():
            raise ValueError("ExtractionSpec.name must not be empty")
        if (
            self.schema_prompt is SchemaPromptMode.REASONED_PYDANTIC
            and self.reasoning is ReasoningMode.NONE
        ):
            raise ValueError("reasoned pydantic schema requires inline reasoning")


@dataclass(frozen=True)
class TrialGroupSpec:
    name: str
    extraction: ExtractionSpec
    count: int | None = None
    ratio: float | None = None
    min_count: int = 0
    max_count: int | None = None
    options: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "options", _options(self.options))
        if not self.name.strip():
            raise ValueError("TrialGroupSpec.name must not be empty")
        if self.count is not None and self.ratio is not None:
            raise ValueError("TrialGroupSpec accepts either count or ratio, not both")
        if self.count is not None and self.count < 0:
            raise ValueError("TrialGroupSpec.count must be non-negative")
        if self.ratio is not None and self.ratio <= 0:
            raise ValueError("TrialGroupSpec.ratio must be positive")
        if self.min_count < 0:
            raise ValueError("TrialGroupSpec.min_count must be non-negative")
        if self.max_count is not None and self.max_count < self.min_count:
            raise ValueError("TrialGroupSpec.max_count must be >= min_count")
        if self.count is not None:
            if self.count < self.min_count:
                raise ValueError("TrialGroupSpec.count must be >= min_count")
            if self.max_count is not None and self.count > self.max_count:
                raise ValueError("TrialGroupSpec.count must be <= max_count")


@dataclass(frozen=True)
class SamplingSpec:
    total_trials: int = 1
    groups: tuple[TrialGroupSpec, ...] = ()
    interleave: bool = True
    options: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "groups", tuple(self.groups))
        object.__setattr__(self, "options", _options(self.options))
        if self.total_trials < 1:
            raise ValueError("SamplingSpec.total_trials must be >= 1")

    @property
    def is_multi_trial(self) -> bool:
        return self.total_trials > 1 or bool(self.groups)


@dataclass(frozen=True)
class AggregationSpec:
    mode: AggregationMode = AggregationMode.PASSTHROUGH
    judge_model: str | None = None
    options: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "mode", AggregationMode(self.mode))
        object.__setattr__(self, "options", _options(self.options))
        if self.mode is not AggregationMode.JUDGE and self.judge_model:
            raise ValueError("judge_model is only valid for judge aggregation")


@dataclass(frozen=True)
class PipelineSpec:
    name: str
    description: str
    extraction: ExtractionSpec = field(default_factory=ExtractionSpec)
    sampling: SamplingSpec = field(default_factory=SamplingSpec)
    aggregation: AggregationSpec = field(default_factory=AggregationSpec)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _options(self.metadata))
        if not self.name.strip():
            raise ValueError("PipelineSpec.name must not be empty")
        if not self.description.strip():
            raise ValueError("PipelineSpec.description must not be empty")

    @property
    def requires_aggregation(self) -> bool:
        return (
            self.sampling.is_multi_trial
            or self.aggregation.mode is not AggregationMode.PASSTHROUGH
        )
