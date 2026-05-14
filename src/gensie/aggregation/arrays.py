from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol, Sequence

from gensie.aggregation.config import SelfConsistencyConfig
from gensie.aggregation.clustering import ValueCluster
from gensie.aggregation.schema_utils import JsonDict, canonical_json


class ArrayAggregator(Protocol):
    def aggregate_cluster(
        self, cluster: ValueCluster, schema: JsonDict, root_schema: JsonDict
    ) -> Any:
        pass

    def score_array_candidate(
        self,
        candidate: Sequence[Any],
        observed_arrays: Sequence[list[Any]],
        item_schema: JsonDict,
        root_schema: JsonDict,
    ) -> float:
        pass


class ArrayCandidateBuilder(ABC):
    @abstractmethod
    def build(
        self,
        clusters: Sequence[ValueCluster],
        observed_arrays: Sequence[list[Any]],
        item_schema: JsonDict,
        root_schema: JsonDict,
        aggregator: ArrayAggregator,
    ) -> list[list[Any]]:
        pass


@dataclass(frozen=True)
class SupportThresholdArrayCandidateBuilder(ArrayCandidateBuilder):
    support_floors: Sequence[int]

    def build(
        self,
        clusters: Sequence[ValueCluster],
        observed_arrays: Sequence[list[Any]],
        item_schema: JsonDict,
        root_schema: JsonDict,
        aggregator: ArrayAggregator,
    ) -> list[list[Any]]:
        del observed_arrays
        candidates: list[list[Any]] = []
        seen: set[str] = set()
        for floor in self.support_floors:
            items = [
                aggregator.aggregate_cluster(cluster, item_schema, root_schema)
                for cluster in clusters
                if cluster.support >= floor
            ]
            key = canonical_json(items)
            if key not in seen:
                seen.add(key)
                candidates.append(items)
        return candidates


class GreedyMbrArrayCandidateBuilder(ArrayCandidateBuilder):
    def build(
        self,
        clusters: Sequence[ValueCluster],
        observed_arrays: Sequence[list[Any]],
        item_schema: JsonDict,
        root_schema: JsonDict,
        aggregator: ArrayAggregator,
    ) -> list[list[Any]]:
        selected: list[ValueCluster] = []
        selected_values: list[Any] = []
        best_score = aggregator.score_array_candidate(
            selected_values, observed_arrays, item_schema, root_schema
        )

        ordered = sorted(clusters, key=lambda cluster: (-cluster.support, cluster.first_position))
        improved = True
        while improved:
            improved = False
            best_next: tuple[float, ValueCluster, Any] | None = None
            for cluster in ordered:
                if cluster in selected:
                    continue
                value = aggregator.aggregate_cluster(cluster, item_schema, root_schema)
                candidate = selected_values + [value]
                score = aggregator.score_array_candidate(
                    candidate, observed_arrays, item_schema, root_schema
                )
                if score > best_score and (
                    best_next is None or score > best_next[0]
                ):
                    best_next = (score, cluster, value)
            if best_next is not None:
                best_score, cluster, value = best_next
                selected.append(cluster)
                selected_values.append(value)
                improved = True

        return [selected_values]


class ArrayCandidateSelector(ABC):
    @abstractmethod
    def select(
        self,
        candidates: Sequence[list[Any]],
        observed_arrays: Sequence[list[Any]],
        item_schema: JsonDict,
        root_schema: JsonDict,
        aggregator: ArrayAggregator,
    ) -> list[Any]:
        pass


class MbrArrayCandidateSelector(ArrayCandidateSelector):
    def select(
        self,
        candidates: Sequence[list[Any]],
        observed_arrays: Sequence[list[Any]],
        item_schema: JsonDict,
        root_schema: JsonDict,
        aggregator: ArrayAggregator,
    ) -> list[Any]:
        if not candidates:
            return []
        best = list(candidates[0])
        best_score = -1.0
        for candidate in candidates:
            score = aggregator.score_array_candidate(
                candidate, observed_arrays, item_schema, root_schema
            )
            if score > best_score:
                best_score = score
                best = list(candidate)
        return best


@dataclass(frozen=True)
class RecallBiasedMbrArrayCandidateSelector(ArrayCandidateSelector):
    score_tolerance: float = 0.06

    def select(
        self,
        candidates: Sequence[list[Any]],
        observed_arrays: Sequence[list[Any]],
        item_schema: JsonDict,
        root_schema: JsonDict,
        aggregator: ArrayAggregator,
    ) -> list[Any]:
        if not candidates:
            return []

        scored: list[tuple[int, list[Any], float]] = []
        for index, candidate in enumerate(candidates):
            score = aggregator.score_array_candidate(
                candidate, observed_arrays, item_schema, root_schema
            )
            scored.append((index, list(candidate), score))

        best_score = max(score for _, _, score in scored)
        min_score = best_score - max(self.score_tolerance, 0.0)
        eligible = [entry for entry in scored if entry[2] >= min_score]
        _, best_candidate, _ = max(
            eligible,
            key=lambda entry: (len(entry[1]), entry[2], -entry[0]),
        )
        return best_candidate


def build_array_selector_from_config(
    config: SelfConsistencyConfig,
) -> ArrayCandidateSelector:
    mode = config.array_selector_mode.strip().lower().replace("-", "_")
    if mode in {"mbr", "pure_mbr", "precision_mbr"}:
        return MbrArrayCandidateSelector()
    if mode in {"recall_biased", "recall_biased_mbr", "recall"}:
        return RecallBiasedMbrArrayCandidateSelector(
            score_tolerance=config.recall_mbr_tolerance
        )
    return RecallBiasedMbrArrayCandidateSelector(
        score_tolerance=config.recall_mbr_tolerance
    )
