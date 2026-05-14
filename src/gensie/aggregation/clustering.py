from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

from gensie.aggregation.config import SelfConsistencyConfig
from gensie.aggregation.schema_utils import (
    JsonDict,
    canonical_json,
    schema_type,
    unwrap_nullable_schema,
)
from gensie.aggregation.similarity import SchemaValueSimilarity
from gensie.schemas.inspect import deref


@dataclass(frozen=True)
class ValueCandidate:
    value: Any
    trial_index: int
    item_index: int = 0


@dataclass
class ValueCluster:
    members: list[ValueCandidate] = field(default_factory=list)

    @property
    def support(self) -> int:
        return len({member.trial_index for member in self.members})

    @property
    def first_position(self) -> tuple[int, int]:
        if not self.members:
            return (10**9, 10**9)
        return min((member.trial_index, member.item_index) for member in self.members)


@dataclass(frozen=True)
class IdentityFieldCandidate:
    name: str
    score: float
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class IdentityFieldDecision:
    field_name: str | None
    score: float
    margin: float
    confidence: str
    candidates: tuple[IdentityFieldCandidate, ...]


class IdentityFieldSelector(ABC):
    name = "base"

    @abstractmethod
    def select(
        self,
        schema: JsonDict,
        root_schema: JsonDict,
        *,
        config: SelfConsistencyConfig,
    ) -> IdentityFieldDecision:
        pass


class HeuristicIdentityFieldSelector(IdentityFieldSelector):
    name = "heuristic"

    POSITIVE_NAME_KEYWORDS = (
        "text",
        "name",
        "title",
        "reaction",
        "symptom",
        "ingredient",
        "entity",
        "mention",
    )
    POSITIVE_DESCRIPTION_KEYWORDS = (
        "verbatim",
        "name",
        "mention",
        "source",
        "ingredient",
        "symptom",
        "adverse effect",
        "reaction",
    )
    NEGATIVE_NAME_KEYWORDS = (
        "label",
        "category",
        "class",
        "type",
        "probability",
        "frequency",
        "impact",
        "severity",
        "amount",
        "unit",
        "date",
        "year",
        "count",
        "number",
        "score",
        "is_",
        "has_",
    )

    def select(
        self,
        schema: JsonDict,
        root_schema: JsonDict,
        *,
        config: SelfConsistencyConfig,
    ) -> IdentityFieldDecision:
        schema, _ = unwrap_nullable_schema(schema, root_schema)
        schema = deref(schema, root_schema)
        props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
        required = set(schema.get("required") or [])
        candidates: list[IdentityFieldCandidate] = []

        for name, prop_schema in props.items():
            if not isinstance(prop_schema, dict):
                continue
            prop_schema, _ = unwrap_nullable_schema(prop_schema, root_schema)
            prop_schema = deref(prop_schema, root_schema)
            prop_type = schema_type(prop_schema)
            is_enum = isinstance(prop_schema.get("enum"), list)
            lname = name.lower()
            desc = (prop_schema.get("description") or "").lower()
            score = 0.0
            reasons: list[str] = []

            if name in required:
                score += 3.0
                reasons.append("required")
            if prop_type == "string" and not is_enum:
                score += 4.0
                reasons.append("free_string")
            if any(keyword in lname for keyword in self.POSITIVE_NAME_KEYWORDS):
                score += 3.0
                reasons.append("identity_name_keyword")
            if any(keyword in desc for keyword in self.POSITIVE_DESCRIPTION_KEYWORDS):
                score += 2.0
                reasons.append("identity_description_keyword")
            if is_enum or prop_type in {"integer", "number", "boolean"}:
                score -= 4.0
                reasons.append("attribute_type")
            if any(keyword in lname for keyword in self.NEGATIVE_NAME_KEYWORDS):
                score -= 3.0
                reasons.append("attribute_name_keyword")

            candidates.append(
                IdentityFieldCandidate(
                    name=name,
                    score=score,
                    reasons=tuple(reasons),
                )
            )

        candidates.sort(key=lambda candidate: (-candidate.score, candidate.name))
        best = candidates[0] if candidates else None
        runner_up_score = candidates[1].score if len(candidates) > 1 else 0.0
        margin = (best.score - runner_up_score) if best else 0.0
        if best and best.score >= config.identity_min_score and margin >= config.identity_min_margin:
            confidence = "high"
            field_name: str | None = best.name
        elif best and best.score >= config.identity_min_score:
            confidence = "medium"
            field_name = best.name
        else:
            confidence = "none"
            field_name = None

        return IdentityFieldDecision(
            field_name=field_name,
            score=best.score if best else 0.0,
            margin=margin,
            confidence=confidence,
            candidates=tuple(candidates),
        )


class NoIdentityFieldSelector(IdentityFieldSelector):
    name = "none"

    def select(
        self,
        schema: JsonDict,
        root_schema: JsonDict,
        *,
        config: SelfConsistencyConfig,
    ) -> IdentityFieldDecision:
        return IdentityFieldDecision(
            field_name=None,
            score=0.0,
            margin=0.0,
            confidence="disabled",
            candidates=(),
        )


class ItemClusterer:
    """Greedy constrained clustering with at most one item vote per trial."""

    def __init__(self, comparator: SchemaValueSimilarity):
        self.comparator = comparator

    def cluster(
        self,
        candidates: Sequence[ValueCandidate],
        schema: JsonDict,
        root_schema: JsonDict,
        *,
        threshold: float,
        exact: bool = False,
        similarity_func: Callable[[Any, Any], float] | None = None,
    ) -> list[ValueCluster]:
        if exact:
            grouped: dict[str, list[ValueCandidate]] = defaultdict(list)
            for candidate in candidates:
                grouped[canonical_json(candidate.value)].append(candidate)
            clusters = [ValueCluster(members=members) for members in grouped.values()]
            clusters.sort(key=lambda cluster: (-cluster.support, cluster.first_position))
            return clusters

        clusters: list[ValueCluster] = []
        compare = similarity_func or (
            lambda a, b: self.comparator.similarity(a, b, schema, root_schema)
        )
        for candidate in candidates:
            best_cluster: ValueCluster | None = None
            best_score = -1.0
            for cluster in clusters:
                if any(member.trial_index == candidate.trial_index for member in cluster.members):
                    continue
                score = max(compare(candidate.value, member.value) for member in cluster.members)
                if score >= threshold and score > best_score:
                    best_cluster = cluster
                    best_score = score
            if best_cluster is None:
                clusters.append(ValueCluster(members=[candidate]))
            else:
                best_cluster.members.append(candidate)

        clusters.sort(key=lambda cluster: (-cluster.support, cluster.first_position))
        return clusters


def medoid(
    members: Sequence[ValueCandidate],
    schema: JsonDict,
    root_schema: JsonDict,
    comparator: SchemaValueSimilarity,
) -> Any:
    if not members:
        return None
    if len(members) == 1:
        return members[0].value

    best_member = members[0]
    best_score = -1.0
    for candidate in members:
        score = 0.0
        for other in members:
            score += comparator.similarity(candidate.value, other.value, schema, root_schema)
        score /= len(members)
        if score > best_score:
            best_score = score
            best_member = candidate
    return best_member.value
