"""FSP-RAG basado en embeddings por campo de primer nivel.

Pipeline:
1. Descompone cada `Task` en sus campos de primer nivel (`target_schema.properties`).
2. Embebe el texto `"<name> (<type>): <description>"` de cada campo con fastembed.
3. Guarda una matriz NPZ con todos los embeddings de los candidatos de `data/dev/`
   y un sidecar JSON con (task_id, field_name, type_class, text) por fila.
4. Para una query, vectoriza sus campos y construye, por cada candidato, un vector
   con dim = nº campos de la query, donde la i-ésima posición es la similitud
   coseno máxima entre el i-ésimo campo de la query y cualquier campo del candidato
   con la *misma clase de tipo*. Tipos incompatibles ⇒ 0.
5. Selecciona los dos candidatos c1, c2 que maximizan |c1+c2| + |c1-c2|
   (similares a la query y a la vez complementarios entre sí).
"""

from __future__ import annotations

import json
import os
import random
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

from gensie.fsp.examples import StructuredFspCase, canonical_json
from gensie.fsp.retrieval import (
    FspRetrievalResult,
    rank_fsp_cases,
)
from gensie.schemas.fields import FieldInfo, parse_schema_fields
from gensie.schemas.inspect import JsonDict
from gensie.task import Task


DEFAULT_EMBED_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_DATA_DIR = Path("data/dev")
DEFAULT_INDEX_DIR = Path("data/fsp_index")
DEFAULT_INDEX_PATH = DEFAULT_INDEX_DIR / "dev_field_embeddings.npz"
DEFAULT_META_PATH = DEFAULT_INDEX_DIR / "dev_field_embeddings.meta.json"
DEFAULT_INDEX_PATH_P25 = DEFAULT_INDEX_DIR / "dev_field_embeddings_p25.npz"
DEFAULT_META_PATH_P25 = DEFAULT_INDEX_DIR / "dev_field_embeddings_p25.meta.json"
DEFAULT_INDEX_PATH_P50 = DEFAULT_INDEX_DIR / "dev_field_embeddings_p50.npz"
DEFAULT_META_PATH_P50 = DEFAULT_INDEX_DIR / "dev_field_embeddings_p50.meta.json"
DEFAULT_CASE_INDEX_PATH = DEFAULT_INDEX_DIR / "fsp_case_embeddings.npz"
DEFAULT_CASE_META_PATH = DEFAULT_INDEX_DIR / "fsp_case_embeddings.meta.json"
DEFAULT_SAME_SCHEMA_SIMILARITY_THRESHOLD = 0.6
PARTIAL_INDEX_SEED = 42
PARTIAL_COVERED_SCHEMA_TYPES = frozenset(
    {
        "NewsArticle",
        "NamedEntities",
        "TextAnswer",
        "CelestialObjectProperties",
        "DiseaseProfile",
        "RecipeProcedural",
        "SoftwareDescription",
        "LiteraryWork",
        "MediaReview",
    }
)
SCHEMA_UNORDERED_ARRAY_KEYS = frozenset({"required", "enum", "type"})


@dataclass(frozen=True)
class FieldIndexVariant:
    tag: str
    npz_path: Path
    meta_path: Path
    fraction: float | None = None
    covered_schema_types: frozenset[str] | None = None


FIELD_INDEX_VARIANTS: dict[str, FieldIndexVariant] = {
    "full": FieldIndexVariant(
        tag="full",
        npz_path=DEFAULT_INDEX_PATH,
        meta_path=DEFAULT_META_PATH,
    ),
    "p25": FieldIndexVariant(
        tag="p25",
        npz_path=DEFAULT_INDEX_PATH_P25,
        meta_path=DEFAULT_META_PATH_P25,
        fraction=0.25,
        covered_schema_types=PARTIAL_COVERED_SCHEMA_TYPES,
    ),
    "p50": FieldIndexVariant(
        tag="p50",
        npz_path=DEFAULT_INDEX_PATH_P50,
        meta_path=DEFAULT_META_PATH_P50,
        fraction=0.50,
        covered_schema_types=PARTIAL_COVERED_SCHEMA_TYPES,
    ),
}


def task_schema_type(task: Task) -> str:
    """Tipo de tarea = título del schema JSON (p. ej. NewsArticle)."""
    title = task.target_schema.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    return "Unknown"


def resolve_field_index_tag(tag: str | None = None) -> FieldIndexVariant:
    """Resuelve la variante de índice. Tag desconocido ⇒ índice completo."""
    raw = (tag or os.getenv("GENSIE_FSP_FIELD_INDEX") or "full").strip().lower()
    return FIELD_INDEX_VARIANTS.get(raw, FIELD_INDEX_VARIANTS["full"])


def select_task_ids_for_partial_index(
    tasks: Iterable[Task],
    *,
    fraction: float,
    covered_schema_types: frozenset[str],
    seed: int = PARTIAL_INDEX_SEED,
) -> frozenset[str]:
    """Muestra estratificada por tipo de schema dentro de `covered_schema_types`."""
    if not 0.0 < fraction <= 1.0:
        raise ValueError("fraction debe estar en (0, 1].")

    by_type: dict[str, list[str]] = defaultdict(list)
    for task in tasks:
        schema_type = task_schema_type(task)
        if schema_type in covered_schema_types:
            by_type[schema_type].append(task.id)

    rng = random.Random(seed)
    selected: list[str] = []
    for schema_type in sorted(by_type):
        task_ids = sorted(by_type[schema_type])
        sample_size = max(1, round(len(task_ids) * fraction))
        sample_size = min(sample_size, len(task_ids))
        selected.extend(rng.sample(task_ids, sample_size))
    return frozenset(selected)


# ---------------------------------------------------------------------------
# Tipos / clases de tipo
# ---------------------------------------------------------------------------

def type_class(field: FieldInfo) -> str:
    """Devuelve la clase de tipo de un campo para comparar compatibilidad.

    Reglas:
      - cualquier enum  -> "enum"  (distintos enums son comparables)
      - integer / number -> "numeric"
      - string / boolean / object -> el propio nombre
      - array -> "array[<clase del item>]" (arrays solo compatibles si su item
        está en la misma clase, p.ej. array[string] ≠ array[numeric])
      - se ignora la nulabilidad: nullable[int] y int están en la misma clase
    """
    if field.enum is not None:
        return "enum"
    base = field.json_type
    if base in ("integer", "number"):
        return "numeric"
    if base in ("string", "boolean", "object"):
        return base
    if base == "array":
        inner = "any" if field.items is None else type_class(field.items)
        return f"array[{inner}]"
    return "any"


def type_repr(field: FieldInfo) -> str:
    """Etiqueta legible del tipo para incluir en el texto del embedding."""
    if field.enum is not None:
        ref_name = field.ref.split("/")[-1] if field.ref else "enum"
        base = f"enum[{ref_name}]" if ref_name != "enum" else "enum"
    else:
        base = field.json_type or "any"
        if base == "array" and field.items is not None:
            base = f"array of {type_repr(field.items)}"
    if field.nullable:
        base = f"{base}|null"
    return base


def field_embedding_text(field: FieldInfo) -> str:
    head = f"{field.name} ({type_repr(field)})"
    if field.description:
        return f"{head}: {field.description.strip()}"
    return head


def task_embedding_text(
    instruction: str,
    target_schema: JsonDict,
    *,
    task_id: str | None = None,
) -> str:
    """Texto global para comparar tasks con el mismo schema estructural."""
    parts = []
    if task_id:
        parts.append(task_id.strip())
    parts.append(instruction.strip())
    parts.extend(spec.text for spec in task_field_specs(target_schema))
    return "\n".join(part for part in parts if part)


def normalized_schema_fingerprint(schema: JsonDict) -> str:
    """Fingerprint estructural que ignora descriptions y orden accidental."""
    return canonical_json(_normalize_schema_for_fingerprint(schema))


def _normalize_schema_for_fingerprint(value: Any, *, parent_key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {
            key: "" if key == "description" else _normalize_schema_for_fingerprint(
                item,
                parent_key=key,
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        normalized = [
            _normalize_schema_for_fingerprint(item, parent_key=parent_key)
            for item in value
        ]
        if parent_key in SCHEMA_UNORDERED_ARRAY_KEYS:
            return sorted(normalized, key=canonical_json)
        return normalized
    return value


# ---------------------------------------------------------------------------
# Especificaciones de campo / tarea
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FieldSpec:
    name: str
    type_class: str
    text: str


def task_field_specs(target_schema: JsonDict) -> tuple[FieldSpec, ...]:
    """Decompone el schema en sus campos de primer nivel."""
    return tuple(
        FieldSpec(
            name=field.name,
            type_class=type_class(field),
            text=field_embedding_text(field),
        )
        for field in parse_schema_fields(target_schema)
    )


# ---------------------------------------------------------------------------
# Embedder
# ---------------------------------------------------------------------------

def _normalize(matrix: np.ndarray) -> np.ndarray:
    if matrix.size == 0:
        return matrix
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


class FieldEmbedder:
    """Wrapper sobre `fastembed.TextEmbedding` que devuelve vectores L2-normalizados."""

    def __init__(self, model_name: str = DEFAULT_EMBED_MODEL) -> None:
        from fastembed import TextEmbedding

        self.model_name = model_name
        self._model = TextEmbedding(model_name=model_name)

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 0), dtype=np.float32)
        vectors = np.asarray(list(self._model.embed(list(texts))), dtype=np.float32)
        return _normalize(vectors)


# ---------------------------------------------------------------------------
# Construcción del índice
# ---------------------------------------------------------------------------

def iter_tasks(directory: Path) -> Iterable[Task]:
    for path in sorted(directory.glob("*.json")):
        yield Task.load(path)


def build_index(
    data_dir: Path = DEFAULT_DATA_DIR,
    output_path: Path = DEFAULT_INDEX_PATH,
    meta_path: Path = DEFAULT_META_PATH,
    *,
    embedder: FieldEmbedder | None = None,
    verbose: bool = True,
    included_task_ids: frozenset[str] | None = None,
    index_meta: dict[str, Any] | None = None,
) -> int:
    """Recorre `data_dir`, embebe los campos top-level y guarda matriz + meta.

    Si `included_task_ids` está definido, solo indexa esas tareas.
    Devuelve el nº total de filas (campos) indexadas.
    """
    embedder = embedder or FieldEmbedder()

    rows: list[dict[str, str]] = []
    texts: list[str] = []
    task_count = 0
    for task in iter_tasks(data_dir):
        if included_task_ids is not None and task.id not in included_task_ids:
            continue
        task_count += 1
        for spec in task_field_specs(task.target_schema):
            rows.append(
                {
                    "task_id": task.id,
                    "schema_type": task_schema_type(task),
                    "field_name": spec.name,
                    "type_class": spec.type_class,
                    "text": spec.text,
                }
            )
            texts.append(spec.text)

    if not texts:
        raise RuntimeError(f"No se encontró ningún campo de primer nivel en {data_dir}")

    if verbose:
        suffix = ""
        if included_task_ids is not None:
            suffix = f" (subset: {task_count} tareas)"
        print(
            f"[field_rag] tareas: {task_count}, campos: {len(texts)}{suffix}; "
            f"embebiendo con {embedder.model_name}…"
        )

    embeddings = embedder.embed(texts)

    payload: dict[str, Any] = {
        "model": embedder.model_name,
        "dim": int(embeddings.shape[1]) if embeddings.ndim == 2 else 0,
        "rows": rows,
    }
    if index_meta:
        payload.update(index_meta)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(output_path, embeddings=embeddings)
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if verbose:
        print(
            f"[field_rag] guardado embeddings={output_path} "
            f"(shape={tuple(embeddings.shape)}), meta={meta_path}"
        )
    return len(rows)


def build_index_for_variant(
    variant: FieldIndexVariant | str,
    data_dir: Path = DEFAULT_DATA_DIR,
    *,
    embedder: FieldEmbedder | None = None,
    verbose: bool = True,
) -> int:
    """Construye un índice dev según la variante (`full`, `p25`, `p50`)."""
    if isinstance(variant, str):
        variant = FIELD_INDEX_VARIANTS[variant]

    included_task_ids: frozenset[str] | None = None
    index_meta: dict[str, Any] = {"index_tag": variant.tag}
    if variant.fraction is not None and variant.covered_schema_types is not None:
        tasks = list(iter_tasks(data_dir))
        included_task_ids = select_task_ids_for_partial_index(
            tasks,
            fraction=variant.fraction,
            covered_schema_types=variant.covered_schema_types,
        )
        index_meta.update(
            {
                "fraction": variant.fraction,
                "covered_schema_types": sorted(variant.covered_schema_types),
                "included_task_ids": sorted(included_task_ids),
                "task_count": len(included_task_ids),
            }
        )
    else:
        index_meta["task_count"] = sum(1 for _ in iter_tasks(data_dir))

    return build_index(
        data_dir,
        variant.npz_path,
        variant.meta_path,
        embedder=embedder,
        verbose=verbose,
        included_task_ids=included_task_ids,
        index_meta=index_meta,
    )


def build_dev_field_indices(
    tags: Sequence[str] = ("full", "p25", "p50"),
    data_dir: Path = DEFAULT_DATA_DIR,
    *,
    embedder: FieldEmbedder | None = None,
    verbose: bool = True,
) -> dict[str, int]:
    """Construye varias variantes del índice dev. Devuelve filas indexadas por tag."""
    embedder = embedder or FieldEmbedder()
    counts: dict[str, int] = {}
    for raw_tag in tags:
        tag = raw_tag.strip().lower()
        if tag not in FIELD_INDEX_VARIANTS:
            raise KeyError(
                f"Índice desconocido: {raw_tag!r}. Opciones: {', '.join(FIELD_INDEX_VARIANTS)}"
            )
        counts[tag] = build_index_for_variant(
            FIELD_INDEX_VARIANTS[tag],
            data_dir,
            embedder=embedder,
            verbose=verbose,
        )
    return counts


def build_case_index(
    cases: Iterable[StructuredFspCase] | None = None,
    output_path: Path = DEFAULT_CASE_INDEX_PATH,
    meta_path: Path = DEFAULT_CASE_META_PATH,
    *,
    embedder: FieldEmbedder | None = None,
    verbose: bool = True,
) -> int:
    """Embebe el corpus FSP: campos top-level y texto global same-schema."""
    if cases is None:
        from gensie.fsp.cases import default_extraction_fsp_cases

        cases = default_extraction_fsp_cases()
    embedder = embedder or FieldEmbedder()

    field_rows: list[dict[str, str]] = []
    field_texts: list[str] = []
    same_schema_rows: list[dict[str, str]] = []
    same_schema_texts: list[str] = []
    case_count = 0
    for case in cases:
        case_count += 1
        for spec in task_field_specs(case.schema):
            field_rows.append(
                {
                    "case_id": case.id,
                    "field_name": spec.name,
                    "type_class": spec.type_class,
                    "text": spec.text,
                }
            )
            field_texts.append(spec.text)
        same_schema_text = task_embedding_text(
            case.instruction,
            case.schema,
            task_id=case.id,
        )
        same_schema_rows.append(
            {
                "case_id": case.id,
                "schema_fingerprint": normalized_schema_fingerprint(case.schema),
                "text": same_schema_text,
            }
        )
        same_schema_texts.append(same_schema_text)

    if not field_texts:
        raise RuntimeError("No se encontro ningun campo en el corpus FSP.")

    if verbose:
        print(
            f"[field_rag] casos FSP: {case_count}, campos: {len(field_texts)}, "
            f"same_schema: {len(same_schema_texts)}; embebiendo con {embedder.model_name}..."
        )

    field_embeddings = embedder.embed(field_texts)
    same_schema_embeddings = embedder.embed(same_schema_texts)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        output_path,
        field_embeddings=field_embeddings,
        same_schema_embeddings=same_schema_embeddings,
    )
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(
        json.dumps(
            {
                "model": embedder.model_name,
                "field_dim": int(field_embeddings.shape[1])
                if field_embeddings.ndim == 2
                else 0,
                "same_schema_dim": int(same_schema_embeddings.shape[1])
                if same_schema_embeddings.ndim == 2
                else 0,
                "field_rows": field_rows,
                "same_schema_rows": same_schema_rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return len(field_rows)


# ---------------------------------------------------------------------------
# Carga del índice
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IndexedField:
    row_index: int
    task_id: str
    field_name: str
    type_class: str
    text: str


@dataclass
class FieldIndex:
    model_name: str
    embeddings: np.ndarray  # (N_campos, dim) ya L2-normalizados
    fields: tuple[IndexedField, ...]
    by_task: dict[str, list[IndexedField]]

    @classmethod
    def load(
        cls,
        npz_path: Path | None = None,
        meta_path: Path | None = None,
        *,
        tag: str | None = None,
    ) -> "FieldIndex":
        if npz_path is None or meta_path is None:
            variant = resolve_field_index_tag(tag)
            npz_path = npz_path or variant.npz_path
            meta_path = meta_path or variant.meta_path
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        with np.load(npz_path) as data:
            embeddings = np.array(data["embeddings"], dtype=np.float32)
        fields = tuple(
            IndexedField(
                row_index=index,
                task_id=row["task_id"],
                field_name=row["field_name"],
                type_class=row["type_class"],
                text=row["text"],
            )
            for index, row in enumerate(meta["rows"])
        )
        by_task: dict[str, list[IndexedField]] = {}
        for field in fields:
            by_task.setdefault(field.task_id, []).append(field)
        return cls(
            model_name=meta["model"],
            embeddings=embeddings,
            fields=fields,
            by_task=by_task,
        )


# ---------------------------------------------------------------------------
# Selección de pares diversos
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DiverseSelection:
    first_task_id: str
    second_task_id: str
    score: float
    query_field_names: tuple[str, ...]
    first_vector: np.ndarray
    second_vector: np.ndarray
    per_task_vectors: dict[str, np.ndarray]


@dataclass(frozen=True)
class FieldRankedCase:
    key: str
    index: int
    case: StructuredFspCase
    vector: np.ndarray
    best_field_names: tuple[str, ...]
    field_score: float
    base_score: float
    matched_tags: tuple[str, ...]
    matched_terms: tuple[str, ...]
    schema_match: bool
    compatible_fields: tuple[str, ...]


@dataclass(frozen=True)
class SameSchemaRankedCase:
    key: str
    index: int
    case: StructuredFspCase
    similarity: float
    schema_fingerprint: str
    above_threshold: bool


def candidate_vector(
    query_specs: Sequence[FieldSpec],
    query_embeddings: np.ndarray,
    candidate_fields: Sequence[IndexedField],
    all_candidate_embeddings: np.ndarray,
) -> np.ndarray:
    """Construye el vector del candidato (dim = nº de campos de la query).

    vec[i] = max coseno entre query_emb[i] y los campos del candidato cuya
    `type_class` coincida con la del campo i-ésimo de la query. 0 si no hay match.
    """
    out = np.zeros(len(query_specs), dtype=np.float32)
    if not candidate_fields:
        return out

    rows = np.array([f.row_index for f in candidate_fields], dtype=np.int64)
    cand_emb = all_candidate_embeddings[rows]  # (n_fields, dim)
    cand_classes = np.array([f.type_class for f in candidate_fields])

    for i, qspec in enumerate(query_specs):
        mask = np.where(cand_classes == qspec.type_class)[0]
        if mask.size == 0:
            continue
        sims = cand_emb[mask] @ query_embeddings[i]
        out[i] = max(0.0, float(np.max(sims)))
    return out


def candidate_alignment(
    query_specs: Sequence[FieldSpec],
    query_embeddings: np.ndarray,
    candidate_fields: Sequence[IndexedField],
    all_candidate_embeddings: np.ndarray,
) -> tuple[np.ndarray, tuple[str, ...]]:
    """Devuelve vector de similitud y mejor campo FSP por campo de la query."""
    out = np.zeros(len(query_specs), dtype=np.float32)
    best_names = [""] * len(query_specs)
    if not candidate_fields:
        return out, tuple(best_names)

    rows = np.array([f.row_index for f in candidate_fields], dtype=np.int64)
    cand_emb = all_candidate_embeddings[rows]  # (n_fields, dim)
    cand_classes = np.array([f.type_class for f in candidate_fields])

    for i, qspec in enumerate(query_specs):
        mask = np.where(cand_classes == qspec.type_class)[0]
        if mask.size == 0:
            continue
        sims = cand_emb[mask] @ query_embeddings[i]
        best_local_index = int(np.argmax(sims))
        best_score = max(0.0, float(sims[best_local_index]))
        out[i] = best_score
        if best_score > 0.0:
            best_names[i] = candidate_fields[int(mask[best_local_index])].field_name
    return out, tuple(best_names)


def _pair_score(v1: np.ndarray, v2: np.ndarray) -> float:
    return float(np.linalg.norm(v1 + v2) + np.linalg.norm(v1 - v2))


def select_diverse_pair(
    target_schema: JsonDict,
    index: FieldIndex,
    embedder: FieldEmbedder,
    *,
    exclude_task_ids: Iterable[str] = (),
) -> DiverseSelection:
    """Devuelve los dos candidatos c1, c2 que maximizan |c1+c2| + |c1-c2|."""
    query_specs = task_field_specs(target_schema)
    if not query_specs:
        raise ValueError("La query no tiene campos de primer nivel para vectorizar.")

    query_embeddings = embedder.embed([s.text for s in query_specs])

    excluded = set(exclude_task_ids)
    task_vectors: dict[str, np.ndarray] = {}
    for task_id, fields in index.by_task.items():
        if task_id in excluded:
            continue
        task_vectors[task_id] = candidate_vector(
            query_specs, query_embeddings, fields, index.embeddings
        )

    task_ids = list(task_vectors.keys())
    if len(task_ids) < 2:
        raise ValueError("Se necesitan al menos 2 candidatos en el índice.")

    best_score = -1.0
    best_pair: tuple[str, str] | None = None
    for i, a in enumerate(task_ids):
        va = task_vectors[a]
        for b in task_ids[i + 1:]:
            score = _pair_score(va, task_vectors[b])
            if score > best_score:
                best_score = score
                best_pair = (a, b)

    assert best_pair is not None
    a, b = best_pair
    return DiverseSelection(
        first_task_id=a,
        second_task_id=b,
        score=best_score,
        query_field_names=tuple(s.name for s in query_specs),
        first_vector=task_vectors[a],
        second_vector=task_vectors[b],
        per_task_vectors=task_vectors,
    )


@lru_cache(maxsize=1)
def default_field_embedder() -> FieldEmbedder:
    return FieldEmbedder()


def rank_fsp_cases_by_field_embeddings(
    *,
    task_schema: JsonDict,
    task_text: str,
    task_id: str | None = None,
    task_instruction: str | None = None,
    cases: Iterable[StructuredFspCase],
    top_k: int,
    embedder: FieldEmbedder | None = None,
    diagnostics: dict[str, Any] | None = None,
    same_schema_similarity_threshold: float = DEFAULT_SAME_SCHEMA_SIMILARITY_THRESHOLD,
) -> tuple[FspRetrievalResult, ...]:
    """Rankea casos FSP usando embeddings por campo top-level.

    Si hay suficientes casos con el mismo schema exacto, conserva esa prioridad.
    Para el resto, usa el vector campo-a-campo y, cuando se piden al menos dos
    casos, favorece el par más complementario según `_pair_score`.
    """
    case_list = tuple(cases)
    limit = max(1, top_k)
    if not case_list:
        _set_diagnostics(
            diagnostics,
            {
                "method": "same_schema_embeddings",
                "selection_method": "empty_corpus",
                "task_schema_fields": [],
                "same_schema_similarity_threshold": same_schema_similarity_threshold,
                "same_schema_candidates": [],
                "considered_cases": [],
                "selected_case_ids": [],
            },
        )
        return ()

    query_specs = task_field_specs(task_schema)
    if not query_specs:
        legacy_results = rank_fsp_cases(
            task_schema=task_schema,
            task_text=task_text,
            cases=case_list,
            top_k=len(case_list),
        )
        results = _mark_results_not_same_schema(legacy_results[:limit])
        _set_diagnostics(
            diagnostics,
            {
                "method": "schema_lexical",
                "selection_method": "schema_lexical_fallback",
                "task_schema_fields": [],
                "same_schema_similarity_threshold": same_schema_similarity_threshold,
                "same_schema_candidates": [],
                "considered_cases": [],
                "selected_case_ids": [result.case.id for result in results],
            },
        )
        return results

    embedder = embedder or default_field_embedder()
    query_instruction = task_instruction if task_instruction is not None else task_text
    same_schema_ranked = _rank_same_schema_candidates(
        task_schema=task_schema,
        task_id=task_id,
        task_instruction=query_instruction,
        cases=case_list,
        embedder=embedder,
        threshold=same_schema_similarity_threshold,
    )
    same_schema_available = [
        item for item in same_schema_ranked
        if item.above_threshold
    ]
    if len(same_schema_available) >= 2:
        selected_same_schema = tuple(
            sorted(
                same_schema_available,
                key=lambda item: (-item.similarity, item.index),
            )[:limit]
        )
        results = tuple(
            FspRetrievalResult(
                case=item.case,
                score=item.similarity,
                rank=rank,
                matched_tags=(),
                matched_terms=(),
                schema_match=True,
                compatible_fields=tuple(spec.name for spec in query_specs),
                method="same_schema_embeddings",
            )
            for rank, item in enumerate(selected_same_schema, start=1)
        )
        _set_diagnostics(
            diagnostics,
            _same_schema_retrieval_diagnostics(
                query_specs,
                same_schema_ranked,
                results,
                threshold=same_schema_similarity_threshold,
                task_fingerprint=normalized_schema_fingerprint(task_schema),
                selection_method="same_schema_embeddings",
            ),
        )
        return results

    query_embeddings = embedder.embed([spec.text for spec in query_specs])

    candidate_fields_by_key: dict[str, list[IndexedField]] = {}
    candidate_case_by_key: dict[str, StructuredFspCase] = {}
    candidate_texts: list[str] = []
    candidate_rows: list[IndexedField] = []
    for index, case in enumerate(case_list):
        key = str(index)
        fields: list[IndexedField] = []
        for spec in task_field_specs(case.schema):
            row = IndexedField(
                row_index=len(candidate_rows),
                task_id=key,
                field_name=spec.name,
                type_class=spec.type_class,
                text=spec.text,
            )
            fields.append(row)
            candidate_rows.append(row)
            candidate_texts.append(spec.text)
        if fields:
            candidate_fields_by_key[key] = fields
            candidate_case_by_key[key] = case

    if not candidate_texts:
        legacy_results = rank_fsp_cases(
            task_schema=task_schema,
            task_text=task_text,
            cases=case_list,
            top_k=len(case_list),
        )
        results = _mark_results_not_same_schema(legacy_results[:limit])
        _set_diagnostics(
            diagnostics,
            {
                "method": "schema_lexical",
                "selection_method": "schema_lexical_fallback",
                "task_schema_fields": [spec.name for spec in query_specs],
                "same_schema_similarity_threshold": same_schema_similarity_threshold,
                "same_schema_candidates": _same_schema_candidates_diagnostics(
                    same_schema_ranked
                ),
                "considered_cases": [],
                "selected_case_ids": [result.case.id for result in results],
            },
        )
        return results

    candidate_embeddings = embedder.embed(candidate_texts)
    ranked: list[FieldRankedCase] = []
    for key, fields in candidate_fields_by_key.items():
        case = candidate_case_by_key[key]
        vector, best_field_names = candidate_alignment(
            query_specs,
            query_embeddings,
            fields,
            candidate_embeddings,
        )
        field_score = float(np.linalg.norm(vector))
        ranked.append(
            FieldRankedCase(
                key=key,
                index=int(key),
                case=case,
                vector=vector,
                best_field_names=best_field_names,
                field_score=field_score,
                base_score=0.0,
                matched_tags=(),
                matched_terms=(),
                schema_match=False,
                compatible_fields=tuple(
                    spec.name
                    for spec, value in zip(query_specs, vector)
                    if value > 0.0
                ),
            )
        )

    if not ranked or all(item.field_score <= 0.0 for item in ranked):
        legacy_results = rank_fsp_cases(
            task_schema=task_schema,
            task_text=task_text,
            cases=case_list,
            top_k=len(case_list),
        )
        results = _mark_results_not_same_schema(legacy_results[:limit])
        _set_diagnostics(
            diagnostics,
            _with_same_schema_diagnostics(
                _field_retrieval_diagnostics(
                    query_specs,
                    ranked,
                    results,
                    selection_method="schema_lexical_fallback",
                ),
                same_schema_ranked=same_schema_ranked,
                threshold=same_schema_similarity_threshold,
                task_fingerprint=normalized_schema_fingerprint(task_schema),
            ),
        )
        return results

    selected = _select_field_ranked_cases(ranked, limit)
    results = tuple(
        FspRetrievalResult(
            case=item.case,
            score=item.field_score,
            rank=rank,
            matched_tags=item.matched_tags,
            matched_terms=item.matched_terms,
            schema_match=False,
            compatible_fields=item.compatible_fields,
            method="field_embeddings",
        )
        for rank, item in enumerate(selected, start=1)
    )
    _set_diagnostics(
        diagnostics,
        _with_same_schema_diagnostics(
            _field_retrieval_diagnostics(
                query_specs,
                ranked,
                results,
                selection_method="field_embeddings_fallback",
            ),
            same_schema_ranked=same_schema_ranked,
            threshold=same_schema_similarity_threshold,
            task_fingerprint=normalized_schema_fingerprint(task_schema),
        ),
    )
    return results


def _rank_same_schema_candidates(
    *,
    task_schema: JsonDict,
    task_id: str | None,
    task_instruction: str,
    cases: Sequence[StructuredFspCase],
    embedder: FieldEmbedder,
    threshold: float,
) -> tuple[SameSchemaRankedCase, ...]:
    task_fingerprint = normalized_schema_fingerprint(task_schema)
    fingerprint_matches: list[tuple[str, int, StructuredFspCase, str]] = []
    candidate_texts: list[str] = []
    for index, case in enumerate(cases):
        case_fingerprint = normalized_schema_fingerprint(case.schema)
        if case_fingerprint != task_fingerprint:
            continue
        fingerprint_matches.append((str(index), index, case, case_fingerprint))
        candidate_texts.append(
            task_embedding_text(
                case.instruction,
                case.schema,
                task_id=case.id,
            )
        )
    if not fingerprint_matches:
        return ()

    query_text = task_embedding_text(
        task_instruction,
        task_schema,
        task_id=task_id,
    )
    embeddings = _normalize(embedder.embed([query_text, *candidate_texts]))
    if embeddings.ndim != 2 or embeddings.shape[0] != len(candidate_texts) + 1:
        return ()
    query_embedding = embeddings[0]
    candidate_embeddings = embeddings[1:]

    ranked: list[SameSchemaRankedCase] = []
    for (key, index, case, fingerprint), candidate_embedding in zip(
        fingerprint_matches,
        candidate_embeddings,
    ):
        similarity = float(candidate_embedding @ query_embedding)
        ranked.append(
            SameSchemaRankedCase(
                key=key,
                index=index,
                case=case,
                similarity=similarity,
                schema_fingerprint=fingerprint,
                above_threshold=similarity >= threshold,
            )
        )
    return tuple(sorted(ranked, key=lambda item: (-item.similarity, item.index)))


def _same_schema_retrieval_diagnostics(
    query_specs: Sequence[FieldSpec],
    ranked: Sequence[SameSchemaRankedCase],
    results: Sequence[FspRetrievalResult],
    *,
    threshold: float,
    task_fingerprint: str,
    selection_method: str,
) -> dict[str, Any]:
    task_fields = [spec.name for spec in query_specs]
    return {
        "method": "same_schema_embeddings",
        "selection_method": selection_method,
        "task_schema_fields": task_fields,
        "same_schema_task_fingerprint": task_fingerprint,
        "same_schema_similarity_threshold": threshold,
        "same_schema_candidates": _same_schema_candidates_diagnostics(ranked),
        "selected_case_ids": [result.case.id for result in results],
        "considered_cases": [],
    }


def _same_schema_candidates_diagnostics(
    ranked: Sequence[SameSchemaRankedCase],
) -> list[dict[str, Any]]:
    return [
        {
            "case_id": item.case.id,
            "domain": item.case.domain,
            "selected_by_threshold": item.above_threshold,
            "similarity": round(float(item.similarity), 6),
            "schema_fingerprint": item.schema_fingerprint,
        }
        for item in sorted(ranked, key=lambda candidate: candidate.index)
    ]


def _with_same_schema_diagnostics(
    payload: dict[str, Any],
    *,
    same_schema_ranked: Sequence[SameSchemaRankedCase],
    threshold: float,
    task_fingerprint: str,
) -> dict[str, Any]:
    payload["same_schema_task_fingerprint"] = task_fingerprint
    payload["same_schema_similarity_threshold"] = threshold
    payload["same_schema_candidates"] = _same_schema_candidates_diagnostics(
        same_schema_ranked
    )
    return payload


def _mark_results_not_same_schema(
    results: Sequence[FspRetrievalResult],
) -> tuple[FspRetrievalResult, ...]:
    return tuple(
        FspRetrievalResult(
            case=result.case,
            score=result.score,
            rank=result.rank,
            matched_tags=result.matched_tags,
            matched_terms=result.matched_terms,
            schema_match=False,
            compatible_fields=result.compatible_fields,
            method=result.method,
        )
        for result in results
    )


def _set_diagnostics(
    diagnostics: dict[str, Any] | None,
    payload: dict[str, Any],
) -> None:
    if diagnostics is None:
        return
    diagnostics.clear()
    diagnostics.update(payload)


def _field_retrieval_diagnostics(
    query_specs: Sequence[FieldSpec],
    ranked: Sequence[FieldRankedCase],
    results: Sequence[FspRetrievalResult],
    *,
    selection_method: str,
) -> dict[str, Any]:
    selected_by_id = {result.case.id: result for result in results}
    task_fields = [spec.name for spec in query_specs]
    considered_cases = []
    for item in sorted(ranked, key=lambda ranked_case: ranked_case.index):
        selected = selected_by_id.get(item.case.id)
        score = (
            selected.score
            if selected is not None
            else item.field_score
        )
        considered_cases.append(
            {
                "case_id": item.case.id,
                "domain": item.case.domain,
                "selected": selected is not None,
                "rank": selected.rank if selected is not None else None,
                "score": round(float(score), 6),
                "field_score": round(float(item.field_score), 6),
                "base_score": round(float(item.base_score), 6),
                "schema_match": item.schema_match,
                "task_fields": task_fields,
                "similarity_vector": [
                    round(float(value), 6) for value in item.vector.tolist()
                ],
                "best_fsp_field_by_task_field": list(item.best_field_names),
            }
        )
    return {
        "method": "field_embeddings",
        "selection_method": selection_method,
        "task_schema_fields": task_fields,
        "selected_case_ids": [result.case.id for result in results],
        "considered_cases": considered_cases,
    }


def _select_field_ranked_cases(
    ranked: Sequence[FieldRankedCase],
    limit: int,
) -> tuple[FieldRankedCase, ...]:
    exact = [item for item in ranked if item.schema_match]
    selected: list[FieldRankedCase] = []
    if exact:
        exact.sort(key=lambda item: (-item.field_score, item.index))
        selected.extend(exact[:limit])

    if len(selected) >= limit:
        return tuple(selected[:limit])

    selected_keys = {item.key for item in selected}
    remaining = [item for item in ranked if item.key not in selected_keys]
    selected.extend(
        _select_diverse_field_ranked_cases(remaining, limit - len(selected))
    )
    return tuple(selected[:limit])


def _select_diverse_field_ranked_cases(
    ranked: Sequence[FieldRankedCase],
    limit: int,
) -> tuple[FieldRankedCase, ...]:
    if limit <= 0 or not ranked:
        return ()
    if limit == 1 or len(ranked) == 1:
        return tuple(sorted(ranked, key=_field_rank_sort_key)[:limit])

    best_pair: tuple[FieldRankedCase, FieldRankedCase] | None = None
    best_key: tuple[float, float, int] | None = None
    for i, first in enumerate(ranked):
        for second in ranked[i + 1 :]:
            pair_score = _pair_score(first.vector, second.vector)
            score_key = (
                pair_score,
                first.field_score + second.field_score,
                -(first.index + second.index),
            )
            if best_key is None or score_key > best_key:
                best_key = score_key
                best_pair = (first, second)

    if best_pair is None or best_key is None or best_key[0] <= 0.0:
        return tuple(sorted(ranked, key=_field_rank_sort_key)[:limit])

    selected = sorted(best_pair, key=_field_rank_sort_key)
    selected_keys = {item.key for item in selected}
    remaining = [
        item for item in sorted(ranked, key=_field_rank_sort_key)
        if item.key not in selected_keys
    ]
    selected.extend(remaining[: max(0, limit - len(selected))])
    return tuple(selected[:limit])


def _field_rank_sort_key(item: FieldRankedCase) -> tuple[float, float, int]:
    return (-item.field_score, 0.0, item.index)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    index_choices = ("full", "p25", "p50", "all", *FIELD_INDEX_VARIANTS.keys())
    parser = argparse.ArgumentParser(
        description="Construye el índice FSP de embeddings de campos sobre data/dev."
    )
    parser.add_argument(
        "--corpus",
        choices=("dev", "fsp-cases"),
        default="dev",
        help="Corpus a indexar: tasks de data/dev o recursos FSP para RAG.",
    )
    parser.add_argument(
        "--index",
        "-i",
        choices=sorted(set(index_choices)),
        default="full",
        help=(
            "Variante del índice dev: full (100%%), p25 (25%% de tipos cubiertos), "
            "p50 (50%%), all (construye las tres). Ignorado para --corpus fsp-cases."
        ),
    )
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--meta", type=Path)
    parser.add_argument("--model", default=DEFAULT_EMBED_MODEL)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    embedder = FieldEmbedder(model_name=args.model)
    if args.corpus == "fsp-cases":
        build_case_index(
            output_path=args.output or DEFAULT_CASE_INDEX_PATH,
            meta_path=args.meta or DEFAULT_CASE_META_PATH,
            embedder=embedder,
            verbose=not args.quiet,
        )
        return

    if args.index == "all":
        counts = build_dev_field_indices(
            ("full", "p25", "p50"),
            args.data_dir,
            embedder=embedder,
            verbose=not args.quiet,
        )
        if not args.quiet:
            for tag, row_count in counts.items():
                print(f"[field_rag] {tag}: {row_count} campos indexados")
        return

    variant = FIELD_INDEX_VARIANTS[args.index]
    if args.output is not None or args.meta is not None:
        build_index(
            args.data_dir,
            args.output or variant.npz_path,
            args.meta or variant.meta_path,
            embedder=embedder,
            verbose=not args.quiet,
            included_task_ids=(
                select_task_ids_for_partial_index(
                    list(iter_tasks(args.data_dir)),
                    fraction=variant.fraction,
                    covered_schema_types=variant.covered_schema_types,
                )
                if variant.fraction is not None and variant.covered_schema_types
                else None
            ),
            index_meta={"index_tag": variant.tag},
        )
    else:
        build_index_for_variant(
            variant,
            args.data_dir,
            embedder=embedder,
            verbose=not args.quiet,
        )


if __name__ == "__main__":
    main()
