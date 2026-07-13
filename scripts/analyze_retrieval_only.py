from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gensie.eval import flatten_json
from gensie.fsp.cases import default_extraction_fsp_cases
from gensie.fsp.examples import StructuredFspCase
from gensie.fsp.field_rag import (
    DEFAULT_EMBED_MODEL,
    DEFAULT_SAME_SCHEMA_SIMILARITY_THRESHOLD,
    FieldEmbedder,
    normalized_schema_fingerprint,
    rank_fsp_cases_by_field_embeddings,
    same_schema_fsp_cases,
    task_field_specs,
)
from gensie.fsp.retrieval import FspRetrievalResult, rank_fsp_cases
from gensie.task import Task


@dataclass
class CachingFieldEmbedder:
    model_name: str = DEFAULT_EMBED_MODEL
    cache: dict[str, np.ndarray] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._embedder = FieldEmbedder(model_name=self.model_name)

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 0), dtype=np.float32)

        missing = [text for text in texts if text not in self.cache]
        if missing:
            vectors = self._embedder.embed(missing)
            for text, vector in zip(missing, vectors):
                self.cache[text] = np.asarray(vector, dtype=np.float32)
        return np.asarray([self.cache[text] for text in texts], dtype=np.float32)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run FSP retrieval only over GenSIE tasks without calling an LLM."
    )
    parser.add_argument("--data-dir", type=Path, default=Path("data/test"))
    parser.add_argument("--output-dir", type=Path, default=Path("analysis/retrieval_only"))
    parser.add_argument("--model-name", default=DEFAULT_EMBED_MODEL)
    parser.add_argument(
        "--fastembed-cache",
        type=Path,
        default=Path(".cache/fastembed"),
        help="Local fastembed cache path. Use an existing cache to avoid network.",
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--drop-set",
        choices=("none", "official"),
        default="none",
        help="Exclude the official GenSIE 20-instance drop-set before analysis.",
    )
    parser.add_argument(
        "--same-schema-threshold",
        type=float,
        default=DEFAULT_SAME_SCHEMA_SIMILARITY_THRESHOLD,
    )
    parser.add_argument(
        "--trace-examples",
        type=int,
        default=12,
        help="Number of compact human-readable task traces to include.",
    )
    args = parser.parse_args()

    if args.fastembed_cache:
        os.environ.setdefault("FASTEMBED_CACHE_PATH", str(args.fastembed_cache.resolve()))

    loaded_tasks = _load_tasks(args.data_dir, limit=args.limit)
    tasks = apply_drop_set(loaded_tasks, args.drop_set)
    cases = default_extraction_fsp_cases()
    embedder = CachingFieldEmbedder(model_name=args.model_name)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    records = [
        analyze_task(
            task,
            cases=cases,
            embedder=embedder,
            same_schema_threshold=args.same_schema_threshold,
        )
        for task in tasks
    ]
    elapsed_s = time.perf_counter() - started

    summary = build_summary(
        records,
        elapsed_s=elapsed_s,
        embedding_cache_size=len(embedder.cache),
        drop_set=args.drop_set,
        excluded_task_count=len(loaded_tasks) - len(tasks),
    )
    write_outputs(
        args.output_dir,
        records,
        summary,
        trace_examples=args.trace_examples,
    )
    print(f"Wrote retrieval-only analysis to {args.output_dir}")
    print(
        f"Tasks={summary['task_count']} same_schema_route={summary['same_schema_route_count']} "
        f"field_route={summary['field_route_count']} elapsed_s={elapsed_s:.2f}"
    )


def analyze_task(
    task: Task,
    *,
    cases: Sequence[StructuredFspCase],
    embedder: CachingFieldEmbedder,
    same_schema_threshold: float,
) -> dict[str, Any]:
    task_text = " ".join(
        (
            task.id,
            task.instruction,
            str(task.target_schema.get("description") or ""),
        )
    )
    query_specs, field_parse_error = _safe_task_field_specs(task)
    structural_same_cases = same_schema_fsp_cases(task.target_schema, cases)

    official_results, official_diagnostics = _official_retrieval(
        task,
        task_text=task_text,
        cases=cases,
        embedder=embedder,
        same_schema_threshold=same_schema_threshold,
    )

    independent_diagnostics: dict[str, Any] = {}
    independent_results = ()
    if not _uses_same_schema_route(official_results):
        independent_results, independent_diagnostics = _independent_field_retrieval(
            task,
            task_text=task_text,
            cases=cases,
            embedder=embedder,
            same_schema_threshold=same_schema_threshold,
        )

    official_selected = [result.case.id for result in official_results]
    independent_selected = [result.case.id for result in independent_results]
    official_field_metrics = _field_selection_metrics(official_diagnostics)
    independent_field_metrics = _field_selection_metrics(independent_diagnostics)
    same_schema_candidates = _same_schema_candidates(official_diagnostics)
    selected_same_scores = [
        item["similarity"]
        for item in same_schema_candidates
        if item["case_id"] in set(official_selected)
    ]

    return {
        "task_id": task.id,
        "domain": _domain_from_task_id(task.id),
        "schema_title": _schema_title(task),
        "schema_fingerprint": normalized_schema_fingerprint(task.target_schema),
        "input_chars": len(task.input_text),
        "instruction_chars": len(task.instruction),
        "field_count": len(query_specs),
        "field_names": [spec.name for spec in query_specs],
        "field_parse_error": field_parse_error,
        "gold_keys": _gold_key_count(task),
        "structural_same_schema_count": len(structural_same_cases),
        "structural_same_schema_case_ids": [case.id for case in structural_same_cases],
        "same_schema_above_threshold_count": sum(
            1 for item in same_schema_candidates if item.get("selected_by_threshold")
        ),
        "same_schema_candidate_max_similarity": _max_or_none(
            item["similarity"] for item in same_schema_candidates
        ),
        "same_schema_candidate_mean_similarity": _mean_or_none(
            item["similarity"] for item in same_schema_candidates
        ),
        "selected_same_schema_min_similarity": _min_or_none(selected_same_scores),
        "official_method": official_diagnostics.get("method"),
        "official_selection_method": official_diagnostics.get("selection_method"),
        "official_selected_case_ids": official_selected,
        "official_selected_case_domains": [_case_domain(case_id, cases) for case_id in official_selected],
        "official_selected_scores": [round(float(result.score), 6) for result in official_results],
        "official_uses_same_schema": _uses_same_schema_route(official_results),
        "official_field_metrics": official_field_metrics,
        "independent_top2_case_ids": independent_selected,
        "independent_top2_scores": [
            round(float(result.score), 6) for result in independent_results
        ],
        "independent_field_metrics": independent_field_metrics,
        "default_vs_independent_same_pair": (
            set(official_selected) == set(independent_selected)
            if independent_selected
            else None
        ),
        "pair_score_gain_vs_independent": _difference(
            official_field_metrics.get("pair_score"),
            independent_field_metrics.get("pair_score"),
        ),
        "field_score_sum_loss_vs_independent": _difference(
            independent_field_metrics.get("field_score_sum"),
            official_field_metrics.get("field_score_sum"),
        ),
        "coverage_gain_vs_independent": _difference(
            official_field_metrics.get("coverage_ratio"),
            independent_field_metrics.get("coverage_ratio"),
        ),
        "same_schema_candidates": same_schema_candidates,
        "official_considered_cases": _compact_considered_cases(official_diagnostics),
        "independent_considered_cases": _compact_considered_cases(independent_diagnostics),
    }


def _safe_task_field_specs(task: Task) -> tuple[tuple[Any, ...], str | None]:
    try:
        return tuple(task_field_specs(task.target_schema)), None
    except Exception as exc:
        return (), str(exc) or repr(exc)


def _official_retrieval(
    task: Task,
    *,
    task_text: str,
    cases: Sequence[StructuredFspCase],
    embedder: CachingFieldEmbedder,
    same_schema_threshold: float,
) -> tuple[tuple[FspRetrievalResult, ...], dict[str, Any]]:
    diagnostics: dict[str, Any] = {}
    try:
        results = rank_fsp_cases_by_field_embeddings(
            task_schema=task.target_schema,
            task_text=task_text,
            task_id=task.id,
            task_instruction=task.instruction,
            cases=cases,
            top_k=2,
            embedder=embedder,
            diagnostics=diagnostics,
            same_schema_similarity_threshold=same_schema_threshold,
        )
    except Exception as exc:
        return _schema_lexical_fallback(
            task,
            task_text=task_text,
            cases=cases,
            error=str(exc) or repr(exc),
            selection_method="schema_lexical_fallback_after_error",
        )
    return results, diagnostics


def _independent_field_retrieval(
    task: Task,
    *,
    task_text: str,
    cases: Sequence[StructuredFspCase],
    embedder: CachingFieldEmbedder,
    same_schema_threshold: float,
) -> tuple[tuple[FspRetrievalResult, ...], dict[str, Any]]:
    diagnostics: dict[str, Any] = {}
    try:
        results = rank_fsp_cases_by_field_embeddings(
            task_schema=task.target_schema,
            task_text=task_text,
            task_id=task.id,
            task_instruction=task.instruction,
            cases=cases,
            top_k=2,
            embedder=embedder,
            diagnostics=diagnostics,
            same_schema_similarity_threshold=same_schema_threshold,
            use_same_schema_phase=False,
            field_selection="independent_topk",
        )
    except Exception as exc:
        return _schema_lexical_fallback(
            task,
            task_text=task_text,
            cases=cases,
            error=str(exc) or repr(exc),
            selection_method="schema_lexical_fallback_for_independent_after_error",
        )
    return results, diagnostics


def _schema_lexical_fallback(
    task: Task,
    *,
    task_text: str,
    cases: Sequence[StructuredFspCase],
    error: str,
    selection_method: str,
) -> tuple[tuple[FspRetrievalResult, ...], dict[str, Any]]:
    try:
        raw_results = rank_fsp_cases(
            task_schema=task.target_schema,
            task_text=task_text,
            cases=cases,
            top_k=2,
        )
    except Exception as fallback_exc:
        return (), {
            "method": "schema_lexical",
            "selection_method": "retrieval_failed_after_error",
            "task_schema_fields": [],
            "same_schema_similarity_threshold": DEFAULT_SAME_SCHEMA_SIMILARITY_THRESHOLD,
            "same_schema_candidates": [],
            "considered_cases": [],
            "selected_case_ids": [],
            "error": error,
            "fallback_error": str(fallback_exc) or repr(fallback_exc),
        }
    results = tuple(
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
        for result in raw_results
    )
    return results, {
        "method": "schema_lexical",
        "selection_method": selection_method,
        "task_schema_fields": [],
        "same_schema_similarity_threshold": DEFAULT_SAME_SCHEMA_SIMILARITY_THRESHOLD,
        "same_schema_candidates": [],
        "considered_cases": [],
        "selected_case_ids": [result.case.id for result in results],
        "error": error,
    }


def build_summary(
    records: Sequence[dict[str, Any]],
    *,
    elapsed_s: float,
    embedding_cache_size: int,
    drop_set: str,
    excluded_task_count: int,
) -> dict[str, Any]:
    same_schema_records = [
        record for record in records if record["official_uses_same_schema"]
    ]
    field_records = [record for record in records if not record["official_uses_same_schema"]]
    field_embedding_records = [
        record
        for record in field_records
        if record.get("official_selection_method") == "field_embeddings_fallback"
    ]
    failed_records = [
        record
        for record in field_records
        if record.get("official_selection_method") == "retrieval_failed_after_error"
    ]
    structural_same_records = [
        record for record in records if record["structural_same_schema_count"] >= 2
    ]
    structural_but_field = [
        record
        for record in structural_same_records
        if not record["official_uses_same_schema"]
    ]
    pair_gain_values = _numeric_values(
        record.get("pair_score_gain_vs_independent") for record in field_records
    )
    field_score_loss_values = _numeric_values(
        record.get("field_score_sum_loss_vs_independent") for record in field_records
    )
    coverage_gain_values = _numeric_values(
        record.get("coverage_gain_vs_independent") for record in field_records
    )
    same_similarity_values = _numeric_values(
        record.get("selected_same_schema_min_similarity")
        for record in same_schema_records
    )
    same_candidate_max_values = _numeric_values(
        record.get("same_schema_candidate_max_similarity")
        for record in structural_same_records
    )

    by_domain: dict[str, dict[str, Any]] = {}
    for domain in sorted({record["domain"] for record in records}):
        domain_records = [record for record in records if record["domain"] == domain]
        by_domain[domain] = {
            "tasks": len(domain_records),
            "same_schema_route": sum(
                1 for record in domain_records if record["official_uses_same_schema"]
            ),
            "field_route": sum(
                1 for record in domain_records if not record["official_uses_same_schema"]
            ),
            "retrieval_failed": sum(
                1
                for record in domain_records
                if record.get("official_selection_method")
                == "retrieval_failed_after_error"
            ),
        }

    return {
        "task_count": len(records),
        "drop_set": drop_set,
        "excluded_task_count": excluded_task_count,
        "elapsed_s": round(elapsed_s, 3),
        "embedding_cache_size": embedding_cache_size,
        "structural_same_schema_count": len(structural_same_records),
        "same_schema_route_count": len(same_schema_records),
        "field_route_count": len(field_records),
        "field_embeddings_route_count": len(field_embedding_records),
        "retrieval_failed_count": len(failed_records),
        "structural_same_schema_but_field_route_count": len(structural_but_field),
        "non_same_schema_count": len(records) - len(structural_same_records),
        "same_schema_selected_min_similarity": _describe(same_similarity_values),
        "same_schema_candidate_max_similarity": _describe(same_candidate_max_values),
        "field_pair_score_gain_vs_independent": _describe(pair_gain_values),
        "field_score_sum_loss_vs_independent": _describe(field_score_loss_values),
        "field_coverage_gain_vs_independent": _describe(coverage_gain_values),
        "field_default_equals_independent_pair_count": sum(
            1 for record in field_records if record["default_vs_independent_same_pair"] is True
        ),
        "field_default_differs_independent_pair_count": sum(
            1 for record in field_records if record["default_vs_independent_same_pair"] is False
        ),
        "by_domain": by_domain,
        "selected_case_counts": _selected_case_counts(records),
    }


def write_outputs(
    output_dir: Path,
    records: Sequence[dict[str, Any]],
    summary: dict[str, Any],
    *,
    trace_examples: int,
) -> None:
    _write_json(output_dir / "retrieval_summary.json", summary)
    _write_json(output_dir / "test_retrieval_trace.json", {"summary": summary, "tasks": records})
    _write_csv(output_dir / "test_retrieval_by_task.csv", records)
    (output_dir / "retrieval_summary.md").write_text(
        _summary_markdown(summary),
        encoding="utf-8",
    )
    (output_dir / "retrieval_trace_check.md").write_text(
        _trace_check_markdown(records, summary, trace_examples=trace_examples),
        encoding="utf-8",
    )


def _summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Retrieval-only summary",
        "",
        f"- Tasks: {summary['task_count']}",
        f"- Drop-set: {summary['drop_set']} "
        f"(excluded {summary['excluded_task_count']} tasks)",
        f"- Official same-schema route: {summary['same_schema_route_count']}",
        f"- Official field-RAG route: {summary['field_route_count']}",
        (
            "- Field-embedding route with pair diagnostics: "
            f"{summary['field_embeddings_route_count']}"
        ),
        f"- Retrieval failed after fallback: {summary['retrieval_failed_count']}",
        f"- Structural same-schema tasks: {summary['structural_same_schema_count']}",
        (
            "- Structural same-schema but field fallback: "
            f"{summary['structural_same_schema_but_field_route_count']}"
        ),
        f"- Non-same-schema tasks: {summary['non_same_schema_count']}",
        f"- Runtime: {summary['elapsed_s']} s",
        f"- Cached embedding texts: {summary['embedding_cache_size']}",
        "",
        "## Distributions",
        "",
        _describe_bullet(
            "Selected same-schema min similarity",
            summary["same_schema_selected_min_similarity"],
        ),
        _describe_bullet(
            "Same-schema candidate max similarity",
            summary["same_schema_candidate_max_similarity"],
        ),
        _describe_bullet(
            "Field pair-score gain vs independent top-2",
            summary["field_pair_score_gain_vs_independent"],
        ),
        _describe_bullet(
            "Field-score sum loss vs independent top-2",
            summary["field_score_sum_loss_vs_independent"],
        ),
        _describe_bullet(
            "Field coverage gain vs independent top-2",
            summary["field_coverage_gain_vs_independent"],
        ),
        "",
        "## By Domain",
        "",
        "| domain | tasks | same_schema_route | field_route | retrieval_failed |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for domain, payload in summary["by_domain"].items():
        lines.append(
            f"| {domain} | {payload['tasks']} | "
            f"{payload['same_schema_route']} | {payload['field_route']} | "
            f"{payload['retrieval_failed']} |"
        )
    return "\n".join(lines) + "\n"


def _trace_check_markdown(
    records: Sequence[dict[str, Any]],
    summary: dict[str, Any],
    *,
    trace_examples: int,
) -> str:
    same_examples = sorted(
        (record for record in records if record["official_uses_same_schema"]),
        key=lambda record: (
            record.get("selected_same_schema_min_similarity") or 0.0,
            record["task_id"],
        ),
    )[: max(1, trace_examples // 3)]
    field_diff_examples = [
        record
        for record in records
        if record["default_vs_independent_same_pair"] is False
    ][: max(1, trace_examples // 3)]
    field_same_examples = [
        record
        for record in records
        if record["default_vs_independent_same_pair"] is True
    ][: max(1, trace_examples - len(same_examples) - len(field_diff_examples))]
    examples = [*same_examples, *field_diff_examples, *field_same_examples]

    lines = [
        "# Retrieval trace check",
        "",
        "Compact examples for manual inspection. Full traces are in "
        "`test_retrieval_trace.json`.",
        "",
        f"- Tasks: {summary['task_count']}",
        f"- Same-schema route: {summary['same_schema_route_count']}",
        f"- Field route: {summary['field_route_count']}",
        "",
    ]
    for record in examples[:trace_examples]:
        lines.extend(_record_trace_lines(record))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _record_trace_lines(record: dict[str, Any]) -> list[str]:
    lines = [
        f"## {record['task_id']}",
        "",
        f"- Domain/schema: `{record['domain']}` / `{record['schema_title']}`",
        f"- Fields/gold keys: {record['field_count']} / {record['gold_keys']}",
        (
            f"- Route: `{record['official_selection_method']}` "
            f"(structural same-schema candidates: {record['structural_same_schema_count']})"
        ),
        "- Official selected: " + _join_ids(record["official_selected_case_ids"]),
    ]
    if record["official_uses_same_schema"]:
        candidates = sorted(
            record["same_schema_candidates"],
            key=lambda item: item.get("similarity") or 0.0,
            reverse=True,
        )
        rendered = [
            f"{item['case_id']}={item.get('similarity')}"
            for item in candidates[:5]
        ]
        lines.append("- Same-schema candidates: " + _join_ids(rendered))
    else:
        lines.append(
            "- Independent top-2: " + _join_ids(record["independent_top2_case_ids"])
        )
        lines.append(
            "- Official field metrics: "
            + _field_metrics_text(record["official_field_metrics"])
        )
        lines.append(
            "- Independent field metrics: "
            + _field_metrics_text(record["independent_field_metrics"])
        )
        lines.append(
            "- Deltas vs independent: "
            f"pair_score={record['pair_score_gain_vs_independent']}, "
            f"field_sum_loss={record['field_score_sum_loss_vs_independent']}, "
            f"coverage={record['coverage_gain_vs_independent']}"
        )
    return lines


def _write_csv(path: Path, records: Sequence[dict[str, Any]]) -> None:
    fieldnames = [
        "task_id",
        "domain",
        "schema_title",
        "field_count",
        "gold_keys",
        "input_chars",
        "field_parse_error",
        "structural_same_schema_count",
        "same_schema_above_threshold_count",
        "same_schema_candidate_max_similarity",
        "selected_same_schema_min_similarity",
        "official_selection_method",
        "official_uses_same_schema",
        "official_selected_case_ids",
        "official_selected_scores",
        "independent_top2_case_ids",
        "default_vs_independent_same_pair",
        "pair_score_gain_vs_independent",
        "field_score_sum_loss_vs_independent",
        "coverage_gain_vs_independent",
        "official_pair_score",
        "official_field_score_sum",
        "official_coverage_ratio",
        "independent_pair_score",
        "independent_field_score_sum",
        "independent_coverage_ratio",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            official = record.get("official_field_metrics") or {}
            independent = record.get("independent_field_metrics") or {}
            writer.writerow(
                {
                    "task_id": record["task_id"],
                    "domain": record["domain"],
                    "schema_title": record["schema_title"],
                    "field_count": record["field_count"],
                    "gold_keys": record["gold_keys"],
                    "input_chars": record["input_chars"],
                    "field_parse_error": record["field_parse_error"],
                    "structural_same_schema_count": record["structural_same_schema_count"],
                    "same_schema_above_threshold_count": record[
                        "same_schema_above_threshold_count"
                    ],
                    "same_schema_candidate_max_similarity": record[
                        "same_schema_candidate_max_similarity"
                    ],
                    "selected_same_schema_min_similarity": record[
                        "selected_same_schema_min_similarity"
                    ],
                    "official_selection_method": record["official_selection_method"],
                    "official_uses_same_schema": record["official_uses_same_schema"],
                    "official_selected_case_ids": ";".join(
                        record["official_selected_case_ids"]
                    ),
                    "official_selected_scores": ";".join(
                        str(value) for value in record["official_selected_scores"]
                    ),
                    "independent_top2_case_ids": ";".join(
                        record["independent_top2_case_ids"]
                    ),
                    "default_vs_independent_same_pair": record[
                        "default_vs_independent_same_pair"
                    ],
                    "pair_score_gain_vs_independent": record[
                        "pair_score_gain_vs_independent"
                    ],
                    "field_score_sum_loss_vs_independent": record[
                        "field_score_sum_loss_vs_independent"
                    ],
                    "coverage_gain_vs_independent": record[
                        "coverage_gain_vs_independent"
                    ],
                    "official_pair_score": official.get("pair_score"),
                    "official_field_score_sum": official.get("field_score_sum"),
                    "official_coverage_ratio": official.get("coverage_ratio"),
                    "independent_pair_score": independent.get("pair_score"),
                    "independent_field_score_sum": independent.get("field_score_sum"),
                    "independent_coverage_ratio": independent.get("coverage_ratio"),
                }
            )


def _field_selection_metrics(diagnostics: dict[str, Any]) -> dict[str, Any]:
    considered = diagnostics.get("considered_cases")
    selected_ids = diagnostics.get("selected_case_ids")
    task_fields = diagnostics.get("task_schema_fields") or []
    if not isinstance(considered, list) or not selected_ids:
        return {}

    by_id = {item.get("case_id"): item for item in considered if isinstance(item, dict)}
    selected = [by_id[case_id] for case_id in selected_ids if case_id in by_id]
    vectors = [
        np.asarray(item.get("similarity_vector") or [], dtype=np.float32)
        for item in selected
    ]
    vectors = [vector for vector in vectors if vector.size > 0]
    field_scores = [
        float(item.get("field_score") or item.get("score") or 0.0)
        for item in selected
    ]
    if not vectors:
        return {
            "selected_case_ids": list(selected_ids),
            "field_score_sum": round(sum(field_scores), 6),
        }

    stacked = np.vstack(vectors)
    max_by_field = np.max(stacked, axis=0)
    covered = max_by_field > 0.0
    pair_score = None
    if len(vectors) >= 2:
        pair_score = _pair_score(vectors[0], vectors[1])

    return {
        "selected_case_ids": list(selected_ids),
        "field_score_sum": round(sum(field_scores), 6),
        "pair_score": round(pair_score, 6) if pair_score is not None else None,
        "coverage_count": int(np.sum(covered)),
        "coverage_ratio": round(
            float(np.sum(covered)) / len(task_fields), 6
        )
        if task_fields
        else None,
        "mean_max_field_similarity": round(float(np.mean(max_by_field)), 6),
        "min_max_field_similarity": round(float(np.min(max_by_field)), 6),
    }


def _compact_considered_cases(diagnostics: dict[str, Any]) -> list[dict[str, Any]]:
    considered = diagnostics.get("considered_cases")
    if not isinstance(considered, list):
        return []
    compact = []
    for item in considered:
        if not isinstance(item, dict):
            continue
        compact.append(
            {
                "case_id": item.get("case_id"),
                "domain": item.get("domain"),
                "selected": item.get("selected"),
                "rank": item.get("rank"),
                "score": item.get("score"),
                "field_score": item.get("field_score"),
                "similarity_vector": item.get("similarity_vector"),
                "best_fsp_field_by_task_field": item.get(
                    "best_fsp_field_by_task_field"
                ),
            }
        )
    return compact


def _same_schema_candidates(diagnostics: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = diagnostics.get("same_schema_candidates")
    if not isinstance(candidates, list):
        return []
    out = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "case_id": item.get("case_id"),
                "domain": item.get("domain"),
                "selected_by_threshold": item.get("selected_by_threshold"),
                "similarity": _round_or_none(item.get("similarity")),
            }
        )
    return out


def _selected_case_counts(records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for record in records:
        for case_id in record["official_selected_case_ids"]:
            counts[case_id] = counts.get(case_id, 0) + 1
    return [
        {"case_id": case_id, "count": count}
        for case_id, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def _load_tasks(data_dir: Path, *, limit: int | None = None) -> list[Task]:
    paths = sorted(data_dir.glob("*.json"))
    if limit is not None:
        paths = paths[:limit]
    return [Task.load(path) for path in paths]


def apply_drop_set(tasks: Sequence[Task], drop_set: str) -> list[Task]:
    if drop_set == "none":
        return list(tasks)
    if drop_set != "official":
        raise ValueError(f"unknown drop-set: {drop_set}")
    return [task for task in tasks if not _is_official_drop_task_id(task.id)]


def _is_official_drop_task_id(task_id: str) -> bool:
    return _domain_from_task_id(task_id) in {
        "medical_trials",
        "cultural_monuments",
        "stem_biology",
    }


def _uses_same_schema_route(results: Sequence[Any]) -> bool:
    return bool(results) and all(getattr(result, "schema_match", False) for result in results)


def _gold_key_count(task: Task) -> int:
    if task.output is None:
        return 0
    return len(flatten_json(task.output, expand_lists=False))


def _domain_from_task_id(task_id: str) -> str:
    value = task_id
    if value.startswith("test_"):
        value = value[len("test_") :]
    value = re.sub(r"_\d+$", "", value)
    return value or task_id


def _schema_title(task: Task) -> str:
    title = task.target_schema.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    return "Unknown"


def _case_domain(case_id: str, cases: Sequence[StructuredFspCase]) -> str:
    for case in cases:
        if case.id == case_id:
            return case.domain
    return ""


def _pair_score(first: np.ndarray, second: np.ndarray) -> float:
    return float(np.linalg.norm(first + second) + np.linalg.norm(first - second))


def _difference(a: Any, b: Any) -> float | None:
    if a is None or b is None:
        return None
    return round(float(a) - float(b), 6)


def _round_or_none(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)


def _numeric_values(values: Iterable[Any]) -> list[float]:
    out = []
    for value in values:
        if value is None:
            continue
        number = float(value)
        if math.isfinite(number):
            out.append(number)
    return out


def _describe(values: Sequence[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0}
    sorted_values = sorted(values)
    return {
        "n": len(sorted_values),
        "min": round(sorted_values[0], 6),
        "p25": round(_quantile(sorted_values, 0.25), 6),
        "mean": round(statistics.fmean(sorted_values), 6),
        "median": round(statistics.median(sorted_values), 6),
        "p75": round(_quantile(sorted_values, 0.75), 6),
        "max": round(sorted_values[-1], 6),
    }


def _quantile(sorted_values: Sequence[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    pos = (len(sorted_values) - 1) * q
    lower = int(math.floor(pos))
    upper = int(math.ceil(pos))
    if lower == upper:
        return sorted_values[lower]
    weight = pos - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def _max_or_none(values: Iterable[Any]) -> float | None:
    nums = _numeric_values(values)
    return round(max(nums), 6) if nums else None


def _min_or_none(values: Iterable[Any]) -> float | None:
    nums = _numeric_values(values)
    return round(min(nums), 6) if nums else None


def _mean_or_none(values: Iterable[Any]) -> float | None:
    nums = _numeric_values(values)
    return round(statistics.fmean(nums), 6) if nums else None


def _describe_bullet(label: str, payload: dict[str, Any]) -> str:
    if not payload or payload.get("n", 0) == 0:
        return f"- {label}: n=0"
    return (
        f"- {label}: n={payload['n']}, min={payload['min']}, "
        f"p25={payload['p25']}, mean={payload['mean']}, "
        f"median={payload['median']}, p75={payload['p75']}, max={payload['max']}"
    )


def _field_metrics_text(payload: dict[str, Any]) -> str:
    if not payload:
        return "n/a"
    return (
        f"pair={payload.get('pair_score')}, "
        f"field_sum={payload.get('field_score_sum')}, "
        f"coverage={payload.get('coverage_ratio')}"
    )


def _join_ids(values: Sequence[Any]) -> str:
    return ", ".join(str(value) for value in values) if values else "n/a"


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
