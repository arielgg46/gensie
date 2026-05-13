from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from gensie.pipeline.context import PipelineContext


@dataclass(frozen=True)
class PhaseResult:
    name: str
    data: Mapping[str, Any]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "data", dict(self.data))
        object.__setattr__(self, "metadata", dict(self.metadata))


class PipelinePhase(Protocol):
    name: str

    def run(
        self, context: PipelineContext, current: Mapping[str, Any] | None = None
    ) -> PhaseResult:
        pass
