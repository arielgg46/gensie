from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from gensie.fsp.examples import (
    DEFAULT_REASONING_SECTION_LABELS,
    ReasoningSectionLabels,
    StructuredFspCase,
)


@dataclass(frozen=True)
class SelectedFspCase:
    case: StructuredFspCase
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def name(self) -> str:
        return self.case.id

    @property
    def schema_match(self) -> bool:
        retrieval = self.metadata.get("retrieval")
        if not isinstance(retrieval, Mapping):
            return False
        return retrieval.get("schema_match") is True

    def as_metadata(self) -> dict[str, Any]:
        return {"name": self.name, **dict(self.metadata)}


@dataclass(frozen=True)
class FspSelection:
    cases: tuple[SelectedFspCase, ...] = ()
    labels: ReasoningSectionLabels = DEFAULT_REASONING_SECTION_LABELS

    def __post_init__(self) -> None:
        object.__setattr__(self, "cases", tuple(self.cases))

    @property
    def all_schema_match(self) -> bool:
        return bool(self.cases) and all(case.schema_match for case in self.cases)

    def metadata(self) -> list[dict[str, Any]]:
        return [case.as_metadata() for case in self.cases]
