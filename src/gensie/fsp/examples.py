from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal, Mapping, Sequence

JsonDict = dict[str, Any]


class CandidateOrder(StrEnum):
    RESOURCE = "resource"
    SUPPORT_DESC = "support_desc"
    SUPPORT_ASC = "support_asc"
    FIRST_SEEN = "first_seen"
    CANONICAL_JSON = "canonical_json"


@dataclass(frozen=True)
class ReasoningSectionLabels:
    field_asks: str = "EL CAMPO PIDE"
    relevant_fragments: str = "FRAGMENTOS RELEVANTES"
    final_value: str = "VALOR FINAL"


DEFAULT_REASONING_SECTION_LABELS = ReasoningSectionLabels()


@dataclass(frozen=True)
class FieldReasoning:
    field_asks: str
    relevant_fragments: str
    final_value: str
    exact_text: str | None = None

    def render(
        self, labels: ReasoningSectionLabels = DEFAULT_REASONING_SECTION_LABELS
    ) -> str:
        if self.exact_text is not None and labels == DEFAULT_REASONING_SECTION_LABELS:
            return self.exact_text
        return "\n".join(
            (
                f"{labels.field_asks}: {self.field_asks}",
                f"{labels.relevant_fragments}: {self.relevant_fragments}",
                f"{labels.final_value}: {self.final_value}",
            )
        )


@dataclass(frozen=True)
class FieldExample:
    value: Any
    tags: tuple[str, ...] = ()
    reasoning: FieldReasoning | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", copy.deepcopy(self.value))
        object.__setattr__(self, "tags", tuple(self.tags))


@dataclass(frozen=True)
class JudgeCandidateExample:
    value: Any
    support: int
    evidence: str
    include: bool | None = None
    first_seen: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", copy.deepcopy(self.value))
        if self.support < 0:
            raise ValueError("JudgeCandidateExample.support must be non-negative")
        if self.first_seen is not None and self.first_seen < 0:
            raise ValueError("JudgeCandidateExample.first_seen must be non-negative")


@dataclass(frozen=True)
class JudgeFieldExample:
    kind: Literal["single", "array"]
    candidates: tuple[JudgeCandidateExample, ...]
    value: Any | None = None
    reasoned_output: Mapping[str, Any] | None = None
    empty_trial_count: int = 0
    null_trial_count: int = 0
    invalid_value_count: int = 0
    field_description: str | None = None
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.kind not in {"single", "array"}:
            raise ValueError("JudgeFieldExample.kind must be 'single' or 'array'")
        object.__setattr__(self, "candidates", tuple(self.candidates))
        object.__setattr__(self, "value", copy.deepcopy(self.value))
        object.__setattr__(
            self,
            "reasoned_output",
            copy.deepcopy(dict(self.reasoned_output))
            if self.reasoned_output is not None
            else None,
        )
        for name in ("empty_trial_count", "null_trial_count", "invalid_value_count"):
            if getattr(self, name) < 0:
                raise ValueError(f"JudgeFieldExample.{name} must be non-negative")
        object.__setattr__(self, "tags", tuple(self.tags))


@dataclass(frozen=True)
class JudgeExample:
    total_trials: int
    fields: Mapping[str, JudgeFieldExample]
    stable_fields: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.total_trials < 1:
            raise ValueError("JudgeExample.total_trials must be >= 1")
        object.__setattr__(self, "fields", dict(self.fields))
        object.__setattr__(self, "stable_fields", copy.deepcopy(dict(self.stable_fields)))


@dataclass(frozen=True)
class StructuredFspCase:
    id: str
    domain: str
    language: str
    source_text: str
    instruction: str
    schema: JsonDict
    field_examples: Mapping[str, FieldExample]
    tags: tuple[str, ...] = ()
    judge: JudgeExample | None = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("StructuredFspCase.id must not be empty")
        if not self.source_text.strip():
            raise ValueError("StructuredFspCase.source_text must not be empty")
        if not self.instruction.strip():
            raise ValueError("StructuredFspCase.instruction must not be empty")
        object.__setattr__(self, "schema", copy.deepcopy(self.schema))
        object.__setattr__(self, "field_examples", dict(self.field_examples))
        object.__setattr__(self, "tags", tuple(self.tags))


def exact_reasoning_from_text(
    text: str,
    labels: ReasoningSectionLabels = DEFAULT_REASONING_SECTION_LABELS,
) -> FieldReasoning:
    parts = _split_reasoning_sections(text, labels)
    return FieldReasoning(
        field_asks=parts.get("field_asks", ""),
        relevant_fragments=parts.get("relevant_fragments", ""),
        final_value=parts.get("final_value", ""),
        exact_text=text,
    )


def ordered_candidates(
    candidates: Sequence[JudgeCandidateExample],
    order: CandidateOrder = CandidateOrder.RESOURCE,
) -> tuple[JudgeCandidateExample, ...]:
    items = tuple(candidates)
    if order is CandidateOrder.RESOURCE:
        return items
    if order is CandidateOrder.SUPPORT_DESC:
        return tuple(
            sorted(
                items,
                key=lambda item: (
                    -item.support,
                    item.first_seen if item.first_seen is not None else 10**9,
                    canonical_json(item.value),
                ),
            )
        )
    if order is CandidateOrder.SUPPORT_ASC:
        return tuple(
            sorted(
                items,
                key=lambda item: (
                    item.support,
                    item.first_seen if item.first_seen is not None else 10**9,
                    canonical_json(item.value),
                ),
            )
        )
    if order is CandidateOrder.FIRST_SEEN:
        return tuple(
            sorted(
                items,
                key=lambda item: (
                    item.first_seen if item.first_seen is not None else 10**9,
                    canonical_json(item.value),
                ),
            )
        )
    if order is CandidateOrder.CANONICAL_JSON:
        return tuple(sorted(items, key=lambda item: canonical_json(item.value)))
    raise ValueError(f"unsupported candidate order: {order}")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _split_reasoning_sections(
    text: str, labels: ReasoningSectionLabels
) -> dict[str, str]:
    markers = (
        ("field_asks", f"{labels.field_asks}:"),
        ("relevant_fragments", f"{labels.relevant_fragments}:"),
        ("final_value", f"{labels.final_value}:"),
    )
    positions: list[tuple[str, str, int]] = []
    for key, marker in markers:
        index = text.find(marker)
        if index >= 0:
            positions.append((key, marker, index))
    positions.sort(key=lambda item: item[2])

    out: dict[str, str] = {}
    for index, (key, marker, start) in enumerate(positions):
        content_start = start + len(marker)
        content_end = positions[index + 1][2] if index + 1 < len(positions) else len(text)
        out[key] = text[content_start:content_end].strip()
    return out
