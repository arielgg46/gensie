from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from gensie.pipeline.specs import AggregationMode, ExtractionSpec


@dataclass(frozen=True)
class ExtractionResult:
    output: Mapping[str, Any] | None
    raw_output: Any | None = None
    reasoning: Mapping[str, Any] | None = None
    errors: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "output", dict(self.output) if self.output is not None else None
        )
        object.__setattr__(
            self,
            "reasoning",
            dict(self.reasoning) if self.reasoning is not None else None,
        )
        object.__setattr__(self, "errors", tuple(self.errors))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def is_valid(self) -> bool:
        return self.output is not None and not self.errors and "error" not in self.output


@dataclass(frozen=True)
class TrialRecord:
    index: int
    group_name: str
    extraction: ExtractionSpec
    result: ExtractionResult
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.index < 0:
            raise ValueError("TrialRecord.index must be non-negative")
        if not self.group_name.strip():
            raise ValueError("TrialRecord.group_name must not be empty")
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True)
class AggregationResult:
    output: Mapping[str, Any] | None
    mode: AggregationMode
    selected_trial_index: int | None = None
    errors: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "mode", AggregationMode(self.mode))
        object.__setattr__(
            self, "output", dict(self.output) if self.output is not None else None
        )
        object.__setattr__(self, "errors", tuple(self.errors))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def is_valid(self) -> bool:
        return self.output is not None and not self.errors and "error" not in self.output
