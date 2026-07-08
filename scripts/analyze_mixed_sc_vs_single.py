from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from analyze_rag_vs_baseline import (
    add_seen_and_bins,
    int_value,
    load_joined_rows,
    load_seen_by_task,
    mean,
    median,
    metrics_for_rows,
    round_float,
    rows_by_task,
    short_model_label,
    table,
    write_csv,
    write_json,
)


MIXED_PIPELINE = "mixed-extractors-self-consistency-rag"
REFERENCE_PIPELINES = (
    "enriched-schema-rag",
    "enriched-inline-reasoning-rag",
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compare existing mixed self-consistency runs against available "
            "single-call extractors."
        )
    )
    parser.add_argument(
        "--joined-csv",
        type=Path,
        default=Path("analysis/final_results_retrieval/joined_task_metrics.csv"),
    )
    parser.add_argument(
        "--schema-overlap-json",
        type=Path,
        default=Path("analysis/test_schema_subsets/schema_overlap.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("analysis/mixed_sc_vs_single"),
    )
    parser.add_argument(
        "--doc",
        type=Path,
        default=Path("docs/analisis-mixed-sc-vs-single-preliminar.md"),
    )
    args = parser.parse_args()

    rows = load_joined_rows(args.joined_csv)
    add_seen_and_bins(rows, load_seen_by_task(args.schema_overlap_json))
    comparisons = find_comparisons(rows)
    if not comparisons:
        raise SystemExit("No mixed self-consistency comparisons found.")

    overview_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    task_delta_rows: list[dict[str, Any]] = []

    for comparison in comparisons:
        reference_rows = rows_by_task(comparison["reference_rows"])
        mixed_rows = rows_by_task(comparison["mixed_rows"])
        task_ids = sorted(set(reference_rows) & set(mixed_rows))
        deltas = task_delta_rows_for_pair(
            comparison, reference_rows, mixed_rows, task_ids
        )
        task_delta_rows.extend(deltas)
        summary_rows.extend(
            grouped_summary_rows(
                comparison, reference_rows, mixed_rows, deltas, task_ids
            )
        )
        overview_rows.append(overview_row(comparison, deltas, reference_rows, mixed_rows))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.doc.parent.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "mixed_sc_vs_single_overview.csv", overview_rows)
    write_csv(args.output_dir / "mixed_sc_vs_single_summary.csv", summary_rows)
    write_csv(args.output_dir / "mixed_sc_vs_single_task_deltas.csv", task_delta_rows)
    write_json(
        args.output_dir / "mixed_sc_vs_single_summary.json",
        {
            "inputs": {
                "joined_csv": str(args.joined_csv),
                "schema_overlap_json": str(args.schema_overlap_json),
            },
            "overview": overview_rows,
            "summary": summary_rows,
        },
    )
    markdown = render_markdown(overview_rows, summary_rows, task_delta_rows)
    (args.output_dir / "mixed_sc_vs_single_summary.md").write_text(
        markdown, encoding="utf-8"
    )
    args.doc.write_text(markdown, encoding="utf-8")

    print(f"Wrote Mixed-SC analysis to {args.output_dir}")
    print(f"Wrote preliminary note to {args.doc}")
    print(f"Comparisons={len(comparisons)} task_delta_rows={len(task_delta_rows)}")


def find_comparisons(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    by_model_pipeline: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        by_model_pipeline.setdefault((str(row["model"]), str(row["pipeline"])), []).append(row)

    comparisons: list[dict[str, Any]] = []
    for model in sorted({str(row["model"]) for row in rows}):
        mixed_rows = by_model_pipeline.get((model, MIXED_PIPELINE))
        if not mixed_rows:
            continue
        for reference_pipeline in REFERENCE_PIPELINES:
            reference_rows = by_model_pipeline.get((model, reference_pipeline))
            if not reference_rows:
                continue
            short_model = short_model_label(model)
            comparisons.append(
                {
                    "comparison": f"{short_model}: Mixed-SC vs {reference_pipeline}",
                    "model": model,
                    "short_model": short_model,
                    "reference_pipeline": reference_pipeline,
                    "mixed_pipeline": MIXED_PIPELINE,
                    "reference_rows": reference_rows,
                    "mixed_rows": mixed_rows,
                }
            )
    return comparisons


def task_delta_rows_for_pair(
    comparison: Mapping[str, Any],
    reference_rows: Mapping[str, dict[str, Any]],
    mixed_rows: Mapping[str, dict[str, Any]],
    task_ids: Sequence[str],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for task_id in task_ids:
        reference = reference_rows[task_id]
        mixed = mixed_rows[task_id]
        out.append(
            {
                "comparison": comparison["comparison"],
                "model": comparison["model"],
                "short_model": comparison["short_model"],
                "reference_pipeline": comparison["reference_pipeline"],
                "task_id": task_id,
                "domain": mixed["domain"],
                "schema_title": mixed["schema_title"],
                "seen_group": mixed["seen_group"],
                "route_group": mixed["route_group"],
                "field_count": int_value(mixed["field_count"]),
                "gold_keys": int_value(mixed["gold_keys"]),
                "same_similarity_bin": mixed.get("same_similarity_bin") or "",
                "pair_gain_bin": mixed.get("pair_gain_bin") or "",
                "coverage_gain_group": mixed.get("coverage_gain_group") or "",
                "reference_f1": round_float(reference["task_f1"]),
                "mixed_f1": round_float(mixed["task_f1"]),
                "delta_f1": round_float(mixed["task_f1"] - reference["task_f1"]),
                "reference_precision": round_float(reference["task_precision"]),
                "mixed_precision": round_float(mixed["task_precision"]),
                "delta_precision": round_float(
                    mixed["task_precision"] - reference["task_precision"]
                ),
                "reference_recall": round_float(reference["task_recall"]),
                "mixed_recall": round_float(mixed["task_recall"]),
                "delta_recall": round_float(mixed["task_recall"] - reference["task_recall"]),
                "reference_system_minus_gold": int_value(reference["system_minus_gold"]),
                "mixed_system_minus_gold": int_value(mixed["system_minus_gold"]),
                "delta_system_minus_gold": int_value(
                    mixed["system_minus_gold"] - reference["system_minus_gold"]
                ),
                "reference_tokens_total": int_value(reference["tokens_total"]),
                "mixed_tokens_total": int_value(mixed["tokens_total"]),
                "delta_tokens_total": int_value(
                    mixed["tokens_total"] - reference["tokens_total"]
                ),
                "reference_elapsed_s": round_float(reference["elapsed_s"]),
                "mixed_elapsed_s": round_float(mixed["elapsed_s"]),
                "delta_elapsed_s": round_float(
                    mixed["elapsed_s"] - reference["elapsed_s"]
                ),
                "reference_calls": int_value(reference["calls"]),
                "mixed_calls": int_value(mixed["calls"]),
                "reference_calls_zero": bool(reference["calls_zero"]),
                "mixed_calls_zero": bool(mixed["calls_zero"]),
                "both_calls_nonzero": (
                    not bool(reference["calls_zero"]) and not bool(mixed["calls_zero"])
                ),
                "reference_status": reference["status"],
                "mixed_status": mixed["status"],
            }
        )
    return out


def grouped_summary_rows(
    comparison: Mapping[str, Any],
    reference_rows: Mapping[str, dict[str, Any]],
    mixed_rows: Mapping[str, dict[str, Any]],
    deltas: Sequence[dict[str, Any]],
    task_ids: Sequence[str],
) -> list[dict[str, Any]]:
    delta_by_task = {str(row["task_id"]): row for row in deltas}
    groups: list[tuple[str, str, list[str]]] = [("all", "all", list(task_ids))]
    groups.append(
        (
            "calls",
            "both_calls_nonzero",
            [
                task_id
                for task_id in task_ids
                if delta_by_task[task_id]["both_calls_nonzero"]
            ],
        )
    )
    for family, key in (
        ("seen_group", "seen_group"),
        ("route_group", "route_group"),
        ("coverage_gain_group", "coverage_gain_group"),
        ("same_similarity_bin", "same_similarity_bin"),
        ("pair_gain_bin", "pair_gain_bin"),
        ("schema_title", "schema_title"),
    ):
        values = sorted({str(delta_by_task[task_id].get(key) or "") for task_id in task_ids})
        for value in values:
            if not value:
                continue
            subset = [
                task_id
                for task_id in task_ids
                if str(delta_by_task[task_id].get(key) or "") == value
            ]
            groups.append((family, value, subset))
            nonzero_subset = [
                task_id for task_id in subset if delta_by_task[task_id]["both_calls_nonzero"]
            ]
            if nonzero_subset:
                groups.append((f"{family}_both_calls_nonzero", value, nonzero_subset))

    out: list[dict[str, Any]] = []
    for family, group, subset in groups:
        if not subset:
            continue
        reference_metrics = metrics_for_rows([reference_rows[task_id] for task_id in subset])
        mixed_metrics = metrics_for_rows([mixed_rows[task_id] for task_id in subset])
        subset_deltas = [delta_by_task[task_id] for task_id in subset]
        out.append(
            {
                "comparison": comparison["comparison"],
                "model": comparison["model"],
                "short_model": comparison["short_model"],
                "reference_pipeline": comparison["reference_pipeline"],
                "group_family": family,
                "group": group,
                "task_count": len(subset),
                "reference_f1": reference_metrics["f1"],
                "mixed_f1": mixed_metrics["f1"],
                "delta_f1": round_float(mixed_metrics["f1"] - reference_metrics["f1"]),
                "reference_precision": reference_metrics["precision"],
                "mixed_precision": mixed_metrics["precision"],
                "reference_recall": reference_metrics["recall"],
                "mixed_recall": mixed_metrics["recall"],
                "reference_tokens_avg": reference_metrics["tokens_avg"],
                "mixed_tokens_avg": mixed_metrics["tokens_avg"],
                "delta_tokens_avg": round_float(
                    mixed_metrics["tokens_avg"] - reference_metrics["tokens_avg"]
                ),
                "reference_elapsed_avg_s": reference_metrics["elapsed_avg_s"],
                "mixed_elapsed_avg_s": mixed_metrics["elapsed_avg_s"],
                "delta_elapsed_avg_s": round_float(
                    mixed_metrics["elapsed_avg_s"] - reference_metrics["elapsed_avg_s"]
                ),
                "reference_calls_zero": reference_metrics["calls_zero"],
                "mixed_calls_zero": mixed_metrics["calls_zero"],
                "delta_task_f1_mean": round_float(
                    mean(row["delta_f1"] for row in subset_deltas)
                ),
                "improved_tasks": sum(1 for row in subset_deltas if row["delta_f1"] > 0),
                "regressed_tasks": sum(1 for row in subset_deltas if row["delta_f1"] < 0),
                "unchanged_tasks": sum(1 for row in subset_deltas if row["delta_f1"] == 0),
            }
        )
    return out


def overview_row(
    comparison: Mapping[str, Any],
    deltas: Sequence[dict[str, Any]],
    reference_rows: Mapping[str, dict[str, Any]],
    mixed_rows: Mapping[str, dict[str, Any]],
) -> dict[str, Any]:
    task_ids = [str(row["task_id"]) for row in deltas]
    official_reference = metrics_for_rows([reference_rows[task_id] for task_id in task_ids])
    official_mixed = metrics_for_rows([mixed_rows[task_id] for task_id in task_ids])
    nonzero_ids = [str(row["task_id"]) for row in deltas if row["both_calls_nonzero"]]
    nonzero_reference = metrics_for_rows(
        [reference_rows[task_id] for task_id in nonzero_ids]
    )
    nonzero_mixed = metrics_for_rows([mixed_rows[task_id] for task_id in nonzero_ids])
    return {
        "comparison": comparison["comparison"],
        "model": comparison["model"],
        "short_model": comparison["short_model"],
        "reference_pipeline": comparison["reference_pipeline"],
        "task_count": len(task_ids),
        "official_reference_f1": official_reference["f1"],
        "official_mixed_f1": official_mixed["f1"],
        "official_delta_f1": round_float(
            official_mixed["f1"] - official_reference["f1"]
        ),
        "both_calls_nonzero_task_count": len(nonzero_ids),
        "nonzero_reference_f1": nonzero_reference["f1"],
        "nonzero_mixed_f1": nonzero_mixed["f1"],
        "nonzero_delta_f1": round_float(
            nonzero_mixed["f1"] - nonzero_reference["f1"]
        ),
        "mean_task_delta_f1": round_float(mean(row["delta_f1"] for row in deltas)),
        "median_task_delta_f1": round_float(median(row["delta_f1"] for row in deltas)),
        "improved_tasks": sum(1 for row in deltas if row["delta_f1"] > 0),
        "regressed_tasks": sum(1 for row in deltas if row["delta_f1"] < 0),
        "unchanged_tasks": sum(1 for row in deltas if row["delta_f1"] == 0),
        "reference_tokens_avg": official_reference["tokens_avg"],
        "mixed_tokens_avg": official_mixed["tokens_avg"],
        "delta_tokens_avg": round_float(
            official_mixed["tokens_avg"] - official_reference["tokens_avg"]
        ),
    }


def render_markdown(
    overview_rows: Sequence[Mapping[str, Any]],
    summary_rows: Sequence[Mapping[str, Any]],
    task_delta_rows: Sequence[Mapping[str, Any]],
) -> str:
    lines = [
        "# Analisis Mixed-SC vs single-call",
        "",
        "Este documento compara las corridas existentes de self-consistency con "
        "los extractores single-call disponibles. No corre nuevos pipelines ni "
        "usa details internos.",
        "",
        "Salidas principales:",
        "",
        "- `analysis/mixed_sc_vs_single/mixed_sc_vs_single_overview.csv`",
        "- `analysis/mixed_sc_vs_single/mixed_sc_vs_single_summary.csv`",
        "- `analysis/mixed_sc_vs_single/mixed_sc_vs_single_task_deltas.csv`",
        "",
        "## Resumen oficial",
        "",
        table(
            overview_rows,
            [
                "short_model",
                "reference_pipeline",
                "task_count",
                "official_reference_f1",
                "official_mixed_f1",
                "official_delta_f1",
                "improved_tasks",
                "regressed_tasks",
                "delta_tokens_avg",
            ],
        ),
        "",
        "## Sin tasks con calls=0 en ambos lados",
        "",
        table(
            overview_rows,
            [
                "short_model",
                "reference_pipeline",
                "both_calls_nonzero_task_count",
                "nonzero_reference_f1",
                "nonzero_mixed_f1",
                "nonzero_delta_f1",
            ],
        ),
        "",
        "## Rutas de retrieval",
        "",
        table(select_summary(summary_rows, "route_group"), summary_columns()),
        "",
        "## Rutas de retrieval, calls>0 en ambos lados",
        "",
        table(
            select_summary(summary_rows, "route_group_both_calls_nonzero"),
            summary_columns(),
        ),
        "",
        "## Seen vs unseen",
        "",
        table(select_summary(summary_rows, "seen_group"), summary_columns()),
        "",
        "## Cobertura del par complementario",
        "",
        table(select_summary(summary_rows, "coverage_gain_group"), summary_columns()),
        "",
        "## Top mejoras y regresiones por task",
        "",
    ]

    for comparison in sorted({str(row["comparison"]) for row in task_delta_rows}):
        rows = [row for row in task_delta_rows if row["comparison"] == comparison]
        lines.extend([f"### {comparison}", "", "Mejoras:", ""])
        lines.append(table(top_rows(rows, reverse=True), extreme_columns()))
        lines.extend(["", "Regresiones:", ""])
        lines.append(table(top_rows(rows, reverse=False), extreme_columns()))
        lines.append("")

    lines.extend(
        [
            "## Lectura preliminar",
            "",
            "- Mixed-SC se debe leer como trade-off de robustez contra costo: las tablas reportan delta F1 junto con delta de tokens y tiempo.",
            "- La comparacion mas limpia por modelo es contra `enriched-schema-rag`; en Gemma tambien existe la comparacion contra `enriched-inline-reasoning-rag`.",
            "- Las rutas same-schema y field-RAG se reportan separadas porque self-consistency no tiene el mismo comportamiento en ambos cortes.",
        ]
    )
    return "\n".join(lines) + "\n"


def select_summary(
    rows: Sequence[Mapping[str, Any]],
    family: str,
) -> list[Mapping[str, Any]]:
    return [row for row in rows if row["group_family"] == family]


def summary_columns() -> list[str]:
    return [
        "short_model",
        "reference_pipeline",
        "group",
        "task_count",
        "reference_f1",
        "mixed_f1",
        "delta_f1",
        "reference_tokens_avg",
        "mixed_tokens_avg",
        "reference_calls_zero",
        "mixed_calls_zero",
    ]


def top_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    reverse: bool,
    limit: int = 8,
) -> list[Mapping[str, Any]]:
    return sorted(rows, key=lambda row: float(row["delta_f1"]), reverse=reverse)[:limit]


def extreme_columns() -> list[str]:
    return [
        "task_id",
        "schema_title",
        "route_group",
        "seen_group",
        "reference_f1",
        "mixed_f1",
        "delta_f1",
        "reference_system_minus_gold",
        "mixed_system_minus_gold",
        "reference_calls",
        "mixed_calls",
    ]


if __name__ == "__main__":
    main()
