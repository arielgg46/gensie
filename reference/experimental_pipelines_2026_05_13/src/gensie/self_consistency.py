from __future__ import annotations

import json
import math
import os
import re
import unicodedata
from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from gensie.schema_enrichment import _deref, _resolve_local_ref


JsonDict = Dict[str, Any]


def _normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _tokens(value: str) -> List[str]:
    return re.findall(r"\w+", _normalize_text(value), flags=re.UNICODE)


def _counter_f1(a: Iterable[str], b: Iterable[str]) -> float:
    ca = Counter(a)
    cb = Counter(b)
    if not ca and not cb:
        return 1.0
    if not ca or not cb:
        return 0.0
    overlap = sum((ca & cb).values())
    precision = overlap / sum(ca.values())
    recall = overlap / sum(cb.values())
    return 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)


def _char_ngrams(value: str, n: int) -> List[str]:
    value = _normalize_text(value)
    if not value:
        return []
    if len(value) <= n:
        return [value]
    return [value[i : i + n] for i in range(len(value) - n + 1)]


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    ma = math.sqrt(sum(x * x for x in a))
    mb = math.sqrt(sum(y * y for y in b))
    if ma == 0 or mb == 0:
        return 0.0
    return max(0.0, dot / (ma * mb))


class StringSimilarity(ABC):
    """Strategy interface for comparing free-text values."""

    name = "base"

    @abstractmethod
    def similarity(self, a: str, b: str) -> float:
        pass


@dataclass
class LexicalStringSimilarity(StringSimilarity):
    """Small, dependency-free text similarity useful as a baseline ablation."""

    exact_weight: float = 0.15
    token_weight: float = 0.45
    char_weight: float = 0.40
    char_n: int = 3

    name: str = "lexical"

    def similarity(self, a: str, b: str) -> float:
        na = _normalize_text(a)
        nb = _normalize_text(b)
        if na == nb:
            return 1.0

        exact = 1.0 if na == nb else 0.0
        token = _counter_f1(_tokens(a), _tokens(b))
        char = _counter_f1(_char_ngrams(a, self.char_n), _char_ngrams(b, self.char_n))
        score = (
            self.exact_weight * exact
            + self.token_weight * token
            + self.char_weight * char
        )
        return max(0.0, min(1.0, score))


class FastEmbedStringSimilarity(StringSimilarity):
    """
    Optional embedding-backed similarity.

    The model is loaded lazily. If fastembed or the model files are unavailable,
    the strategy falls back to the lexical scorer instead of breaking inference.
    """

    name = "fastembed"

    def __init__(
        self,
        *,
        model_name: str = "BAAI/bge-small-en-v1.5",
        embedding_weight: float = 0.60,
        lexical: Optional[StringSimilarity] = None,
    ):
        self.model_name = model_name
        self.embedding_weight = embedding_weight
        self.lexical = lexical or LexicalStringSimilarity()
        self._model: Any = None
        self._load_failed = False
        self._cache: Dict[str, List[float]] = {}

    def _load_model(self) -> Any:
        if self._load_failed:
            return None
        if self._model is not None:
            return self._model
        try:
            from fastembed import TextEmbedding

            self._model = TextEmbedding(model_name=self.model_name)
        except Exception:
            self._load_failed = True
            self._model = None
        return self._model

    def _embed(self, value: str) -> Optional[List[float]]:
        key = _normalize_text(value)
        if key in self._cache:
            return self._cache[key]
        model = self._load_model()
        if model is None:
            return None
        try:
            embedding = next(iter(model.embed([value])))
        except Exception:
            self._load_failed = True
            return None
        vector = embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)
        self._cache[key] = vector
        return vector

    def similarity(self, a: str, b: str) -> float:
        lexical_score = self.lexical.similarity(a, b)
        va = self._embed(a)
        vb = self._embed(b)
        if va is None or vb is None:
            return lexical_score
        embedding_score = _cosine(va, vb)
        score = (
            self.embedding_weight * embedding_score
            + (1.0 - self.embedding_weight) * lexical_score
        )
        return max(0.0, min(1.0, score))


def build_string_similarity_from_env() -> StringSimilarity:
    mode = os.getenv("GENSIE_SC_STRING_SIMILARITY", "lexical").strip().lower()
    lexical = LexicalStringSimilarity()
    if mode in {"fastembed", "embedding", "hybrid"}:
        model_name = os.getenv("GENSIE_SC_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
        raw_weight = os.getenv("GENSIE_SC_EMBEDDING_WEIGHT", "0.60")
        try:
            embedding_weight = float(raw_weight)
        except ValueError:
            embedding_weight = 0.60
        return FastEmbedStringSimilarity(
            model_name=model_name,
            embedding_weight=embedding_weight,
            lexical=lexical,
        )
    return lexical


@dataclass
class SelfConsistencyConfig:
    """Tunable knobs for schema-aware self-consistency."""

    scalar_string_threshold: float = 0.78
    array_string_threshold: float = 0.78
    object_item_threshold: float = 0.62
    null_wins_ties: bool = False
    simple_item_support_floor: int = 2
    object_item_support_floor: int = 2
    support_ratios: Tuple[float, ...] = (0.40, 0.50, 0.60)
    include_greedy_array_candidate: bool = True
    include_threshold_array_candidates: bool = True
    include_original_array_candidates: bool = False
    optional_property_support_ratio: float = 0.50
    intra_trial_dedupe_threshold: float = 0.96
    use_identity_clustering: bool = True
    identity_min_score: float = 8.0
    identity_min_margin: float = 3.0
    identity_string_threshold: float = 0.62
    array_selector_mode: str = "recall_biased_mbr"
    recall_mbr_tolerance: float = 0.06


@dataclass
class TrialBudgetConfig:
    """Per-task cap for how many self-consistency samples to draw."""

    max_trials: int = 12
    min_trials: int = 1
    dynamic_trials: bool = True
    token_budget: int = 32000
    token_budget_ratio: float = 0.85
    time_budget_s: float = 60.0
    time_budget_ratio: float = 0.85
    completion_token_safety_factor: float = 1.5
    time_safety_factor: float = 1.15
    chars_per_token: float = 4.0
    inter_trial_delay_s: float = 0.0


@dataclass
class TrialBudgetEstimate:
    allowed_trials: int
    prompt_tokens_per_trial: int
    completion_tokens_per_trial: int
    seconds_per_trial: float
    allowed_by_tokens: int
    allowed_by_time: int
    token_budget_effective: int
    time_budget_effective_s: float


class TrialBudgetPlanner:
    """Estimate a per-task self-consistency sample count from observed usage."""

    def __init__(self, config: Optional[TrialBudgetConfig] = None):
        self.config = config or TrialBudgetConfig()

    def estimate_tokens_from_text(self, text: str) -> int:
        chars_per_token = max(self.config.chars_per_token, 1.0)
        return max(1, math.ceil(len(text) / chars_per_token))

    def estimate_prompt_tokens(
        self,
        *,
        messages: Sequence[JsonDict],
        response_format: JsonDict,
    ) -> int:
        text = json.dumps(
            {
                "messages": messages,
                "response_format": response_format,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        return self.estimate_tokens_from_text(text)

    def estimate(
        self,
        *,
        prompt_tokens: Optional[int],
        prompt_token_fallback: int,
        completion_token_samples: Sequence[int],
        trial_duration_samples_s: Sequence[float],
    ) -> TrialBudgetEstimate:
        cfg = self.config
        max_trials = max(cfg.max_trials, 1)
        min_trials = max(1, min(cfg.min_trials, max_trials))

        prompt_per_trial = max(prompt_tokens or prompt_token_fallback, 1)
        if completion_token_samples:
            completion_base = max(completion_token_samples)
        else:
            completion_base = max(1, math.ceil(prompt_per_trial * 0.15))
        completion_per_trial = max(
            1, math.ceil(completion_base * cfg.completion_token_safety_factor)
        )

        if trial_duration_samples_s:
            duration_base = max(trial_duration_samples_s)
        else:
            duration_base = 0.0
        duration_base = max(duration_base, cfg.inter_trial_delay_s)
        seconds_per_trial = max(0.001, duration_base * cfg.time_safety_factor)

        token_budget_effective = max(1, math.floor(cfg.token_budget * cfg.token_budget_ratio))
        time_budget_effective_s = max(0.001, cfg.time_budget_s * cfg.time_budget_ratio)

        tokens_per_trial = prompt_per_trial + completion_per_trial
        allowed_by_tokens = max(1, token_budget_effective // tokens_per_trial)
        allowed_by_time = max(1, math.floor(time_budget_effective_s / seconds_per_trial))

        if cfg.dynamic_trials:
            allowed = min(max_trials, allowed_by_tokens, allowed_by_time)
            allowed = max(min_trials, allowed)
            allowed = min(allowed, max_trials)
        else:
            allowed = max_trials

        return TrialBudgetEstimate(
            allowed_trials=allowed,
            prompt_tokens_per_trial=prompt_per_trial,
            completion_tokens_per_trial=completion_per_trial,
            seconds_per_trial=seconds_per_trial,
            allowed_by_tokens=allowed_by_tokens,
            allowed_by_time=allowed_by_time,
            token_budget_effective=token_budget_effective,
            time_budget_effective_s=time_budget_effective_s,
        )


@dataclass(frozen=True)
class ValueCandidate:
    value: Any
    trial_index: int
    item_index: int = 0


@dataclass
class ValueCluster:
    members: List[ValueCandidate] = field(default_factory=list)

    @property
    def support(self) -> int:
        return len({m.trial_index for m in self.members})

    @property
    def first_position(self) -> Tuple[int, int]:
        if not self.members:
            return (10**9, 10**9)
        return min((m.trial_index, m.item_index) for m in self.members)


@dataclass(frozen=True)
class IdentityFieldCandidate:
    name: str
    score: float
    reasons: Tuple[str, ...]


@dataclass(frozen=True)
class IdentityFieldDecision:
    field_name: Optional[str]
    score: float
    margin: float
    confidence: str
    candidates: Tuple[IdentityFieldCandidate, ...]


class IdentityFieldSelector(ABC):
    """Strategy interface for finding object item identity fields."""

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
    """
    Detects identity-like fields from schema names and descriptions.

    This is intentionally schema-driven and swappable. It prefers required
    free-text fields such as text/name/reaction/symptom/ingredient, and avoids
    attribute-like fields such as labels, categories, probabilities, and units.
    """

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
        schema, _ = _unwrap_nullable_schema(schema, root_schema)
        schema = _deref(schema, root_schema)
        props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
        required = set(schema.get("required") or [])
        candidates: List[IdentityFieldCandidate] = []

        for name, prop_schema in props.items():
            if not isinstance(prop_schema, dict):
                continue
            prop_schema, _ = _unwrap_nullable_schema(prop_schema, root_schema)
            prop_schema = _deref(prop_schema, root_schema)
            prop_type = _schema_type(prop_schema)
            is_enum = isinstance(prop_schema.get("enum"), list)
            lname = name.lower()
            desc = (prop_schema.get("description") or "").lower()
            score = 0.0
            reasons: List[str] = []

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

        candidates.sort(key=lambda c: (-c.score, c.name))
        best = candidates[0] if candidates else None
        runner_up_score = candidates[1].score if len(candidates) > 1 else 0.0
        margin = (best.score - runner_up_score) if best else 0.0
        if best and best.score >= config.identity_min_score and margin >= config.identity_min_margin:
            confidence = "high"
            field_name: Optional[str] = best.name
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
    """Explicit no-op selector useful for ablations."""

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


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _schema_type(schema: JsonDict) -> str:
    schema_type = schema.get("type")
    if isinstance(schema_type, str):
        return schema_type
    if isinstance(schema_type, list):
        non_null = [t for t in schema_type if t != "null"]
        if len(non_null) == 1 and isinstance(non_null[0], str):
            return non_null[0]
    if "enum" in schema:
        return "enum"
    return ""


def _unwrap_nullable_schema(schema: JsonDict, root_schema: JsonDict) -> Tuple[JsonDict, bool]:
    schema = _deref(schema, root_schema)

    any_of = schema.get("anyOf")
    if isinstance(any_of, list):
        non_null_alts: List[JsonDict] = []
        has_null = False
        for alt in any_of:
            if not isinstance(alt, dict):
                return schema, False
            alt = _deref(alt, root_schema)
            if alt.get("type") == "null":
                has_null = True
            else:
                non_null_alts.append(alt)
        if has_null and len(non_null_alts) == 1:
            inner = dict(non_null_alts[0])
            for key in ("description", "title", "default", "examples"):
                if key in schema and key not in inner:
                    inner[key] = schema[key]
            return _deref(inner, root_schema), True

    schema_type = schema.get("type")
    if isinstance(schema_type, list) and "null" in schema_type:
        non_null_types = [t for t in schema_type if t != "null"]
        if len(non_null_types) == 1:
            inner = dict(schema)
            inner["type"] = non_null_types[0]
            return inner, True

    return schema, False


def _is_required(schema: JsonDict, field_name: str) -> bool:
    required = schema.get("required")
    return isinstance(required, list) and field_name in required


class SchemaValueSimilarity:
    """Schema-aware value comparator used by clustering and MBR selectors."""

    def __init__(self, string_similarity: StringSimilarity):
        self.string_similarity = string_similarity

    def similarity(self, a: Any, b: Any, schema: JsonDict, root_schema: JsonDict) -> float:
        if a == b:
            return 1.0
        if a is None or b is None:
            return 0.0

        schema, _ = _unwrap_nullable_schema(schema, root_schema)
        schema = _deref(schema, root_schema)
        enum = schema.get("enum")
        schema_type = _schema_type(schema)

        if isinstance(enum, list):
            return 1.0 if a == b else 0.0
        if schema_type in {"integer", "number", "boolean"}:
            return 1.0 if a == b else 0.0
        if schema_type == "string":
            if not isinstance(a, str) or not isinstance(b, str):
                return 0.0
            return self.string_similarity.similarity(a, b)
        if schema_type == "object":
            return self.object_similarity(a, b, schema, root_schema)
        if schema_type == "array":
            item_schema = schema.get("items") if isinstance(schema.get("items"), dict) else {}
            if "$ref" in item_schema:
                item_schema = _resolve_local_ref(root_schema, item_schema["$ref"])
            if not isinstance(a, list) or not isinstance(b, list):
                return 0.0
            return self.array_similarity(a, b, item_schema, root_schema)

        return 1.0 if _canonical_json(a) == _canonical_json(b) else 0.0

    def object_similarity(self, a: Any, b: Any, schema: JsonDict, root_schema: JsonDict) -> float:
        if not isinstance(a, dict) or not isinstance(b, dict):
            return 0.0
        props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
        if not props:
            return 1.0 if _canonical_json(a) == _canonical_json(b) else 0.0

        total = 0.0
        weight_sum = 0.0
        for name, child_schema in props.items():
            if not isinstance(child_schema, dict):
                continue
            has_a = name in a
            has_b = name in b
            if not has_a and not has_b:
                continue
            weight = self._field_weight(child_schema, root_schema)
            weight_sum += weight
            if has_a and has_b:
                total += weight * self.similarity(a[name], b[name], child_schema, root_schema)
        return total / weight_sum if weight_sum else 1.0

    def array_similarity(
        self,
        a: Sequence[Any],
        b: Sequence[Any],
        item_schema: JsonDict,
        root_schema: JsonDict,
    ) -> float:
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0

        matrix = [
            [self.similarity(aa, bb, item_schema, root_schema) for bb in b]
            for aa in a
        ]
        used_a: set[int] = set()
        used_b: set[int] = set()
        matches = 0.0

        while len(used_a) < len(a) and len(used_b) < len(b):
            best = -1.0
            best_pair = (-1, -1)
            for i in range(len(a)):
                if i in used_a:
                    continue
                for j in range(len(b)):
                    if j in used_b:
                        continue
                    if matrix[i][j] > best:
                        best = matrix[i][j]
                        best_pair = (i, j)
            if best < 0:
                break
            matches += best
            used_a.add(best_pair[0])
            used_b.add(best_pair[1])

        denom = len(a) + len(b) - matches
        return matches / denom if denom > 0 else 0.0

    def _field_weight(self, schema: JsonDict, root_schema: JsonDict) -> float:
        schema, _ = _unwrap_nullable_schema(schema, root_schema)
        schema = _deref(schema, root_schema)
        if schema.get("enum") is not None:
            return 1.10
        schema_type = _schema_type(schema)
        if schema_type == "string":
            return 1.20
        if schema_type in {"integer", "number", "boolean"}:
            return 1.10
        if schema_type == "array":
            return 0.90
        return 1.00


def _medoid(
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
        similarity_func: Optional[Callable[[Any, Any], float]] = None,
    ) -> List[ValueCluster]:
        if exact:
            grouped: Dict[str, List[ValueCandidate]] = defaultdict(list)
            for candidate in candidates:
                grouped[_canonical_json(candidate.value)].append(candidate)
            clusters = [ValueCluster(members=members) for members in grouped.values()]
            clusters.sort(key=lambda c: (-c.support, c.first_position))
            return clusters

        clusters: List[ValueCluster] = []
        compare = similarity_func or (
            lambda a, b: self.comparator.similarity(a, b, schema, root_schema)
        )
        for candidate in candidates:
            best_cluster: Optional[ValueCluster] = None
            best_score = -1.0
            for cluster in clusters:
                if any(m.trial_index == candidate.trial_index for m in cluster.members):
                    continue
                score = max(compare(candidate.value, member.value) for member in cluster.members)
                if score >= threshold and score > best_score:
                    best_cluster = cluster
                    best_score = score
            if best_cluster is None:
                clusters.append(ValueCluster(members=[candidate]))
            else:
                best_cluster.members.append(candidate)

        clusters.sort(key=lambda c: (-c.support, c.first_position))
        return clusters


class ArrayCandidateBuilder(ABC):
    """Build possible consensus arrays from item clusters."""

    @abstractmethod
    def build(
        self,
        clusters: Sequence[ValueCluster],
        observed_arrays: Sequence[List[Any]],
        item_schema: JsonDict,
        root_schema: JsonDict,
        aggregator: "SchemaAwareSelfConsistencyAggregator",
    ) -> List[List[Any]]:
        pass


@dataclass
class SupportThresholdArrayCandidateBuilder(ArrayCandidateBuilder):
    support_floors: Sequence[int]

    def build(
        self,
        clusters: Sequence[ValueCluster],
        observed_arrays: Sequence[List[Any]],
        item_schema: JsonDict,
        root_schema: JsonDict,
        aggregator: "SchemaAwareSelfConsistencyAggregator",
    ) -> List[List[Any]]:
        candidates: List[List[Any]] = []
        seen: set[str] = set()
        for floor in self.support_floors:
            items = [
                aggregator.aggregate_cluster(cluster, item_schema, root_schema)
                for cluster in clusters
                if cluster.support >= floor
            ]
            key = _canonical_json(items)
            if key not in seen:
                seen.add(key)
                candidates.append(items)
        return candidates


class GreedyMbrArrayCandidateBuilder(ArrayCandidateBuilder):
    """Construct a consensus array by adding clusters that improve expected utility."""

    def build(
        self,
        clusters: Sequence[ValueCluster],
        observed_arrays: Sequence[List[Any]],
        item_schema: JsonDict,
        root_schema: JsonDict,
        aggregator: "SchemaAwareSelfConsistencyAggregator",
    ) -> List[List[Any]]:
        selected: List[ValueCluster] = []
        selected_values: List[Any] = []
        best_score = aggregator.score_array_candidate(
            selected_values, observed_arrays, item_schema, root_schema
        )

        ordered = sorted(clusters, key=lambda c: (-c.support, c.first_position))
        improved = True
        while improved:
            improved = False
            best_next: Optional[Tuple[float, ValueCluster, Any]] = None
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
        candidates: Sequence[List[Any]],
        observed_arrays: Sequence[List[Any]],
        item_schema: JsonDict,
        root_schema: JsonDict,
        aggregator: "SchemaAwareSelfConsistencyAggregator",
    ) -> List[Any]:
        pass


class MbrArrayCandidateSelector(ArrayCandidateSelector):
    """Pick the candidate with highest expected similarity to sampled arrays."""

    def select(
        self,
        candidates: Sequence[List[Any]],
        observed_arrays: Sequence[List[Any]],
        item_schema: JsonDict,
        root_schema: JsonDict,
        aggregator: "SchemaAwareSelfConsistencyAggregator",
    ) -> List[Any]:
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


@dataclass
class RecallBiasedMbrArrayCandidateSelector(ArrayCandidateSelector):
    """
    Pick the longest candidate that is close enough to the MBR optimum.

    Pure MBR is conservative for extraction arrays: an item that appears in a
    minority-but-real set of trials can be dropped because leaving it out is
    slightly more central. This selector keeps the MBR guardrail, then breaks
    near-ties toward recall.
    """

    score_tolerance: float = 0.06

    def select(
        self,
        candidates: Sequence[List[Any]],
        observed_arrays: Sequence[List[Any]],
        item_schema: JsonDict,
        root_schema: JsonDict,
        aggregator: "SchemaAwareSelfConsistencyAggregator",
    ) -> List[Any]:
        if not candidates:
            return []

        scored: List[Tuple[int, List[Any], float]] = []
        for index, candidate in enumerate(candidates):
            score = aggregator.score_array_candidate(
                candidate, observed_arrays, item_schema, root_schema
            )
            scored.append((index, list(candidate), score))

        best_score = max(score for _, _, score in scored)
        min_score = best_score - max(self.score_tolerance, 0.0)
        eligible = [
            entry
            for entry in scored
            if entry[2] >= min_score
        ]
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


class SchemaAwareSelfConsistencyAggregator:
    """
    Field-wise self-consistency for GenSIE outputs.

    Arrays are aggregated item-wise. Candidate arrays are constructed from item
    clusters and selected by expected schema-aware similarity to the sampled
    arrays, so no original trial has to be "the" selected array.
    """

    def __init__(
        self,
        *,
        config: Optional[SelfConsistencyConfig] = None,
        string_similarity: Optional[StringSimilarity] = None,
        array_selector: Optional[ArrayCandidateSelector] = None,
        identity_selector: Optional[IdentityFieldSelector] = None,
    ):
        self.config = config or SelfConsistencyConfig()
        self.string_similarity = string_similarity or build_string_similarity_from_env()
        self.comparator = SchemaValueSimilarity(self.string_similarity)
        self.clusterer = ItemClusterer(self.comparator)
        self.array_selector = array_selector or build_array_selector_from_config(self.config)
        if identity_selector is not None:
            self.identity_selector = identity_selector
        elif self.config.use_identity_clustering:
            self.identity_selector = HeuristicIdentityFieldSelector()
        else:
            self.identity_selector = NoIdentityFieldSelector()
        self._identity_decision_cache: Dict[str, IdentityFieldDecision] = {}

    def aggregate(self, outputs: Sequence[JsonDict], schema: JsonDict) -> JsonDict:
        root_schema = schema
        schema, _ = _unwrap_nullable_schema(schema, root_schema)
        schema = _deref(schema, root_schema)
        if schema.get("type") != "object":
            value = self.aggregate_value(list(outputs), schema, root_schema)
            return value if isinstance(value, dict) else {"value": value}
        return self.aggregate_object(list(outputs), schema, root_schema, root=True)

    def aggregate_with_diagnostics(
        self, outputs: Sequence[JsonDict], schema: JsonDict
    ) -> Tuple[JsonDict, JsonDict]:
        final_output = self.aggregate(outputs, schema)
        root_schema = schema
        schema, _ = _unwrap_nullable_schema(schema, root_schema)
        schema = _deref(schema, root_schema)
        diagnostics = {
            "strategy": "schema_aware_self_consistency",
            "sample_count": len(outputs),
            "string_similarity": self.string_similarity.name,
            "array_selector": self.array_selector.__class__.__name__,
            "identity_selector": self.identity_selector.name,
            "config": self.config.__dict__,
            "fields": self.diagnose_object(
                list(outputs), schema, root_schema, final_output, root=True
            )
            if schema.get("type") == "object"
            else {},
        }
        return final_output, diagnostics

    def aggregate_value(
        self,
        values: Sequence[Any],
        schema: JsonDict,
        root_schema: JsonDict,
    ) -> Any:
        schema, nullable = _unwrap_nullable_schema(schema, root_schema)
        schema = _deref(schema, root_schema)
        non_null = [ValueCandidate(v, i) for i, v in enumerate(values) if v is not None]
        null_count = len(values) - len(non_null)

        if not non_null:
            return None if nullable else self._empty_value_for_schema(schema, root_schema)

        schema_type = _schema_type(schema)
        if schema_type == "object":
            best_non_null_support = len(non_null)
            if self._null_wins(null_count, best_non_null_support, nullable):
                return None
            return self.aggregate_object(
                [c.value for c in non_null if isinstance(c.value, dict)],
                schema,
                root_schema,
            )

        if schema_type == "array":
            best_non_null_support = len(non_null)
            if self._null_wins(null_count, best_non_null_support, nullable):
                return None
            arrays = [c.value for c in non_null if isinstance(c.value, list)]
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
            if not present_values and not _is_required(schema, name) and not root:
                continue
            if not root and not _is_required(schema, name):
                needed = max(1, math.ceil(len(objects) * self.config.optional_property_support_ratio))
                if len(present_values) < needed:
                    continue
            out[name] = self.aggregate_value(present_values, child_schema, root_schema)
        return out

    def aggregate_array(
        self,
        arrays: Sequence[List[Any]],
        schema: JsonDict,
        root_schema: JsonDict,
    ) -> List[Any]:
        arrays = [array for array in arrays if isinstance(array, list)]
        if not arrays:
            return []

        item_schema = schema.get("items") if isinstance(schema.get("items"), dict) else {}
        if "$ref" in item_schema:
            item_schema = _resolve_local_ref(root_schema, item_schema["$ref"])
        item_schema, _ = _unwrap_nullable_schema(item_schema, root_schema)
        item_schema = _deref(item_schema, root_schema)

        candidates = self._array_item_candidates(arrays, item_schema, root_schema)
        if not candidates:
            return []

        clusters = self.cluster_array_items(candidates, item_schema, root_schema)
        candidate_arrays = self.build_array_candidates(
            clusters, arrays, item_schema, root_schema
        )

        return self.array_selector.select(candidate_arrays, arrays, item_schema, root_schema, self)

    def aggregate_cluster(
        self,
        cluster: ValueCluster,
        schema: JsonDict,
        root_schema: JsonDict,
    ) -> Any:
        schema, nullable = _unwrap_nullable_schema(schema, root_schema)
        schema = _deref(schema, root_schema)
        values = [member.value for member in cluster.members]
        if not values:
            return None if nullable else self._empty_value_for_schema(schema, root_schema)

        schema_type = _schema_type(schema)
        if schema_type == "object":
            return self.aggregate_object(
                [value for value in values if isinstance(value, dict)],
                schema,
                root_schema,
            )
        if schema_type == "array":
            return self.aggregate_array(
                [value for value in values if isinstance(value, list)],
                schema,
                root_schema,
            )
        return _medoid(cluster.members, schema, root_schema, self.comparator)

    def cluster_scalar_candidates(
        self,
        candidates: Sequence[ValueCandidate],
        schema: JsonDict,
        root_schema: JsonDict,
    ) -> List[ValueCluster]:
        schema, _ = _unwrap_nullable_schema(schema, root_schema)
        schema = _deref(schema, root_schema)
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
    ) -> List[ValueCluster]:
        exact = self._uses_exact_matching(item_schema, root_schema)
        threshold = self._array_item_threshold(item_schema, root_schema)
        similarity_func = None
        identity_decision = self.select_identity_field(item_schema, root_schema)
        if identity_decision.field_name:
            threshold = self.config.identity_string_threshold
            similarity_func = self._identity_similarity_func(
                item_schema,
                root_schema,
                identity_decision.field_name,
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
        self,
        item_schema: JsonDict,
        root_schema: JsonDict,
    ) -> IdentityFieldDecision:
        item_schema, _ = _unwrap_nullable_schema(item_schema, root_schema)
        item_schema = _deref(item_schema, root_schema)
        if _schema_type(item_schema) != "object":
            return IdentityFieldDecision(
                field_name=None,
                score=0.0,
                margin=0.0,
                confidence="not_applicable",
                candidates=(),
            )

        cache_key = _canonical_json(item_schema)
        cached = self._identity_decision_cache.get(cache_key)
        if cached is not None:
            return cached

        decision = self.identity_selector.select(
            item_schema,
            root_schema,
            config=self.config,
        )
        if not self.config.use_identity_clustering:
            decision = NoIdentityFieldSelector().select(
                item_schema,
                root_schema,
                config=self.config,
            )
        self._identity_decision_cache[cache_key] = decision
        return decision

    def _identity_similarity_func(
        self,
        item_schema: JsonDict,
        root_schema: JsonDict,
        field_name: str,
    ) -> Callable[[Any, Any], float]:
        item_schema, _ = _unwrap_nullable_schema(item_schema, root_schema)
        item_schema = _deref(item_schema, root_schema)
        props = item_schema.get("properties") if isinstance(item_schema.get("properties"), dict) else {}
        field_schema = props.get(field_name) if isinstance(props.get(field_name), dict) else {}

        def compare(a: Any, b: Any) -> float:
            if not isinstance(a, dict) or not isinstance(b, dict):
                return self.comparator.similarity(a, b, item_schema, root_schema)
            if field_name not in a or field_name not in b:
                return self.comparator.similarity(a, b, item_schema, root_schema)
            return self.comparator.similarity(
                a[field_name],
                b[field_name],
                field_schema,
                root_schema,
            )

        return compare

    def score_array_candidate(
        self,
        candidate: Sequence[Any],
        observed_arrays: Sequence[List[Any]],
        item_schema: JsonDict,
        root_schema: JsonDict,
    ) -> float:
        if not observed_arrays:
            return 0.0
        return sum(
            self.comparator.array_similarity(candidate, observed, item_schema, root_schema)
            for observed in observed_arrays
        ) / len(observed_arrays)

    def build_array_candidates(
        self,
        clusters: Sequence[ValueCluster],
        observed_arrays: Sequence[List[Any]],
        item_schema: JsonDict,
        root_schema: JsonDict,
    ) -> List[List[Any]]:
        support_floors = self._support_floors(len(observed_arrays), item_schema, root_schema)
        builders: List[ArrayCandidateBuilder] = []
        if self.config.include_threshold_array_candidates:
            builders.append(SupportThresholdArrayCandidateBuilder(support_floors))
        if self.config.include_greedy_array_candidate:
            builders.append(GreedyMbrArrayCandidateBuilder())

        candidate_arrays: List[List[Any]] = []
        seen: set[str] = set()
        for builder in builders:
            for candidate in builder.build(
                clusters, observed_arrays, item_schema, root_schema, self
            ):
                key = _canonical_json(candidate)
                if key not in seen:
                    seen.add(key)
                    candidate_arrays.append(candidate)

        if self.config.include_original_array_candidates:
            for array in observed_arrays:
                key = _canonical_json(array)
                if key not in seen:
                    seen.add(key)
                    candidate_arrays.append(array)
        return candidate_arrays

    def diagnose_object(
        self,
        objects: Sequence[JsonDict],
        schema: JsonDict,
        root_schema: JsonDict,
        final_object: Any,
        *,
        root: bool = False,
    ) -> JsonDict:
        if not isinstance(final_object, dict):
            final_object = {}
        objects = [obj for obj in objects if isinstance(obj, dict)]
        props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
        out: JsonDict = {}
        for name, child_schema in props.items():
            if not isinstance(child_schema, dict):
                continue
            present_values = [obj[name] for obj in objects if name in obj]
            out[name] = self.diagnose_value(
                present_values,
                child_schema,
                root_schema,
                final_object.get(name),
                required=_is_required(schema, name) or root,
            )
        return out

    def diagnose_value(
        self,
        values: Sequence[Any],
        schema: JsonDict,
        root_schema: JsonDict,
        final_value: Any,
        *,
        required: bool,
    ) -> JsonDict:
        original_sample_count = len(values)
        schema, nullable = _unwrap_nullable_schema(schema, root_schema)
        schema = _deref(schema, root_schema)
        schema_type = _schema_type(schema)
        null_count = sum(1 for value in values if value is None)
        non_null_values = [value for value in values if value is not None]
        base: JsonDict = {
            "schema_type": schema_type or "any",
            "required": required,
            "nullable": nullable,
            "sample_count": original_sample_count,
            "null_count": null_count,
            "final_value": final_value,
        }

        if schema_type == "object":
            base["strategy"] = "recursive_object_consensus"
            base["fields"] = self.diagnose_object(
                [value for value in non_null_values if isinstance(value, dict)],
                schema,
                root_schema,
                final_value,
            )
            return base

        if schema_type == "array":
            arrays = [value for value in non_null_values if isinstance(value, list)]
            item_schema = schema.get("items") if isinstance(schema.get("items"), dict) else {}
            if "$ref" in item_schema:
                item_schema = _resolve_local_ref(root_schema, item_schema["$ref"])
            item_schema, _ = _unwrap_nullable_schema(item_schema, root_schema)
            item_schema = _deref(item_schema, root_schema)
            item_type = _schema_type(item_schema) or "any"
            item_candidates = self._array_item_candidates(arrays, item_schema, root_schema)
            clusters = self.cluster_array_items(item_candidates, item_schema, root_schema)
            support_floors = self._support_floors(len(arrays), item_schema, root_schema)
            candidate_arrays = self.build_array_candidates(
                clusters, arrays, item_schema, root_schema
            )
            identity_decision = self.select_identity_field(item_schema, root_schema)
            candidate_scores = [
                {
                    "index": index,
                    "length": len(candidate),
                    "score": round(
                        self.score_array_candidate(candidate, arrays, item_schema, root_schema),
                        6,
                    ),
                    "value": candidate,
                }
                for index, candidate in enumerate(candidate_arrays)
            ]
            selected_index = None
            for entry in candidate_scores:
                if _canonical_json(entry["value"]) == _canonical_json(final_value or []):
                    selected_index = entry["index"]
                    break

            threshold = (
                self.config.identity_string_threshold
                if identity_decision.field_name
                else self._array_item_threshold(item_schema, root_schema)
            )
            final_items = final_value if isinstance(final_value, list) else []
            base.update(
                {
                    "strategy": f"itemwise_array_consensus_{self.config.array_selector_mode}",
                    "item_schema_type": item_type,
                    "array_selector": self.array_selector.__class__.__name__,
                    "observed_lengths": [len(array) for array in arrays],
                    "final_length": len(final_items),
                    "support_floors": support_floors,
                    "cluster_threshold": threshold,
                    "cluster_similarity": (
                        "identity_field"
                        if identity_decision.field_name
                        else "schema_value"
                    ),
                    "identity_field_decision": self._identity_decision_diagnostic(
                        identity_decision
                    ),
                    "cluster_count": len(clusters),
                    "clusters": [
                        self._cluster_diagnostic(
                            cluster,
                            item_schema,
                            root_schema,
                            final_items,
                            threshold=threshold,
                        )
                        for cluster in clusters
                    ],
                    "candidate_arrays": candidate_scores,
                    "selected_candidate_index": selected_index,
                }
            )
            return base

        candidates = [
            ValueCandidate(value, trial_index)
            for trial_index, value in enumerate(values)
            if value is not None
        ]
        clusters = self.cluster_scalar_candidates(candidates, schema, root_schema)
        base.update(
            {
                "strategy": "scalar_cluster_medoid",
                "cluster_threshold": (
                    1.0
                    if self._uses_exact_matching(schema, root_schema)
                    else self.config.scalar_string_threshold
                ),
                "clusters": [
                    self._cluster_diagnostic(
                        cluster,
                        schema,
                        root_schema,
                        [final_value],
                        threshold=1.0
                        if self._uses_exact_matching(schema, root_schema)
                        else self.config.scalar_string_threshold,
                    )
                    for cluster in clusters
                ],
            }
        )
        return base

    def _identity_decision_diagnostic(
        self,
        decision: IdentityFieldDecision,
    ) -> JsonDict:
        return {
            "field_name": decision.field_name,
            "score": round(decision.score, 6),
            "margin": round(decision.margin, 6),
            "confidence": decision.confidence,
            "candidates": [
                {
                    "name": candidate.name,
                    "score": round(candidate.score, 6),
                    "reasons": list(candidate.reasons),
                }
                for candidate in decision.candidates
            ],
        }

    def _cluster_diagnostic(
        self,
        cluster: ValueCluster,
        schema: JsonDict,
        root_schema: JsonDict,
        final_items: Sequence[Any],
        *,
        threshold: float,
    ) -> JsonDict:
        representative = self.aggregate_cluster(cluster, schema, root_schema)
        best_final_similarity = (
            max(
                self.comparator.similarity(representative, final_item, schema, root_schema)
                for final_item in final_items
            )
            if final_items
            else 0.0
        )
        return {
            "support": cluster.support,
            "trial_indices": sorted({member.trial_index for member in cluster.members}),
            "first_position": list(cluster.first_position),
            "representative": representative,
            "included_in_final": best_final_similarity >= threshold,
            "best_final_similarity": round(best_final_similarity, 6),
            "member_values": [member.value for member in cluster.members],
        }

    def _array_item_candidates(
        self,
        arrays: Sequence[List[Any]],
        item_schema: JsonDict,
        root_schema: JsonDict,
    ) -> List[ValueCandidate]:
        out: List[ValueCandidate] = []
        for trial_index, array in enumerate(arrays):
            trial_candidates: List[ValueCandidate] = []
            for item_index, value in enumerate(array):
                trial_candidates.append(ValueCandidate(value, trial_index, item_index))
            out.extend(self._dedupe_trial_candidates(trial_candidates, item_schema, root_schema))
        return out

    def _dedupe_trial_candidates(
        self,
        candidates: Sequence[ValueCandidate],
        schema: JsonDict,
        root_schema: JsonDict,
    ) -> List[ValueCandidate]:
        kept: List[ValueCandidate] = []
        exact = self._uses_exact_matching(schema, root_schema)
        threshold = 1.0 if exact else self.config.intra_trial_dedupe_threshold
        for candidate in candidates:
            if any(
                self.comparator.similarity(candidate.value, old.value, schema, root_schema)
                >= threshold
                for old in kept
            ):
                continue
            kept.append(candidate)
        return kept

    def _support_floors(
        self,
        sample_count: int,
        item_schema: JsonDict,
        root_schema: JsonDict,
    ) -> List[int]:
        item_schema, _ = _unwrap_nullable_schema(item_schema, root_schema)
        item_schema = _deref(item_schema, root_schema)
        schema_type = _schema_type(item_schema)
        base = (
            self.config.object_item_support_floor
            if schema_type == "object"
            else self.config.simple_item_support_floor
        )
        floors = {max(1, min(sample_count, base))}
        for ratio in self.config.support_ratios:
            floors.add(max(1, min(sample_count, math.ceil(sample_count * ratio))))
        return sorted(floors)

    def _array_item_threshold(self, item_schema: JsonDict, root_schema: JsonDict) -> float:
        item_schema, _ = _unwrap_nullable_schema(item_schema, root_schema)
        item_schema = _deref(item_schema, root_schema)
        schema_type = _schema_type(item_schema)
        if schema_type == "object":
            return self.config.object_item_threshold
        if schema_type == "string":
            return self.config.array_string_threshold
        return 1.0

    def _uses_exact_matching(self, schema: JsonDict, root_schema: JsonDict) -> bool:
        schema, _ = _unwrap_nullable_schema(schema, root_schema)
        schema = _deref(schema, root_schema)
        if isinstance(schema.get("enum"), list):
            return True
        return _schema_type(schema) in {"integer", "number", "boolean"}

    def _null_wins(self, null_count: int, best_non_null_support: int, nullable: bool) -> bool:
        if not nullable or null_count <= 0:
            return False
        if null_count > best_non_null_support:
            return True
        return self.config.null_wins_ties and null_count == best_non_null_support

    def _empty_value_for_schema(self, schema: JsonDict, root_schema: JsonDict) -> Any:
        schema, nullable = _unwrap_nullable_schema(schema, root_schema)
        schema = _deref(schema, root_schema)
        if nullable:
            return None
        schema_type = _schema_type(schema)
        if schema_type == "array":
            return []
        if schema_type == "object":
            return {}
        return None
