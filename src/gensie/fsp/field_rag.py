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
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from gensie.schemas.fields import FieldInfo, parse_schema_fields
from gensie.schemas.inspect import JsonDict
from gensie.task import Task


DEFAULT_EMBED_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_DATA_DIR = Path("data/dev")
DEFAULT_INDEX_PATH = Path("data/fsp_index/dev_field_embeddings.npz")
DEFAULT_META_PATH = Path("data/fsp_index/dev_field_embeddings.meta.json")


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
) -> int:
    """Recorre `data_dir`, embebe los campos top-level y guarda matriz + meta.

    Devuelve el nº total de filas (campos) indexadas.
    """
    embedder = embedder or FieldEmbedder()

    rows: list[dict[str, str]] = []
    texts: list[str] = []
    task_count = 0
    for task in iter_tasks(data_dir):
        task_count += 1
        for spec in task_field_specs(task.target_schema):
            rows.append(
                {
                    "task_id": task.id,
                    "field_name": spec.name,
                    "type_class": spec.type_class,
                    "text": spec.text,
                }
            )
            texts.append(spec.text)

    if not texts:
        raise RuntimeError(f"No se encontró ningún campo de primer nivel en {data_dir}")

    if verbose:
        print(f"[field_rag] tareas: {task_count}, campos: {len(texts)}; embebiendo con {embedder.model_name}…")

    embeddings = embedder.embed(texts)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(output_path, embeddings=embeddings)
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(
        json.dumps(
            {
                "model": embedder.model_name,
                "dim": int(embeddings.shape[1]) if embeddings.ndim == 2 else 0,
                "rows": rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    if verbose:
        print(
            f"[field_rag] guardado embeddings={output_path} "
            f"(shape={tuple(embeddings.shape)}), meta={meta_path}"
        )
    return len(rows)


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
        npz_path: Path = DEFAULT_INDEX_PATH,
        meta_path: Path = DEFAULT_META_PATH,
    ) -> "FieldIndex":
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
        out[i] = float(np.max(sims))
    return out


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Construye el índice FSP de embeddings de campos sobre data/dev."
    )
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_INDEX_PATH)
    parser.add_argument("--meta", type=Path, default=DEFAULT_META_PATH)
    parser.add_argument("--model", default=DEFAULT_EMBED_MODEL)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    embedder = FieldEmbedder(model_name=args.model)
    build_index(
        args.data_dir,
        args.output,
        args.meta,
        embedder=embedder,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    main()
