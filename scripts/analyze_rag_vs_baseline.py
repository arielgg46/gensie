from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compare existing enriched-schema-rag final_results against baseline "
            "using task-level rows already joined with retrieval diagnostics."
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
        default=Path("analysis/rag_vs_baseline"),
    )
    parser.add_argument(
        "--doc",
        type=Path,
        default=Path("docs/analisis-rag-vs-baseline-preliminar.md"),
    )
    args = parser.parse_args()

    rows = load_joined_rows(args.joined_csv)
    seen_by_task = load_seen_by_task(args.schema_overlap_json)
    add_seen_and_bins(rows, seen_by_task)

    comparisons = find_comparisons(rows)
    if not comparisons:
        raise SystemExit("No baseline vs enriched-schema-rag comparisons found.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.doc.parent.mkdir(parents=True, exist_ok=True)

    summary_rows: list[dict[str, Any]] = []
    task_delta_rows: list[dict[str, Any]] = []
    overview_rows: list[dict[str, Any]] = []

    for comparison in comparisons:
        baseline_rows = rows_by_task(comparison["baseline_rows"])
        rag_rows = rows_by_task(comparison["rag_rows"])
        common_task_ids = sorted(set(baseline_rows) & set(rag_rows))
        deltas = task_delta_rows_for_pair(
            comparison,
            baseline_rows,
            rag_rows,
            common_task_ids,
        )
        task_delta_rows.extend(deltas)
        summary_rows.extend(
            grouped_summary_rows(
                comparison,
                baseline_rows,
                rag_rows,
                deltas,
                common_task_ids,
            )
        )
        overview_rows.append(overview_row(comparison, deltas, baseline_rows, rag_rows))

    write_csv(args.output_dir / "rag_vs_baseline_summary.csv", summary_rows)
    write_csv(args.output_dir / "rag_vs_baseline_task_deltas.csv", task_delta_rows)
    write_csv(args.output_dir / "rag_vs_baseline_overview.csv", overview_rows)
    write_json(
        args.output_dir / "rag_vs_baseline_summary.json",
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
    (args.output_dir / "rag_vs_baseline_summary.md").write_text(
        markdown, encoding="utf-8"
    )
    args.doc.write_text(markdown, encoding="utf-8")

    print(f"Wrote RAG vs baseline analysis to {args.output_dir}")
    print(f"Wrote preliminary note to {args.doc}")
    print(f"Comparisons={len(comparisons)} task_delta_rows={len(task_delta_rows)}")


def load_joined_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in read_csv(path):
        row = dict(raw)
        for key in (
            "tps",
            "gold_keys",
            "system_keys",
            "system_minus_gold",
            "elapsed_s",
            "tokens_input",
            "tokens_output",
            "tokens_total",
            "calls",
            "field_count",
            "input_chars",
            "selected_same_schema_min_similarity",
            "pair_score_gain_vs_independent",
            "coverage_gain_vs_independent",
        ):
            row[key] = parse_float(row.get(key))
        row["calls_zero"] = parse_bool(row.get("calls_zero"))
        row["task_f1"] = f1_from_counts(row["tps"], row["gold_keys"], row["system_keys"])
        row["task_precision"] = (
            row["tps"] / row["system_keys"] if row["system_keys"] else 0.0
        )
        row["task_recall"] = row["tps"] / row["gold_keys"] if row["gold_keys"] else 0.0
        rows.append(row)
    if not rows:
        raise ValueError(f"No rows found in {path}")
    return rows


def load_seen_by_task(path: Path) -> dict[str, bool]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    seen_by_task: dict[str, bool] = {}
    for schema in payload.get("schemas", []):
        seen = bool(schema.get("seen_in_dev"))
        for task_id in schema.get("task_ids", []):
            seen_by_task[str(task_id)] = seen
    return seen_by_task


def add_seen_and_bins(rows: list[dict[str, Any]], seen_by_task: Mapping[str, bool]) -> None:
    task_features: dict[str, dict[str, Any]] = {}
    for row in rows:
        task_features.setdefault(
            str(row["task_id"]),
            {
                "field_count": row["field_count"],
                "gold_keys": row["gold_keys"],
                "input_chars": row["input_chars"],
            },
        )

    input_thresholds = tertile_thresholds(
        [feature["input_chars"] for feature in task_features.values()]
    )
    for row in rows:
        task_id = str(row["task_id"])
        row["seen_in_dev"] = seen_by_task.get(task_id, False)
        row["seen_group"] = "seen_schema" if row["seen_in_dev"] else "unseen_schema"
        row["field_count_bin"] = field_count_bin(row["field_count"])
        row["gold_keys_bin"] = gold_keys_bin(row["gold_keys"])
        row["input_chars_bin"] = value_tertile(row["input_chars"], input_thresholds)


def find_comparisons(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    by_model_pipeline: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        by_model_pipeline.setdefault((str(row["model"]), str(row["pipeline"])), []).append(row)

    comparisons: list[dict[str, Any]] = []
    for model in sorted({str(row["model"]) for row in rows}):
        baseline_rows = by_model_pipeline.get((model, "baseline"))
        rag_rows = by_model_pipeline.get((model, "enriched-schema-rag"))
        if not baseline_rows or not rag_rows:
            continue
        short_model = short_model_label(model)
        comparisons.append(
            {
                "comparison": f"{short_model}: enriched-schema-rag vs baseline",
                "model": model,
                "short_model": short_model,
                "baseline_pipeline": "baseline",
                "candidate_pipeline": "enriched-schema-rag",
                "baseline_rows": baseline_rows,
                "rag_rows": rag_rows,
            }
        )
    return comparisons


def rows_by_task(rows: Sequence[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        task_id = str(row["task_id"])
        if task_id in out:
            raise ValueError(f"Duplicate task_id in run rows: {task_id}")
        out[task_id] = row
    return out


def task_delta_rows_for_pair(
    comparison: Mapping[str, Any],
    baseline_rows: Mapping[str, dict[str, Any]],
    rag_rows: Mapping[str, dict[str, Any]],
    task_ids: Sequence[str],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for task_id in task_ids:
        baseline = baseline_rows[task_id]
        rag = rag_rows[task_id]
        out.append(
            {
                "comparison": comparison["comparison"],
                "model": comparison["model"],
                "short_model": comparison["short_model"],
                "task_id": task_id,
                "domain": rag["domain"],
                "schema_title": rag["schema_title"],
                "seen_group": rag["seen_group"],
                "route_group": rag["route_group"],
                "field_count": int_value(rag["field_count"]),
                "field_count_bin": rag["field_count_bin"],
                "gold_keys": int_value(rag["gold_keys"]),
                "gold_keys_bin": rag["gold_keys_bin"],
                "input_chars": int_value(rag["input_chars"]),
                "input_chars_bin": rag["input_chars_bin"],
                "same_similarity_bin": rag.get("same_similarity_bin") or "",
                "pair_gain_bin": rag.get("pair_gain_bin") or "",
                "coverage_gain_group": rag.get("coverage_gain_group") or "",
                "baseline_f1": round_float(baseline["task_f1"]),
                "rag_f1": round_float(rag["task_f1"]),
                "delta_f1": round_float(rag["task_f1"] - baseline["task_f1"]),
                "baseline_precision": round_float(baseline["task_precision"]),
                "rag_precision": round_float(rag["task_precision"]),
                "delta_precision": round_float(
                    rag["task_precision"] - baseline["task_precision"]
                ),
                "baseline_recall": round_float(baseline["task_recall"]),
                "rag_recall": round_float(rag["task_recall"]),
                "delta_recall": round_float(rag["task_recall"] - baseline["task_recall"]),
                "baseline_tps": round_float(baseline["tps"]),
                "rag_tps": round_float(rag["tps"]),
                "delta_tps": round_float(rag["tps"] - baseline["tps"]),
                "baseline_system_minus_gold": int_value(baseline["system_minus_gold"]),
                "rag_system_minus_gold": int_value(rag["system_minus_gold"]),
                "delta_system_minus_gold": int_value(
                    rag["system_minus_gold"] - baseline["system_minus_gold"]
                ),
                "baseline_tokens_total": int_value(baseline["tokens_total"]),
                "rag_tokens_total": int_value(rag["tokens_total"]),
                "delta_tokens_total": int_value(
                    rag["tokens_total"] - baseline["tokens_total"]
                ),
                "baseline_elapsed_s": round_float(baseline["elapsed_s"]),
                "rag_elapsed_s": round_float(rag["elapsed_s"]),
                "delta_elapsed_s": round_float(rag["elapsed_s"] - baseline["elapsed_s"]),
                "baseline_calls": int_value(baseline["calls"]),
                "rag_calls": int_value(rag["calls"]),
                "baseline_calls_zero": bool(baseline["calls_zero"]),
                "rag_calls_zero": bool(rag["calls_zero"]),
                "both_calls_nonzero": (
                    not bool(baseline["calls_zero"]) and not bool(rag["calls_zero"])
                ),
                "baseline_status": baseline["status"],
                "rag_status": rag["status"],
            }
        )
    return out


def grouped_summary_rows(
    comparison: Mapping[str, Any],
    baseline_rows: Mapping[str, dict[str, Any]],
    rag_rows: Mapping[str, dict[str, Any]],
    deltas: Sequence[dict[str, Any]],
    task_ids: Sequence[str],
) -> list[dict[str, Any]]:
    delta_by_task = {str(row["task_id"]): row for row in deltas}
    groups: list[tuple[str, str, list[str]]] = [("all", "all", list(task_ids))]

    both_nonzero = [
        task_id for task_id in task_ids if delta_by_task[task_id]["both_calls_nonzero"]
    ]
    groups.append(("calls", "both_calls_nonzero", both_nonzero))

    group_fields = [
        ("seen_group", "seen_group"),
        ("route_group", "route_group"),
        ("domain", "domain"),
        ("schema_title", "schema_title"),
        ("field_count_bin", "field_count_bin"),
        ("gold_keys_bin", "gold_keys_bin"),
        ("input_chars_bin", "input_chars_bin"),
        ("same_similarity_bin", "same_similarity_bin"),
        ("pair_gain_bin", "pair_gain_bin"),
        ("coverage_gain_group", "coverage_gain_group"),
    ]
    for family, key in group_fields:
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

    rows: list[dict[str, Any]] = []
    for family, group, subset_ids in groups:
        if not subset_ids:
            continue
        base_metrics = metrics_for_rows([baseline_rows[task_id] for task_id in subset_ids])
        rag_metrics = metrics_for_rows([rag_rows[task_id] for task_id in subset_ids])
        subset_deltas = [delta_by_task[task_id] for task_id in subset_ids]
        rows.append(
            {
                "comparison": comparison["comparison"],
                "model": comparison["model"],
                "short_model": comparison["short_model"],
                "group_family": family,
                "group": group,
                "task_count": len(subset_ids),
                "baseline_precision": base_metrics["precision"],
                "rag_precision": rag_metrics["precision"],
                "delta_precision": round_float(
                    rag_metrics["precision"] - base_metrics["precision"]
                ),
                "baseline_recall": base_metrics["recall"],
                "rag_recall": rag_metrics["recall"],
                "delta_recall": round_float(rag_metrics["recall"] - base_metrics["recall"]),
                "baseline_f1": base_metrics["f1"],
                "rag_f1": rag_metrics["f1"],
                "delta_f1": round_float(rag_metrics["f1"] - base_metrics["f1"]),
                "baseline_tokens_avg": base_metrics["tokens_avg"],
                "rag_tokens_avg": rag_metrics["tokens_avg"],
                "delta_tokens_avg": round_float(
                    rag_metrics["tokens_avg"] - base_metrics["tokens_avg"]
                ),
                "baseline_elapsed_avg_s": base_metrics["elapsed_avg_s"],
                "rag_elapsed_avg_s": rag_metrics["elapsed_avg_s"],
                "delta_elapsed_avg_s": round_float(
                    rag_metrics["elapsed_avg_s"] - base_metrics["elapsed_avg_s"]
                ),
                "baseline_calls_zero": base_metrics["calls_zero"],
                "rag_calls_zero": rag_metrics["calls_zero"],
                "baseline_system_minus_gold_avg": base_metrics[
                    "system_minus_gold_avg"
                ],
                "rag_system_minus_gold_avg": rag_metrics["system_minus_gold_avg"],
                "delta_task_f1_mean": round_float(
                    mean(row["delta_f1"] for row in subset_deltas)
                ),
                "improved_tasks": sum(1 for row in subset_deltas if row["delta_f1"] > 0),
                "regressed_tasks": sum(1 for row in subset_deltas if row["delta_f1"] < 0),
                "unchanged_tasks": sum(1 for row in subset_deltas if row["delta_f1"] == 0),
            }
        )
    return rows


def overview_row(
    comparison: Mapping[str, Any],
    deltas: Sequence[dict[str, Any]],
    baseline_rows: Mapping[str, dict[str, Any]],
    rag_rows: Mapping[str, dict[str, Any]],
) -> dict[str, Any]:
    task_ids = [str(row["task_id"]) for row in deltas]
    official_base = metrics_for_rows([baseline_rows[task_id] for task_id in task_ids])
    official_rag = metrics_for_rows([rag_rows[task_id] for task_id in task_ids])
    nonzero_ids = [str(row["task_id"]) for row in deltas if row["both_calls_nonzero"]]
    nonzero_base = metrics_for_rows([baseline_rows[task_id] for task_id in nonzero_ids])
    nonzero_rag = metrics_for_rows([rag_rows[task_id] for task_id in nonzero_ids])
    return {
        "comparison": comparison["comparison"],
        "model": comparison["model"],
        "short_model": comparison["short_model"],
        "task_count": len(task_ids),
        "official_baseline_f1": official_base["f1"],
        "official_rag_f1": official_rag["f1"],
        "official_delta_f1": round_float(official_rag["f1"] - official_base["f1"]),
        "both_calls_nonzero_task_count": len(nonzero_ids),
        "nonzero_baseline_f1": nonzero_base["f1"],
        "nonzero_rag_f1": nonzero_rag["f1"],
        "nonzero_delta_f1": round_float(nonzero_rag["f1"] - nonzero_base["f1"]),
        "mean_task_delta_f1": round_float(mean(row["delta_f1"] for row in deltas)),
        "median_task_delta_f1": round_float(median(row["delta_f1"] for row in deltas)),
        "improved_tasks": sum(1 for row in deltas if row["delta_f1"] > 0),
        "regressed_tasks": sum(1 for row in deltas if row["delta_f1"] < 0),
        "unchanged_tasks": sum(1 for row in deltas if row["delta_f1"] == 0),
        "large_improvement_tasks_delta_ge_0_10": sum(
            1 for row in deltas if row["delta_f1"] >= 0.10
        ),
        "large_regression_tasks_delta_le_neg_0_10": sum(
            1 for row in deltas if row["delta_f1"] <= -0.10
        ),
        "baseline_tokens_avg": official_base["tokens_avg"],
        "rag_tokens_avg": official_rag["tokens_avg"],
        "delta_tokens_avg": round_float(
            official_rag["tokens_avg"] - official_base["tokens_avg"]
        ),
    }


def metrics_for_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    rows = list(rows)
    tps = sum(float(row["tps"]) for row in rows)
    gold = sum(int_value(row["gold_keys"]) for row in rows)
    system = sum(int_value(row["system_keys"]) for row in rows)
    precision = tps / system if system else 0.0
    recall = tps / gold if gold else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    calls_zero = sum(1 for row in rows if bool(row["calls_zero"]))
    return {
        "precision": round_float(precision),
        "recall": round_float(recall),
        "f1": round_float(f1),
        "calls_zero": calls_zero,
        "tokens_avg": round_float(mean(row["tokens_total"] for row in rows), 3),
        "elapsed_avg_s": round_float(mean(row["elapsed_s"] for row in rows), 3),
        "system_minus_gold_avg": round_float(
            mean(row["system_minus_gold"] for row in rows), 3
        ),
    }


def render_markdown(
    overview_rows: Sequence[Mapping[str, Any]],
    summary_rows: Sequence[Mapping[str, Any]],
    task_delta_rows: Sequence[Mapping[str, Any]],
) -> str:
    lines = [
        "# Analisis RAG vs baseline",
        "",
        "Este documento cruza resultados ya existentes. No corre pipelines nuevos "
        "ni usa details por campo.",
        "",
        "Entradas:",
        "",
        "- `analysis/final_results_retrieval/joined_task_metrics.csv`",
        "- `analysis/test_schema_subsets/schema_overlap.json`",
        "",
        "Salidas principales:",
        "",
        "- `analysis/rag_vs_baseline/rag_vs_baseline_overview.csv`",
        "- `analysis/rag_vs_baseline/rag_vs_baseline_summary.csv`",
        "- `analysis/rag_vs_baseline/rag_vs_baseline_task_deltas.csv`",
        "",
        "## Resumen oficial",
        "",
        table(
            overview_rows,
            [
                "short_model",
                "task_count",
                "official_baseline_f1",
                "official_rag_f1",
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
                "both_calls_nonzero_task_count",
                "nonzero_baseline_f1",
                "nonzero_rag_f1",
                "nonzero_delta_f1",
            ],
        ),
        "",
        "## Seen vs unseen",
        "",
        table(
            select_summary(summary_rows, "seen_group"),
            summary_columns(),
        ),
        "",
        "## Seen vs unseen, calls>0 en ambos lados",
        "",
        table(
            select_summary(summary_rows, "seen_group_both_calls_nonzero"),
            summary_columns(),
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
        "## Complejidad por gold keys",
        "",
        table(select_summary(summary_rows, "gold_keys_bin"), summary_columns()),
        "",
        "## Complejidad por numero de campos",
        "",
        table(select_summary(summary_rows, "field_count_bin"), summary_columns()),
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
            "- RAG mejora al baseline en los dos modelos en la metrica oficial.",
            "- La mejora se mantiene al excluir tasks donde alguno de los dos lados tiene `calls=0`.",
            "- El corte seen/unseen debe leerse junto con la ruta de retrieval: en este test, los schemas vistos coinciden con la ruta same-schema y los no vistos con field-RAG/fallos.",
            "- Las tablas por task sirven para inspeccion y seleccion de casos; las conclusiones agregadas deben usar las filas micro de `rag_vs_baseline_summary.csv`.",
        ]
    )
    return "\n".join(lines) + "\n"


def select_summary(
    rows: Sequence[Mapping[str, Any]],
    family: str,
) -> list[Mapping[str, Any]]:
    return [row for row in rows if row["group_family"] == family]


def top_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    reverse: bool,
    limit: int = 8,
) -> list[Mapping[str, Any]]:
    return sorted(rows, key=lambda row: float(row["delta_f1"]), reverse=reverse)[:limit]


def summary_columns() -> list[str]:
    return [
        "short_model",
        "group",
        "task_count",
        "baseline_f1",
        "rag_f1",
        "delta_f1",
        "baseline_precision",
        "rag_precision",
        "baseline_recall",
        "rag_recall",
        "baseline_calls_zero",
        "rag_calls_zero",
    ]


def extreme_columns() -> list[str]:
    return [
        "task_id",
        "schema_title",
        "route_group",
        "seen_group",
        "baseline_f1",
        "rag_f1",
        "delta_f1",
        "baseline_system_minus_gold",
        "rag_system_minus_gold",
        "baseline_calls",
        "rag_calls",
    ]


def field_count_bin(value: Any) -> str:
    count = int_value(value)
    if count <= 3:
        return "fields_01_03"
    if count <= 6:
        return "fields_04_06"
    return "fields_07_plus"


def gold_keys_bin(value: Any) -> str:
    count = int_value(value)
    if count <= 5:
        return "gold_keys_01_05"
    if count <= 8:
        return "gold_keys_06_08"
    return "gold_keys_09_plus"


def f1_from_counts(tps: Any, gold_keys: Any, system_keys: Any) -> float:
    tps_f = float(tps or 0.0)
    gold = float(gold_keys or 0.0)
    system = float(system_keys or 0.0)
    precision = tps_f / system if system else 0.0
    recall = tps_f / gold if gold else 0.0
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def tertile_thresholds(values: Sequence[Any]) -> tuple[float, float] | None:
    nums = sorted(float(value) for value in values if value not in (None, ""))
    if len(nums) < 3:
        return None
    return quantile(nums, 1 / 3), quantile(nums, 2 / 3)


def value_tertile(value: Any, thresholds: tuple[float, float] | None) -> str:
    if value in (None, "") or thresholds is None:
        return ""
    low, high = thresholds
    value_f = float(value)
    if value_f <= low:
        return "low"
    if value_f <= high:
        return "mid"
    return "high"


def quantile(sorted_values: Sequence[float], q: float) -> float:
    pos = (len(sorted_values) - 1) * q
    lower = int(math.floor(pos))
    upper = int(math.ceil(pos))
    if lower == upper:
        return sorted_values[lower]
    weight = pos - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def short_model_label(model: str) -> str:
    value = model.lower()
    if "qwen" in value:
        return "qwen3-14b"
    if "gemma" in value or "gema" in value:
        return "gemma-4-e4b-it"
    return model


def mean(values: Iterable[Any]) -> float:
    nums = [float(value) for value in values if value not in (None, "")]
    return statistics.fmean(nums) if nums else 0.0


def median(values: Iterable[Any]) -> float:
    nums = sorted(float(value) for value in values if value not in (None, ""))
    return statistics.median(nums) if nums else 0.0


def parse_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def parse_bool(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def int_value(value: Any) -> int:
    return int(round(float(value or 0.0)))


def round_float(value: Any, digits: int = 6) -> float:
    return round(float(value or 0.0), digits)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def table(rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(format_cell(row.get(column)) for column in columns)
            + " |"
        )
    return "\n".join(lines)


def format_cell(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6f}".rstrip("0").rstrip(".")
    return str(value) if value is not None else ""


if __name__ == "__main__":
    main()
