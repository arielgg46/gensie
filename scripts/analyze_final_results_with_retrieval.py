from __future__ import annotations

import argparse
import csv
import glob
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class RunInfo:
    label: str
    model: str
    pipeline: str
    mode: str
    path: Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Join retrieval-only diagnostics with final_results task metrics "
            "and compute grouped micro metrics."
        )
    )
    parser.add_argument(
        "--retrieval-csv",
        type=Path,
        default=Path("analysis/retrieval_only/test_retrieval_by_task.csv"),
    )
    parser.add_argument(
        "--results-glob",
        default="results/final_results*.json",
        help="Glob for final_results JSON files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("analysis/final_results_retrieval"),
    )
    parser.add_argument(
        "--drop-set",
        choices=("none", "official"),
        default="none",
        help="Exclude the official GenSIE 20-instance drop-set before joining.",
    )
    args = parser.parse_args()

    retrieval = load_retrieval(args.retrieval_csv)
    result_paths = sorted(Path(path) for path in glob.glob(args.results_glob))
    if not result_paths:
        raise SystemExit(f"No final result files matched: {args.results_glob}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    joined_rows: list[dict[str, Any]] = []
    group_rows: list[dict[str, Any]] = []
    group_rows_nonzero: list[dict[str, Any]] = []
    selected_case_rows: list[dict[str, Any]] = []
    run_rows: list[dict[str, Any]] = []
    run_rows_nonzero: list[dict[str, Any]] = []
    warnings: list[str] = []

    for result_path in result_paths:
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        run = run_info(result_path, payload)
        task_rows, run_warnings = join_run_tasks(
            run, payload, retrieval, drop_set=args.drop_set
        )
        warnings.extend(run_warnings)
        joined_rows.extend(task_rows)
        run_rows.append(run_summary_row(run, task_rows))
        nonzero_task_rows = [row for row in task_rows if not row["calls_zero"]]
        run_rows_nonzero.append(run_summary_row(run, nonzero_task_rows))
        group_rows.extend(group_metric_rows(run, task_rows))
        group_rows_nonzero.extend(group_metric_rows(run, nonzero_task_rows))
        selected_case_rows.extend(selected_case_metric_rows(run, task_rows))

    write_csv(args.output_dir / "joined_task_metrics.csv", joined_rows)
    write_csv(args.output_dir / "run_summary.csv", run_rows)
    write_csv(args.output_dir / "run_summary_calls_nonzero.csv", run_rows_nonzero)
    write_csv(args.output_dir / "retrieval_group_metrics.csv", group_rows)
    write_csv(
        args.output_dir / "retrieval_group_metrics_calls_nonzero.csv",
        group_rows_nonzero,
    )
    write_csv(args.output_dir / "selected_case_metrics.csv", selected_case_rows)
    write_json(
        args.output_dir / "retrieval_group_metrics.json",
        {
            "warnings": warnings,
            "runs": run_rows,
            "runs_calls_nonzero": run_rows_nonzero,
            "groups": group_rows,
            "groups_calls_nonzero": group_rows_nonzero,
            "selected_cases": selected_case_rows,
        },
    )
    (args.output_dir / "retrieval_group_metrics.md").write_text(
        render_markdown(
            run_rows,
            group_rows,
            run_rows_nonzero,
            group_rows_nonzero,
            selected_case_rows,
            warnings,
        ),
        encoding="utf-8",
    )

    print(f"Wrote final-results retrieval analysis to {args.output_dir}")
    print(f"Runs={len(run_rows)} joined_rows={len(joined_rows)} warnings={len(warnings)}")


def load_retrieval(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in read_csv(path):
        row = dict(row)
        row["official_uses_same_schema"] = parse_bool(row.get("official_uses_same_schema"))
        row["default_vs_independent_same_pair"] = parse_optional_bool(
            row.get("default_vs_independent_same_pair")
        )
        for key in (
            "field_count",
            "gold_keys",
            "input_chars",
            "structural_same_schema_count",
            "same_schema_above_threshold_count",
        ):
            row[key] = parse_int(row.get(key))
        for key in (
            "same_schema_candidate_max_similarity",
            "selected_same_schema_min_similarity",
            "pair_score_gain_vs_independent",
            "field_score_sum_loss_vs_independent",
            "coverage_gain_vs_independent",
            "official_pair_score",
            "official_field_score_sum",
            "official_coverage_ratio",
            "independent_pair_score",
            "independent_field_score_sum",
            "independent_coverage_ratio",
        ):
            row[key] = parse_float(row.get(key))
        row["official_selected_case_ids_list"] = split_semicolon(
            row.get("official_selected_case_ids")
        )
        rows[str(row["task_id"])] = row

    add_bins(rows.values())
    return rows


def add_bins(rows: Iterable[dict[str, Any]]) -> None:
    row_list = list(rows)
    same_values = [
        row["selected_same_schema_min_similarity"]
        for row in row_list
        if row["selected_same_schema_min_similarity"] is not None
    ]
    pair_values = [
        row["pair_score_gain_vs_independent"]
        for row in row_list
        if row["pair_score_gain_vs_independent"] is not None
    ]
    same_thresholds = tertile_thresholds(same_values)
    pair_thresholds = tertile_thresholds(pair_values)

    for row in row_list:
        row["route_group"] = route_group(row)
        row["same_similarity_bin"] = value_tertile(
            row["selected_same_schema_min_similarity"],
            same_thresholds,
        )
        row["pair_gain_bin"] = value_tertile(
            row["pair_score_gain_vs_independent"],
            pair_thresholds,
        )
        coverage_gain = row["coverage_gain_vs_independent"]
        if coverage_gain is None:
            row["coverage_gain_group"] = ""
        elif coverage_gain > 0:
            row["coverage_gain_group"] = "coverage_gain_positive"
        else:
            row["coverage_gain_group"] = "coverage_gain_zero"


def route_group(row: Mapping[str, Any]) -> str:
    method = str(row.get("official_selection_method") or "")
    if row.get("official_uses_same_schema") is True:
        return "same_schema"
    if method == "field_embeddings_fallback":
        return "field_embeddings"
    if method == "retrieval_failed_after_error":
        return "retrieval_failed"
    return method or "unknown"


def join_run_tasks(
    run: RunInfo,
    payload: Mapping[str, Any],
    retrieval: Mapping[str, dict[str, Any]],
    *,
    drop_set: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    rows: list[dict[str, Any]] = []
    for task in payload.get("tasks") or []:
        if not isinstance(task, Mapping):
            continue
        task_id = str(task.get("task_id") or "")
        if drop_set == "official" and is_official_drop_task_id(task_id):
            continue
        r = retrieval.get(task_id)
        if r is None:
            warnings.append(f"{run.label}: missing retrieval row for {task_id}")
            continue
        tokens = task.get("tokens") if isinstance(task.get("tokens"), Mapping) else {}
        system_keys = parse_int(task.get("system_keys"))
        gold_keys = parse_int(task.get("gold_keys"))
        rows.append(
            {
                "run": run.label,
                "model": run.model,
                "pipeline": run.pipeline,
                "mode": run.mode,
                "result_file": str(run.path),
                "task_id": task_id,
                "tps": parse_float(task.get("tps")) or 0.0,
                "gold_keys": gold_keys,
                "system_keys": system_keys,
                "system_minus_gold": system_keys - gold_keys,
                "elapsed_s": parse_float(task.get("elapsed_s")),
                "tokens_input": parse_int(tokens.get("input")),
                "tokens_output": parse_int(tokens.get("output")),
                "tokens_total": parse_int(tokens.get("total")),
                "calls": parse_int(tokens.get("calls")),
                "calls_zero": parse_int(tokens.get("calls")) == 0,
                "status": str(task.get("status") or ""),
                "error": str(task.get("error") or ""),
                "domain": r["domain"],
                "schema_title": r["schema_title"],
                "field_count": r["field_count"],
                "input_chars": r["input_chars"],
                "route_group": r["route_group"],
                "official_selection_method": r["official_selection_method"],
                "official_selected_case_ids": r.get("official_selected_case_ids") or "",
                "same_similarity_bin": r["same_similarity_bin"],
                "pair_gain_bin": r["pair_gain_bin"],
                "coverage_gain_group": r["coverage_gain_group"],
                "selected_same_schema_min_similarity": r[
                    "selected_same_schema_min_similarity"
                ],
                "pair_score_gain_vs_independent": r[
                    "pair_score_gain_vs_independent"
                ],
                "coverage_gain_vs_independent": r["coverage_gain_vs_independent"],
                "field_parse_error": r.get("field_parse_error") or "",
            }
        )
    return rows, warnings


def group_metric_rows(run: RunInfo, rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    group_specs: list[tuple[str, str, list[dict[str, Any]]]] = [
        ("all", "all", list(rows)),
    ]

    for value in sorted({row["route_group"] for row in rows}):
        group_specs.append(
            ("route", value, [row for row in rows if row["route_group"] == value])
        )
    for value in ("low", "mid", "high"):
        subset = [row for row in rows if row["same_similarity_bin"] == value]
        if subset:
            group_specs.append(("same_similarity_tertile", value, subset))
    for value in ("low", "mid", "high"):
        subset = [row for row in rows if row["pair_gain_bin"] == value]
        if subset:
            group_specs.append(("pair_gain_tertile", value, subset))
    for value in ("coverage_gain_zero", "coverage_gain_positive"):
        subset = [row for row in rows if row["coverage_gain_group"] == value]
        if subset:
            group_specs.append(("coverage_gain", value, subset))
    for value in sorted({row["domain"] for row in rows}):
        subset = [row for row in rows if row["domain"] == value]
        group_specs.append(("domain", value, subset))
    for value in sorted({row["schema_title"] for row in rows}):
        subset = [row for row in rows if row["schema_title"] == value]
        group_specs.append(("schema_title", value, subset))

    return [
        {
            "run": run.label,
            "model": run.model,
            "pipeline": run.pipeline,
            "mode": run.mode,
            "group_family": family,
            "group": group,
            **metrics_for_rows(subset),
        }
        for family, group, subset in group_specs
    ]


def selected_case_metric_rows(
    run: RunInfo,
    rows: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        for case_id in split_semicolon(row.get("official_selected_case_ids")):
            by_case[case_id].append(row)
    out = []
    for case_id, subset in sorted(by_case.items(), key=lambda item: (-len(item[1]), item[0])):
        metrics = metrics_for_rows(subset)
        out.append(
            {
                "run": run.label,
                "model": run.model,
                "pipeline": run.pipeline,
                "mode": run.mode,
                "case_id": case_id,
                "selected_task_count": len(subset),
                **metrics,
            }
        )
    return out


def run_summary_row(run: RunInfo, rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    return {
        "run": run.label,
        "model": run.model,
        "pipeline": run.pipeline,
        "mode": run.mode,
        **metrics_for_rows(rows),
    }


def metrics_for_rows(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    rows = list(rows)
    tps = sum(float(row["tps"]) for row in rows)
    gold = sum(int(row["gold_keys"]) for row in rows)
    system = sum(int(row["system_keys"]) for row in rows)
    precision = tps / system if system else 0.0
    recall = tps / gold if gold else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall > 0.0
        else 0.0
    )
    calls_zero = sum(1 for row in rows if row["calls_zero"])
    statuses = Counter(str(row.get("status") or "") for row in rows)
    return {
        "task_count": len(rows),
        "tps": round(tps, 6),
        "gold_keys": gold,
        "system_keys": system,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "calls_total": sum(int(row["calls"]) for row in rows),
        "calls_zero": calls_zero,
        "calls_zero_pct": round(calls_zero / len(rows), 6) if rows else 0.0,
        "tokens_total": sum(int(row["tokens_total"]) for row in rows),
        "tokens_avg": round(mean(row["tokens_total"] for row in rows), 3),
        "elapsed_avg_s": round(mean_optional(row["elapsed_s"] for row in rows), 3),
        "elapsed_max_s": round(max_optional(row["elapsed_s"] for row in rows), 3),
        "system_minus_gold_avg": round(mean(row["system_minus_gold"] for row in rows), 3),
        "status_pass": statuses.get("PASS", 0),
        "status_fail": len(rows) - statuses.get("PASS", 0),
    }


def render_markdown(
    run_rows: Sequence[dict[str, Any]],
    group_rows: Sequence[dict[str, Any]],
    run_rows_nonzero: Sequence[dict[str, Any]],
    group_rows_nonzero: Sequence[dict[str, Any]],
    selected_case_rows: Sequence[dict[str, Any]],
    warnings: Sequence[str],
) -> str:
    lines = [
        "# Final results x retrieval",
        "",
        "Generated from `results/final_results*.json` joined with "
        "`analysis/retrieval_only/test_retrieval_by_task.csv`.",
        "",
        "## Runs",
        "",
        table(
            run_rows,
            ["run", "task_count", "precision", "recall", "f1", "tokens_avg", "calls_zero"],
        ),
        "",
        "## Runs, Calls > 0",
        "",
        table(
            run_rows_nonzero,
            ["run", "task_count", "precision", "recall", "f1", "tokens_avg", "calls_zero"],
        ),
        "",
        "## By Retrieval Route",
        "",
    ]
    route_rows = [
        row for row in group_rows if row["group_family"] == "route"
    ]
    lines.append(
        table(
            route_rows,
            [
                "run",
                "group",
                "task_count",
                "precision",
                "recall",
                "f1",
                "tokens_avg",
                "calls_zero",
            ],
        )
    )
    lines.extend(["", "## By Retrieval Route, Calls > 0", ""])
    route_rows_nonzero = [
        row for row in group_rows_nonzero if row["group_family"] == "route"
    ]
    lines.append(
        table(
            route_rows_nonzero,
            [
                "run",
                "group",
                "task_count",
                "precision",
                "recall",
                "f1",
                "tokens_avg",
                "calls_zero",
            ],
        )
    )
    lines.extend(["", "## Field Coverage Gain Groups", ""])
    coverage_rows = [
        row for row in group_rows if row["group_family"] == "coverage_gain"
    ]
    lines.append(
        table(
            coverage_rows,
            ["run", "group", "task_count", "precision", "recall", "f1", "calls_zero"],
        )
    )
    lines.extend(["", "## Same-Schema Similarity Tertiles", ""])
    same_rows = [
        row for row in group_rows if row["group_family"] == "same_similarity_tertile"
    ]
    lines.append(
        table(
            same_rows,
            ["run", "group", "task_count", "precision", "recall", "f1", "calls_zero"],
        )
    )
    lines.extend(["", "## Pair-Gain Tertiles", ""])
    pair_rows = [
        row for row in group_rows if row["group_family"] == "pair_gain_tertile"
    ]
    lines.append(
        table(
            pair_rows,
            ["run", "group", "task_count", "precision", "recall", "f1", "calls_zero"],
        )
    )
    lines.extend(["", "## Frequently Selected FSP Cases", ""])
    top_case_rows = [
        row for row in selected_case_rows
        if row["selected_task_count"] >= 10
    ][:80]
    lines.append(
        table(
            top_case_rows,
            ["run", "case_id", "selected_task_count", "precision", "recall", "f1"],
        )
    )
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings[:50])
    return "\n".join(lines) + "\n"


def run_info(path: Path, payload: Mapping[str, Any]) -> RunInfo:
    config = payload.get("config") if isinstance(payload.get("config"), Mapping) else {}
    model = str(config.get("model") or "unknown_model")
    pipeline = str(config.get("pipeline") or "unknown_pipeline")
    mode = mode_from_path(path)
    label_parts = [short_model_label(model), pipeline]
    if mode:
        label_parts.append(mode)
    return RunInfo(
        label="::".join(label_parts),
        model=model,
        pipeline=pipeline,
        mode=mode,
        path=path,
    )


def mode_from_path(path: Path) -> str:
    parts = path.stem.split("__")
    if parts and parts[-1] in {"think", "nothink"}:
        return parts[-1]
    return ""


def short_model_label(model: str) -> str:
    value = model.lower()
    if "qwen" in value:
        return "qwen3-14b"
    if "gemma" in value or "gema" in value:
        return "gemma-4-e4b-it"
    return model


def is_official_drop_task_id(task_id: str) -> bool:
    return domain_from_task_id(task_id) in {
        "medical_trials",
        "cultural_monuments",
        "stem_biology",
    }


def domain_from_task_id(task_id: str) -> str:
    value = task_id
    if value.startswith("test_"):
        value = value[len("test_") :]
    parts = value.split("_")
    if parts and parts[-1].isdigit():
        parts = parts[:-1]
    return "_".join(parts)


def tertile_thresholds(values: Sequence[float]) -> tuple[float, float] | None:
    values = sorted(float(value) for value in values if value is not None)
    if len(values) < 3:
        return None
    return quantile(values, 1 / 3), quantile(values, 2 / 3)


def value_tertile(value: float | None, thresholds: tuple[float, float] | None) -> str:
    if value is None or thresholds is None:
        return ""
    low, high = thresholds
    if value <= low:
        return "low"
    if value <= high:
        return "mid"
    return "high"


def quantile(sorted_values: Sequence[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    pos = (len(sorted_values) - 1) * q
    lower = int(math.floor(pos))
    upper = int(math.ceil(pos))
    if lower == upper:
        return sorted_values[lower]
    weight = pos - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def mean(values: Iterable[Any]) -> float:
    nums = [float(value) for value in values if value is not None]
    return statistics.fmean(nums) if nums else 0.0


def mean_optional(values: Iterable[Any]) -> float:
    return mean(values)


def max_optional(values: Iterable[Any]) -> float:
    nums = [float(value) for value in values if value is not None]
    return max(nums) if nums else 0.0


def parse_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(float(value))


def parse_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def parse_bool(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def parse_optional_bool(value: Any) -> bool | None:
    text = str(value).strip().lower()
    if text == "true":
        return True
    if text == "false":
        return False
    return None


def split_semicolon(value: Any) -> list[str]:
    if value is None:
        return []
    text = str(value).strip()
    if not text:
        return []
    return [item for item in text.split(";") if item]


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
