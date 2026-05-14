from __future__ import annotations

import math
import os
import re
import unicodedata
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from gensie.aggregation.schema_utils import (
    JsonDict,
    canonical_json,
    deref_item_schema,
    schema_type,
    unwrap_nullable_schema,
)
from gensie.schemas.inspect import deref


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def tokens(value: str) -> list[str]:
    return re.findall(r"\w+", normalize_text(value), flags=re.UNICODE)


def counter_f1(a: Iterable[str], b: Iterable[str]) -> float:
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


def char_ngrams(value: str, n: int) -> list[str]:
    value = normalize_text(value)
    if not value:
        return []
    if len(value) <= n:
        return [value]
    return [value[index : index + n] for index in range(len(value) - n + 1)]


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    ma = math.sqrt(sum(x * x for x in a))
    mb = math.sqrt(sum(y * y for y in b))
    if ma == 0 or mb == 0:
        return 0.0
    return max(0.0, dot / (ma * mb))


class StringSimilarity(ABC):
    name = "base"

    @abstractmethod
    def similarity(self, a: str, b: str) -> float:
        pass


@dataclass(frozen=True)
class LexicalStringSimilarity(StringSimilarity):
    exact_weight: float = 0.15
    token_weight: float = 0.45
    char_weight: float = 0.40
    char_n: int = 3

    name: str = "lexical"

    def similarity(self, a: str, b: str) -> float:
        na = normalize_text(a)
        nb = normalize_text(b)
        if na == nb:
            return 1.0

        exact = 1.0 if na == nb else 0.0
        token = counter_f1(tokens(a), tokens(b))
        char = counter_f1(char_ngrams(a, self.char_n), char_ngrams(b, self.char_n))
        score = (
            self.exact_weight * exact
            + self.token_weight * token
            + self.char_weight * char
        )
        return max(0.0, min(1.0, score))


class FastEmbedStringSimilarity(StringSimilarity):
    name = "fastembed"

    def __init__(
        self,
        *,
        model_name: str = "BAAI/bge-small-en-v1.5",
        embedding_weight: float = 0.60,
        lexical: StringSimilarity | None = None,
    ):
        self.model_name = model_name
        self.embedding_weight = embedding_weight
        self.lexical = lexical or LexicalStringSimilarity()
        self._model: Any = None
        self._load_failed = False
        self._cache: dict[str, list[float]] = {}

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

    def _embed(self, value: str) -> list[float] | None:
        key = normalize_text(value)
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
        embedding_score = cosine(va, vb)
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
        try:
            embedding_weight = float(os.getenv("GENSIE_SC_EMBEDDING_WEIGHT", "0.60"))
        except ValueError:
            embedding_weight = 0.60
        return FastEmbedStringSimilarity(
            model_name=model_name,
            embedding_weight=embedding_weight,
            lexical=lexical,
        )
    return lexical


class SchemaValueSimilarity:
    """Schema-aware value comparator used by clustering and MBR selectors."""

    def __init__(self, string_similarity: StringSimilarity):
        self.string_similarity = string_similarity

    def similarity(
        self, a: Any, b: Any, schema: JsonDict, root_schema: JsonDict
    ) -> float:
        if a == b:
            return 1.0
        if a is None or b is None:
            return 0.0

        schema, _ = unwrap_nullable_schema(schema, root_schema)
        schema = deref(schema, root_schema)
        enum = schema.get("enum")
        current_type = schema_type(schema)

        if isinstance(enum, list):
            return 1.0 if a == b else 0.0
        if current_type in {"integer", "number", "boolean"}:
            return 1.0 if a == b else 0.0
        if current_type == "string":
            if not isinstance(a, str) or not isinstance(b, str):
                return 0.0
            return self.string_similarity.similarity(a, b)
        if current_type == "object":
            return self.object_similarity(a, b, schema, root_schema)
        if current_type == "array":
            item_schema = deref_item_schema(schema, root_schema)
            if not isinstance(a, list) or not isinstance(b, list):
                return 0.0
            return self.array_similarity(a, b, item_schema, root_schema)

        return 1.0 if canonical_json(a) == canonical_json(b) else 0.0

    def object_similarity(
        self, a: Any, b: Any, schema: JsonDict, root_schema: JsonDict
    ) -> float:
        if not isinstance(a, dict) or not isinstance(b, dict):
            return 0.0
        props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
        if not props:
            return 1.0 if canonical_json(a) == canonical_json(b) else 0.0

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
                total += weight * self.similarity(
                    a[name], b[name], child_schema, root_schema
                )
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
        schema, _ = unwrap_nullable_schema(schema, root_schema)
        schema = deref(schema, root_schema)
        if schema.get("enum") is not None:
            return 1.10
        current_type = schema_type(schema)
        if current_type == "string":
            return 1.20
        if current_type in {"integer", "number", "boolean"}:
            return 1.10
        if current_type == "array":
            return 0.90
        return 1.00
