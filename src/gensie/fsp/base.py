from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from gensie.pipeline.context import PipelineContext
from gensie.pipeline.specs import ExtractionSpec


@dataclass(frozen=True)
class FSPExample:
    name: str
    prompt: str
    output: Mapping[str, Any]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "output", dict(self.output))
        object.__setattr__(self, "metadata", dict(self.metadata))


class FSPProvider(Protocol):
    def examples(
        self, context: PipelineContext, extraction: ExtractionSpec
    ) -> tuple[FSPExample, ...]:
        pass
