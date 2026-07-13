from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

BASELINES = {
    "gemma": 0.7895,
    "qwen": 0.7805,
}

DROP_DOMAINS = {
    "medical_trials",
    "cultural_monuments",
    "stem_biology",
}

PIPELINE_LABELS = {
    "enriched-schema-rag": "Schema-RAG",
    "enriched-inline-reasoning-rag": "Reasoned-RAG",
    "mixed-extractors-self-consistency-rag": "Mixed-SC",
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build DRILLER official-result tables from summary.json and reports, "
            "with the GenSIE 20-instance drop-set applied."
        )
    )
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=Path("results/DRILLER/summary.json"),
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=Path("results/DRILLER/reports"),
    )
    parser.add_argument(
        "--retrieval-csv",
        type=Path,
        default=Path("analysis/retrieval_only/test_retrieval_by_task.csv"),
    )
    parser.add_argument(
        "--schema-overlap-json",
        type=Path,
        default=Path("analysis/test_schema_subsets_official/schema_overlap.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("analysis/official_driller"),
    )
    parser.add_argument(
        "--doc",
        type=Path,
        default=Path("docs/analisis-official-results.md"),
    )
    args = parser.parse_args()

    summary = read_json(args.summary_json)
    all_cells = official_cells(summary)
    reports = load_reports(args.reports_dir)
    retrieval = load_retrieval(args.retrieval_csv)
    schema_payload = (
        read_json(args.schema_overlap_json)
        if args.schema_overlap_json.exists()
        else None
    )

    attach_reports(all_cells, reports)
    best_cells = best_cells_by_model_pipeline(all_cells)
    route_rows = route_metrics_for_cells(best_cells, reports, retrieval)
    all_route_rows = route_metrics_for_cells(all_cells, reports, retrieval)
    rag_rows = rag_vs_baseline_rows(all_cells)
    mixed_rows = mixed_vs_schema_rows(all_cells)
    retrieval_rows, retrieval_summary = retrieval_diagnostics(retrieval)
    schema_rows, schema_summary = schema_diagnostics(schema_payload)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.doc.parent.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "official_all_cells.csv", all_cells)
    write_csv(args.output_dir / "official_best_cells.csv", best_cells)
    write_csv(args.output_dir / "official_best_route_metrics.csv", route_rows)
    write_csv(args.output_dir / "official_all_route_metrics.csv", all_route_rows)
    write_csv(args.output_dir / "official_rag_vs_baseline.csv", rag_rows)
    write_csv(args.output_dir / "official_mixed_sc_vs_schema.csv", mixed_rows)
    write_csv(args.output_dir / "official_retrieval_by_domain.csv", retrieval_rows)
    write_csv(args.output_dir / "official_schema_overlap.csv", schema_rows)
    write_json(
        args.output_dir / "official_summary.json",
        {
            "summary_json": str(args.summary_json),
            "reports_dir": str(args.reports_dir),
            "retrieval_csv": str(args.retrieval_csv),
            "drop_domains": sorted(DROP_DOMAINS),
            "rank": summary.get("rank"),
            "avg_gap_closed": summary.get("avg_gap_closed"),
            "all_cells": all_cells,
            "best_cells": best_cells,
            "mixed_sc_vs_schema": mixed_rows,
            "retrieval_summary": retrieval_summary,
            "schema_summary": schema_summary,
        },
    )
    markdown = render_markdown(
        summary=summary,
        all_cells=all_cells,
        best_cells=best_cells,
        route_rows=route_rows,
        mixed_rows=mixed_rows,
        retrieval_summary=retrieval_summary,
        schema_summary=schema_summary,
    )
    (args.output_dir / "official_summary.md").write_text(markdown, encoding="utf-8")
    args.doc.write_text(markdown, encoding="utf-8")

    print(f"Wrote official DRILLER analysis to {args.output_dir}")
    print(f"Wrote note to {args.doc}")


def official_cells(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for raw in summary.get("pipelines") or []:
        model = canonical_model(str(raw["model"]))
        pipeline = str(raw["pipeline"])
        mode = str(raw["mode"])
        baseline = BASELINES[model]
        row = {
            "model": model,
            "model_label": model_label(model),
            "pipeline": pipeline,
            "pipeline_label": PIPELINE_LABELS.get(pipeline, pipeline),
            "mode": mode,
            "precision": round_float(raw["precision"], 4),
            "recall": round_float(raw["recall"], 4),
            "f1": round_float(raw["f1"], 4),
            "baseline_f1": baseline,
            "delta_f1_vs_baseline": round_float(float(raw["f1"]) - baseline, 4),
            "gap_closed": round_float(gap_closed(float(raw["f1"]), baseline), 4),
            "gap_closed_pct": round_float(100.0 * gap_closed(float(raw["f1"]), baseline), 1),
            "n_instances": int(raw["n_instances"]),
            "source_event": str(raw["source_event"]),
            "report_file": "",
        }
        key = (model, pipeline, mode)
        current = by_key.get(key)
        if current is None or (
            row["f1"],
            row["source_event"],
        ) > (
            current["f1"],
            current["source_event"],
        ):
            by_key[key] = row

    return sorted(
        by_key.values(),
        key=lambda row: (row["model"], -float(row["f1"]), row["pipeline"], row["mode"]),
    )


def load_reports(reports_dir: Path) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    out: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for path in sorted(reports_dir.glob("*.json")):
        event, pipeline, model, mode = parse_report_name(path)
        payload = read_json(path)
        keep_tasks = [
            task for task in payload.get("tasks") or []
            if not is_official_drop_task_id(str(task.get("task_id") or ""))
        ]
        metrics = metric_summary(keep_tasks)
        out[(event, pipeline, model, mode)] = {
            "path": path,
            "event": event,
            "pipeline": pipeline,
            "model": model,
            "mode": mode,
            "tasks": keep_tasks,
            "metrics": metrics,
        }
    return out


def parse_report_name(path: Path) -> tuple[str, str, str, str]:
    parts = path.stem.split("__")
    if len(parts) != 4:
        raise ValueError(f"unexpected report filename: {path.name}")
    event, pipeline, model, mode = parts
    return event, pipeline, canonical_model(model), mode


def attach_reports(
    cells: Sequence[dict[str, Any]],
    reports: Mapping[tuple[str, str, str, str], dict[str, Any]],
) -> None:
    for cell in cells:
        candidates = [
            report
            for (event, pipeline, model, mode), report in reports.items()
            if pipeline == cell["pipeline"]
            and model == cell["model"]
            and mode == cell["mode"]
        ]
        candidates.sort(
            key=lambda report: (
                abs(float(report["metrics"]["f1"]) - float(cell["f1"])),
                -float(report["metrics"]["f1"]),
                str(report["event"]),
            )
        )
        if not candidates:
            continue
        selected = candidates[0]
        if abs(float(selected["metrics"]["f1"]) - float(cell["f1"])) > 0.0001:
            continue
        cell["report_file"] = selected["path"].name


def best_cells_by_model_pipeline(cells: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str], Mapping[str, Any]] = {}
    for cell in cells:
        key = (str(cell["model"]), str(cell["pipeline"]))
        current = by_key.get(key)
        if current is None or float(cell["f1"]) > float(current["f1"]):
            by_key[key] = cell
    return [
        dict(row)
        for row in sorted(
            by_key.values(),
            key=lambda row: (str(row["model"]), str(row["pipeline"])),
        )
    ]


def route_metrics_for_cells(
    cells: Sequence[Mapping[str, Any]],
    reports: Mapping[tuple[str, str, str, str], dict[str, Any]],
    retrieval: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cell in cells:
        report_file = str(cell.get("report_file") or "")
        if not report_file:
            continue
        report = next(
            (
                value
                for value in reports.values()
                if value["path"].name == report_file
            ),
            None,
        )
        if report is None:
            continue
        by_route: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
        for task in report["tasks"]:
            task_id = str(task["task_id"])
            route = str(retrieval[task_id]["route_group"])
            by_route[route].append(task)
        for route in ("same_schema", "field_rag"):
            metrics = metric_summary(by_route.get(route, []))
            rows.append(
                {
                    "model": cell["model"],
                    "model_label": cell["model_label"],
                    "pipeline": cell["pipeline"],
                    "pipeline_label": cell["pipeline_label"],
                    "mode": cell["mode"],
                    "route": route,
                    **metrics,
                }
            )
    return rows


def rag_vs_baseline_rows(cells: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "model": cell["model"],
            "model_label": cell["model_label"],
            "pipeline": cell["pipeline"],
            "pipeline_label": cell["pipeline_label"],
            "mode": cell["mode"],
            "baseline_f1": cell["baseline_f1"],
            "system_f1": cell["f1"],
            "delta_f1": cell["delta_f1_vs_baseline"],
            "gap_closed": cell["gap_closed"],
            "gap_closed_pct": cell["gap_closed_pct"],
        }
        for cell in cells
    ]


def mixed_vs_schema_rows(cells: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for model in ("gemma", "qwen"):
        by_pipeline = {
            str(cell["pipeline"]): cell
            for cell in best_cells_by_model_pipeline(
                [cell for cell in cells if cell["model"] == model]
            )
        }
        schema = by_pipeline.get("enriched-schema-rag")
        mixed = by_pipeline.get("mixed-extractors-self-consistency-rag")
        if schema and mixed:
            rows.append(compare_cells("best_cell", model, schema, mixed))

        schema_nt = cell_by_key(cells, model, "enriched-schema-rag", "nothink")
        mixed_nt = cell_by_key(
            cells, model, "mixed-extractors-self-consistency-rag", "nothink"
        )
        if schema_nt and mixed_nt:
            rows.append(compare_cells("nothink_controlled", model, schema_nt, mixed_nt))
    return rows


def compare_cells(
    comparison_type: str,
    model: str,
    schema: Mapping[str, Any],
    mixed: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "comparison_type": comparison_type,
        "model": model,
        "model_label": model_label(model),
        "schema_mode": schema["mode"],
        "mixed_mode": mixed["mode"],
        "schema_f1": schema["f1"],
        "mixed_f1": mixed["f1"],
        "delta_mixed_minus_schema": round_float(float(mixed["f1"]) - float(schema["f1"]), 4),
        "schema_gap_closed": schema["gap_closed"],
        "mixed_gap_closed": mixed["gap_closed"],
    }


def cell_by_key(
    cells: Sequence[Mapping[str, Any]],
    model: str,
    pipeline: str,
    mode: str,
) -> Mapping[str, Any] | None:
    matches = [
        cell
        for cell in cells
        if cell["model"] == model and cell["pipeline"] == pipeline and cell["mode"] == mode
    ]
    return max(matches, key=lambda cell: float(cell["f1"])) if matches else None


def load_retrieval(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for raw in read_csv(path):
        task_id = str(raw["task_id"])
        if is_official_drop_task_id(task_id):
            continue
        uses_same = str(raw.get("official_uses_same_schema") or "").lower() == "true"
        method = str(raw.get("official_selection_method") or "")
        if uses_same:
            route = "same_schema"
        elif method == "field_embeddings_fallback":
            route = "field_rag"
        else:
            route = method or "unknown"
        row = dict(raw)
        row["route_group"] = route
        row["coverage_gain_vs_independent"] = parse_optional_float(
            row.get("coverage_gain_vs_independent")
        )
        row["pair_score_gain_vs_independent"] = parse_optional_float(
            row.get("pair_score_gain_vs_independent")
        )
        rows[task_id] = row
    return rows


def retrieval_diagnostics(
    retrieval: Mapping[str, Mapping[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for domain in sorted({str(row["domain"]) for row in retrieval.values()}):
        subset = [row for row in retrieval.values() if row["domain"] == domain]
        rows.append(
            {
                "domain": domain,
                "tasks": len(subset),
                "same_schema": sum(row["route_group"] == "same_schema" for row in subset),
                "field_rag": sum(row["route_group"] == "field_rag" for row in subset),
                "retrieval_failed": sum(
                    row["route_group"] == "retrieval_failed_after_error"
                    for row in subset
                ),
            }
        )
    field_rows = [
        row for row in retrieval.values() if row["route_group"] == "field_rag"
    ]
    same_rows = [
        row for row in retrieval.values() if row["route_group"] == "same_schema"
    ]
    coverage_values = [
        float(row["coverage_gain_vs_independent"])
        for row in field_rows
        if row["coverage_gain_vs_independent"] is not None
    ]
    pair_values = [
        float(row["pair_score_gain_vs_independent"])
        for row in field_rows
        if row["pair_score_gain_vs_independent"] is not None
    ]
    summary = {
        "task_count": len(retrieval),
        "same_schema_route_count": len(same_rows),
        "field_rag_route_count": len(field_rows),
        "retrieval_failed_count": sum(
            row["route_group"] == "retrieval_failed_after_error"
            for row in retrieval.values()
        ),
        "field_rag_pair_diagnostics_count": len(pair_values),
        "field_rag_positive_coverage_gain_count": sum(
            value > 0.0 for value in coverage_values
        ),
        "field_rag_pair_score_gain": describe(pair_values),
        "field_rag_coverage_gain": describe(coverage_values),
    }
    return rows, summary


def schema_diagnostics(
    schema_payload: Mapping[str, Any] | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not schema_payload:
        return [], {}
    rows = []
    for schema in schema_payload.get("schemas") or []:
        rows.append(
            {
                "seen_in_dev": bool(schema["seen_in_dev"]),
                "schema_title": str(schema["schema_title"]),
                "tasks": int(schema["test_task_count"]),
                "domains": ",".join(str(item) for item in schema.get("domains") or []),
            }
        )
    return rows, dict(schema_payload.get("summary") or {})


def metric_summary(tasks: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    tps = sum(float(task.get("tps") or 0.0) for task in tasks)
    gold = sum(int(task.get("gold_keys") or 0) for task in tasks)
    system = sum(int(task.get("system_keys") or 0) for task in tasks)
    precision = tps / system if system else 0.0
    recall = tps / gold if gold else 0.0
    f1 = (
        2.0 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return {
        "task_count": len(tasks),
        "precision": round_float(precision, 4),
        "recall": round_float(recall, 4),
        "f1": round_float(f1, 4),
        "tps": round_float(tps, 6),
        "gold_keys": gold,
        "system_keys": system,
    }


def render_markdown(
    *,
    summary: Mapping[str, Any],
    all_cells: Sequence[Mapping[str, Any]],
    best_cells: Sequence[Mapping[str, Any]],
    route_rows: Sequence[Mapping[str, Any]],
    mixed_rows: Sequence[Mapping[str, Any]],
    retrieval_summary: Mapping[str, Any],
    schema_summary: Mapping[str, Any],
) -> str:
    lines = [
        "# Official DRILLER results analysis",
        "",
        "Computed from `results/DRILLER/summary.json`, "
        "`results/DRILLER/reports/*.json`, and retrieval diagnostics with the "
        "official 20-instance drop-set removed.",
        "",
        f"- Rank: {summary.get('rank')}",
        f"- Avg gap closed: {float(summary.get('avg_gap_closed') or 0.0):.4f}",
        "- Official baselines: Gemma 4 E4B no-think F1=0.7895; "
        "Qwen3-14B no-think F1=0.7805.",
        "- Drop-set domains: medical_trials=8, cultural_monuments=2, "
        "stem_biology=10.",
        "",
        "## All official cells",
        "",
        table(
            all_cells,
            [
                "model_label",
                "pipeline_label",
                "mode",
                "precision",
                "recall",
                "f1",
                "gap_closed_pct",
                "source_event",
            ],
        ),
        "",
        "## Best cell by model and pipeline",
        "",
        table(
            best_cells,
            [
                "model_label",
                "pipeline_label",
                "mode",
                "precision",
                "recall",
                "f1",
                "gap_closed_pct",
            ],
        ),
        "",
        "## Best-cell route diagnostics",
        "",
        table(
            route_rows,
            [
                "model_label",
                "pipeline_label",
                "mode",
                "route",
                "task_count",
                "precision",
                "recall",
                "f1",
            ],
        ),
        "",
        "## Mixed-SC vs Schema-RAG",
        "",
        table(
            mixed_rows,
            [
                "comparison_type",
                "model_label",
                "schema_mode",
                "mixed_mode",
                "schema_f1",
                "mixed_f1",
                "delta_mixed_minus_schema",
            ],
        ),
        "",
        "## Retrieval composition",
        "",
        table(
            [retrieval_summary],
            [
                "task_count",
                "same_schema_route_count",
                "field_rag_route_count",
                "retrieval_failed_count",
                "field_rag_pair_diagnostics_count",
                "field_rag_positive_coverage_gain_count",
            ],
        ),
        "",
        "## Schema composition",
        "",
        table(
            [schema_summary],
            [
                "total_schemas",
                "seen_schemas",
                "unseen_schemas",
                "total_tasks",
                "seen_schema_tasks",
                "unseen_schema_tasks",
            ],
        ),
        "",
        "## Notes",
        "",
        "- Route diagnostics are system-only cuts; no official per-route baseline "
        "reports are present in `results/DRILLER`.",
        "- Timing is intentionally omitted because the hosted backend and model "
        "generation latency are confounded with user-code execution.",
    ]
    return "\n".join(lines) + "\n"


def gap_closed(system_f1: float, baseline_f1: float) -> float:
    if baseline_f1 >= 1.0:
        return 0.0
    return max(0.0, (system_f1 - baseline_f1) / (1.0 - baseline_f1))


def canonical_model(value: str) -> str:
    lower = value.lower()
    if "gemma" in lower or "gema" in lower:
        return "gemma"
    if "qwen" in lower:
        return "qwen"
    return lower


def model_label(value: str) -> str:
    if value == "gemma":
        return "Gemma"
    if value == "qwen":
        return "Qwen"
    return value


def is_official_drop_task_id(task_id: str) -> bool:
    return domain_from_task_id(task_id) in DROP_DOMAINS


def domain_from_task_id(task_id: str) -> str:
    value = task_id
    if value.startswith("test_"):
        value = value[len("test_") :]
    parts = value.split("_")
    if parts and parts[-1].isdigit():
        parts = parts[:-1]
    return "_".join(parts)


def describe(values: Sequence[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0}
    values = sorted(values)
    return {
        "n": len(values),
        "min": round_float(values[0], 6),
        "p25": round_float(quantile(values, 0.25), 6),
        "mean": round_float(statistics.fmean(values), 6),
        "median": round_float(statistics.median(values), 6),
        "p75": round_float(quantile(values, 0.75), 6),
        "max": round_float(values[-1], 6),
    }


def quantile(sorted_values: Sequence[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    pos = (len(sorted_values) - 1) * q
    lower = int(math.floor(pos))
    upper = int(math.ceil(pos))
    if lower == upper:
        return sorted_values[lower]
    weight = pos - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def round_float(value: Any, digits: int = 4) -> float:
    return round(float(value or 0.0), digits)


def parse_optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


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
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value) if value is not None else ""


if __name__ == "__main__":
    main()
