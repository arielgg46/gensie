from __future__ import annotations

import math
from typing import Any, Sequence

from gensie.aggregation.arrays import (
    ArrayCandidateBuilder,
    ArrayCandidateSelector,
    GreedyMbrArrayCandidateBuilder,
    SupportThresholdArrayCandidateBuilder,
    build_array_selector_from_config,
)
from gensie.aggregation.config import SelfConsistencyConfig
from gensie.aggregation.clustering import (
    HeuristicIdentityFieldSelector,
    IdentityFieldDecision,
    IdentityFieldSelector,
    ItemClusterer,
    NoIdentityFieldSelector,
    ValueCandidate,
    ValueCluster,
    medoid,
)
from gensie.aggregation.diagnostics import build_self_consistency_diagnostics
from gensie.aggregation.schema_utils import (
    JsonDict,
    canonical_json,
    deref_item_schema,
    is_required,
    schema_type,
    unwrap_nullable_schema,
)
from gensie.aggregation.similarity import (
    SchemaValueSimilarity,
    StringSimilarity,
    build_string_similarity_from_env,
)
from gensie.schemas.inspect import deref


class SchemaAwareSelfConsistencyAggregator:
    """
    Field-wise self-consistency for GenSIE outputs.

    Arrays are aggregated item-wise, then selected by expected schema-aware
    similarity to the sampled arrays. This follows the reference implementation
    while keeping similarity, clustering, and array selection in separate files.
    """

    def __init__(
        self,
        *,
        config: SelfConsistencyConfig | None = None,
        string_similarity: StringSimilarity | None = None,
        array_selector: ArrayCandidateSelector | None = None,
        identity_selector: IdentityFieldSelector | None = None,
    ):
        self.config = config or SelfConsistencyConfig()
        self.string_similarity = string_similarity or build_string_similarity_from_env()
        self.comparator = SchemaValueSimilarity(self.string_similarity)
        self.clusterer = ItemClusterer(self.comparator)
        self.array_selector = array_selector or build_array_selector_from_config(
            self.config
        )
        if identity_selector is not None:
            self.identity_selector = identity_selector
        elif self.config.use_identity_clustering:
            self.identity_selector = HeuristicIdentityFieldSelector()
        else:
            self.identity_selector = NoIdentityFieldSelector()
        self._identity_decision_cache: dict[str, IdentityFieldDecision] = {}

    def aggregate(self, outputs: Sequence[JsonDict], schema: JsonDict) -> JsonDict:
        root_schema = schema
        schema, _ = unwrap_nullable_schema(schema, root_schema)
        schema = deref(schema, root_schema)
        if schema.get("type") != "object":
            value = self.aggregate_value(list(outputs), schema, root_schema)
            return value if isinstance(value, dict) else {"value": value}
        return self.aggregate_object(list(outputs), schema, root_schema, root=True)

    def aggregate_with_diagnostics(
        self, outputs: Sequence[JsonDict], schema: JsonDict
    ) -> tuple[JsonDict, JsonDict]:
        final_output = self.aggregate(outputs, schema)
        root_schema = schema
        diagnostics = build_self_consistency_diagnostics(
            self, outputs, schema, final_output
        )
        return final_output, diagnostics

    def aggregate_value(
        self, values: Sequence[Any], schema: JsonDict, root_schema: JsonDict
    ) -> Any:
        schema, nullable = unwrap_nullable_schema(schema, root_schema)
        schema = deref(schema, root_schema)
        non_null = [
            ValueCandidate(value, index)
            for index, value in enumerate(values)
            if value is not None
        ]
        null_count = len(values) - len(non_null)

        if not non_null:
            return None if nullable else self._empty_value_for_schema(schema, root_schema)

        current_type = schema_type(schema)
        if current_type == "object":
            if self._null_wins(null_count, len(non_null), nullable):
                return None
            return self.aggregate_object(
                [candidate.value for candidate in non_null if isinstance(candidate.value, dict)],
                schema,
                root_schema,
            )

        if current_type == "array":
            if self._null_wins(null_count, len(non_null), nullable):
                return None
            arrays = [candidate.value for candidate in non_null if isinstance(candidate.value, list)]
            return self.aggregate_array(arrays, schema, root_schema)

        clusters = self.cluster_scalar_candidates(non_null, schema, root_schema)
        best_cluster = clusters[0] if clusters else ValueCluster([])
        if self._null_wins(null_count, best_cluster.support, nullable):
            return None
        return self.aggregate_cluster(best_cluster, schema, root_schema)

    def aggregate_object(
        self,
        objects: Sequence[JsonDict],
        schema: JsonDict,
        root_schema: JsonDict,
        *,
        root: bool = False,
    ) -> JsonDict:
        objects = [obj for obj in objects if isinstance(obj, dict)]
        props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
        out: JsonDict = {}
        for name, child_schema in props.items():
            if not isinstance(child_schema, dict):
                continue
            present_values = [obj[name] for obj in objects if name in obj]
            if not present_values and not is_required(schema, name) and not root:
                continue
            if not root and not is_required(schema, name):
                needed = max(
                    1,
                    math.ceil(len(objects) * self.config.optional_property_support_ratio),
                )
                if len(present_values) < needed:
                    continue
            out[name] = self.aggregate_value(present_values, child_schema, root_schema)
        return out

    def aggregate_array(
        self, arrays: Sequence[list[Any]], schema: JsonDict, root_schema: JsonDict
    ) -> list[Any]:
        arrays = [array for array in arrays if isinstance(array, list)]
        if not arrays:
            return []

        item_schema = deref_item_schema(schema, root_schema)
        candidates = self._array_item_candidates(arrays, item_schema, root_schema)
        if not candidates:
            return []

        clusters = self.cluster_array_items(candidates, item_schema, root_schema)
        candidate_arrays = self.build_array_candidates(
            clusters, arrays, item_schema, root_schema
        )
        return self.array_selector.select(
            candidate_arrays, arrays, item_schema, root_schema, self
        )

    def aggregate_cluster(
        self, cluster: ValueCluster, schema: JsonDict, root_schema: JsonDict
    ) -> Any:
        schema, nullable = unwrap_nullable_schema(schema, root_schema)
        schema = deref(schema, root_schema)
        values = [member.value for member in cluster.members]
        if not values:
            return None if nullable else self._empty_value_for_schema(schema, root_schema)

        current_type = schema_type(schema)
        if current_type == "object":
            return self.aggregate_object(
                [value for value in values if isinstance(value, dict)],
                schema,
                root_schema,
            )
        if current_type == "array":
            return self.aggregate_array(
                [value for value in values if isinstance(value, list)],
                schema,
                root_schema,
            )
        return medoid(cluster.members, schema, root_schema, self.comparator)

    def cluster_scalar_candidates(
        self,
        candidates: Sequence[ValueCandidate],
        schema: JsonDict,
        root_schema: JsonDict,
    ) -> list[ValueCluster]:
        schema, _ = unwrap_nullable_schema(schema, root_schema)
        schema = deref(schema, root_schema)
        exact = self._uses_exact_matching(schema, root_schema)
        threshold = 1.0 if exact else self.config.scalar_string_threshold
        return self.clusterer.cluster(
            candidates,
            schema,
            root_schema,
            threshold=threshold,
            exact=exact,
        )

    def cluster_array_items(
        self,
        candidates: Sequence[ValueCandidate],
        item_schema: JsonDict,
        root_schema: JsonDict,
    ) -> list[ValueCluster]:
        exact = self._uses_exact_matching(item_schema, root_schema)
        threshold = self._array_item_threshold(item_schema, root_schema)
        similarity_func = None
        identity_decision = self.select_identity_field(item_schema, root_schema)
        if identity_decision.field_name:
            threshold = self.config.identity_string_threshold
            similarity_func = self._identity_similarity_func(
                item_schema, root_schema, identity_decision.field_name
            )
        return self.clusterer.cluster(
            candidates,
            item_schema,
            root_schema,
            threshold=threshold,
            exact=exact,
            similarity_func=similarity_func,
        )

    def select_identity_field(
        self, item_schema: JsonDict, root_schema: JsonDict
    ) -> IdentityFieldDecision:
        item_schema, _ = unwrap_nullable_schema(item_schema, root_schema)
        item_schema = deref(item_schema, root_schema)
        if schema_type(item_schema) != "object":
            return IdentityFieldDecision(
                field_name=None,
                score=0.0,
                margin=0.0,
                confidence="not_applicable",
                candidates=(),
            )

        cache_key = canonical_json(item_schema)
        cached = self._identity_decision_cache.get(cache_key)
        if cached is not None:
            return cached

        decision = self.identity_selector.select(
            item_schema, root_schema, config=self.config
        )
        if not self.config.use_identity_clustering:
            decision = NoIdentityFieldSelector().select(
                item_schema, root_schema, config=self.config
            )
        self._identity_decision_cache[cache_key] = decision
        return decision

    def _identity_similarity_func(
        self, item_schema: JsonDict, root_schema: JsonDict, field_name: str
    ):
        item_schema, _ = unwrap_nullable_schema(item_schema, root_schema)
        item_schema = deref(item_schema, root_schema)
        props = item_schema.get("properties") if isinstance(item_schema.get("properties"), dict) else {}
        field_schema = props.get(field_name) if isinstance(props.get(field_name), dict) else {}

        def compare(a: Any, b: Any) -> float:
            if not isinstance(a, dict) or not isinstance(b, dict):
                return self.comparator.similarity(a, b, item_schema, root_schema)
            if field_name not in a or field_name not in b:
                return self.comparator.similarity(a, b, item_schema, root_schema)
            return self.comparator.similarity(
                a[field_name], b[field_name], field_schema, root_schema
            )

        return compare

    def score_array_candidate(
        self,
        candidate: Sequence[Any],
        observed_arrays: Sequence[list[Any]],
        item_schema: JsonDict,
        root_schema: JsonDict,
    ) -> float:
        if not observed_arrays:
            return 0.0
        return sum(
            self.comparator.array_similarity(
                candidate, observed, item_schema, root_schema
            )
            for observed in observed_arrays
        ) / len(observed_arrays)

    def build_array_candidates(
        self,
        clusters: Sequence[ValueCluster],
        observed_arrays: Sequence[list[Any]],
        item_schema: JsonDict,
        root_schema: JsonDict,
    ) -> list[list[Any]]:
        support_floors = self._support_floors(
            len(observed_arrays), item_schema, root_schema
        )
        builders: list[ArrayCandidateBuilder] = []
        if self.config.include_threshold_array_candidates:
            builders.append(SupportThresholdArrayCandidateBuilder(support_floors))
        if self.config.include_greedy_array_candidate:
            builders.append(GreedyMbrArrayCandidateBuilder())

        candidate_arrays: list[list[Any]] = []
        seen: set[str] = set()
        for builder in builders:
            for candidate in builder.build(
                clusters, observed_arrays, item_schema, root_schema, self
            ):
                key = canonical_json(candidate)
                if key not in seen:
                    seen.add(key)
                    candidate_arrays.append(candidate)

        if self.config.include_original_array_candidates:
            for array in observed_arrays:
                key = canonical_json(array)
                if key not in seen:
                    seen.add(key)
                    candidate_arrays.append(array)
        return candidate_arrays

    def _array_item_candidates(
        self,
        arrays: Sequence[list[Any]],
        item_schema: JsonDict,
        root_schema: JsonDict,
    ) -> list[ValueCandidate]:
        out: list[ValueCandidate] = []
        for trial_index, array in enumerate(arrays):
            trial_candidates = [
                ValueCandidate(value, trial_index, item_index)
                for item_index, value in enumerate(array)
            ]
            out.extend(
                self._dedupe_trial_candidates(
                    trial_candidates, item_schema, root_schema
                )
            )
        return out

    def _dedupe_trial_candidates(
        self,
        candidates: Sequence[ValueCandidate],
        schema: JsonDict,
        root_schema: JsonDict,
    ) -> list[ValueCandidate]:
        kept: list[ValueCandidate] = []
        exact = self._uses_exact_matching(schema, root_schema)
        threshold = 1.0 if exact else self.config.intra_trial_dedupe_threshold
        for candidate in candidates:
            if any(
                self.comparator.similarity(
                    candidate.value, old.value, schema, root_schema
                )
                >= threshold
                for old in kept
            ):
                continue
            kept.append(candidate)
        return kept

    def _support_floors(
        self, sample_count: int, item_schema: JsonDict, root_schema: JsonDict
    ) -> list[int]:
        item_schema, _ = unwrap_nullable_schema(item_schema, root_schema)
        item_schema = deref(item_schema, root_schema)
        current_type = schema_type(item_schema)
        base = (
            self.config.object_item_support_floor
            if current_type == "object"
            else self.config.simple_item_support_floor
        )
        floors = {max(1, min(sample_count, base))}
        for ratio in self.config.support_ratios:
            floors.add(max(1, min(sample_count, math.ceil(sample_count * ratio))))
        return sorted(floors)

    def _array_item_threshold(
        self, item_schema: JsonDict, root_schema: JsonDict
    ) -> float:
        item_schema, _ = unwrap_nullable_schema(item_schema, root_schema)
        item_schema = deref(item_schema, root_schema)
        current_type = schema_type(item_schema)
        if current_type == "object":
            return self.config.object_item_threshold
        if current_type == "string":
            return self.config.array_string_threshold
        return 1.0

    def _uses_exact_matching(self, schema: JsonDict, root_schema: JsonDict) -> bool:
        schema, _ = unwrap_nullable_schema(schema, root_schema)
        schema = deref(schema, root_schema)
        if isinstance(schema.get("enum"), list):
            return True
        return schema_type(schema) in {"integer", "number", "boolean"}

    def _null_wins(
        self, null_count: int, best_non_null_support: int, nullable: bool
    ) -> bool:
        if not nullable or null_count <= 0:
            return False
        if null_count > best_non_null_support:
            return True
        return self.config.null_wins_ties and null_count == best_non_null_support

    def _empty_value_for_schema(self, schema: JsonDict, root_schema: JsonDict) -> Any:
        schema, nullable = unwrap_nullable_schema(schema, root_schema)
        schema = deref(schema, root_schema)
        if nullable:
            return None
        current_type = schema_type(schema)
        if current_type == "array":
            return []
        if current_type == "object":
            return {}
        return None
