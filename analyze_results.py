from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any


LEVEL_RE = re.compile(r"Complexity:\s*(L\d+)", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Enrich and analyze a GenSIE evaluation run. Supports plain results/*.json "
            "files and local runs with run-details artifacts."
        )
    )
    parser.add_argument(
        "--results-path",
        default="local-results/run-summary.json",
        help="Path to the evaluation summary JSON file.",
    )
    parser.add_argument(
        "--data-path",
        default="data/dev",
        help="Optional fallback dataset directory if no run-details artifacts exist.",
    )
    parser.add_argument(
        "--details-dir",
        default="local-results/run-details",
        help="Directory containing per-task artifacts such as task.json, gold.json and prediction.json.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="How many best/worst tasks to print.",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=4,
        help="How many task IDs to show as examples for grouped summaries.",
    )
    parser.add_argument(
        "--csv-out",
        default="local-results/enriched_run_analysis.csv",
        help="Optional path to export an enriched per-task CSV.",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def extract_level(schema_description: str | None) -> str:
    if not schema_description:
        return "UNKNOWN"
    match = LEVEL_RE.search(schema_description)
    return match.group(1).upper() if match else "UNKNOWN"


def safe_mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def safe_median(values: list[float]) -> float:
    return median(values) if values else 0.0


def per_task_f1(tps: float, gold_keys: int, system_keys: int) -> float:
    precision = tps / system_keys if system_keys else 0.0
    recall = tps / gold_keys if gold_keys else 0.0
    return (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )


def classify_outcome(status: str, tps: float, gold_keys: int, system_keys: int) -> str:
    if status != "PASS":
        if system_keys == 0:
            return "hard_fail_no_output"
        return "hard_fail_partial_output"
    if system_keys == 0:
        return "pass_but_empty"
    if tps == 0:
        return "valid_but_zero_score"
    if gold_keys == system_keys:
        return "same_key_count_partial_match"
    if system_keys < gold_keys:
        return "underfilled_output"
    return "overfilled_output"


def flatten_json(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, dict):
        items: dict[str, Any] = {}
        for key, subvalue in value.items():
            next_prefix = f"{prefix}.{key}" if prefix else key
            items.update(flatten_json(subvalue, next_prefix))
        return items
    if isinstance(value, list):
        items: dict[str, Any] = {}
        for index, subvalue in enumerate(value):
            next_prefix = f"{prefix}[{index}]"
            items.update(flatten_json(subvalue, next_prefix))
        if not value:
            items[prefix] = []
        return items
    return {prefix: value}


def count_nulls(value: Any) -> int:
    if value is None:
        return 1
    if isinstance(value, dict):
        return sum(count_nulls(item) for item in value.values())
    if isinstance(value, list):
        return sum(count_nulls(item) for item in value)
    return 0


def summarize_json_shape(value: Any) -> tuple[int, int, int]:
    flat = flatten_json(value)
    leaf_count = len(flat)
    null_count = sum(1 for item in flat.values() if item is None)
    list_leaf_count = sum(1 for item in flat.values() if isinstance(item, list))
    return leaf_count, null_count, list_leaf_count


def build_dataset_index(data_path: Path) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    if not data_path.exists():
        return index
    for json_path in sorted(data_path.rglob("*.json")):
        payload = load_json(json_path)
        task_id = payload.get("id") or json_path.stem
        metadata = payload.get("metadata", {})
        schema = payload.get("target_schema", {}) or {}
        description = schema.get("description", "")
        index[task_id] = {
            "task_path": json_path.as_posix(),
            "instruction": payload.get("instruction", ""),
            "instruction_len": len(payload.get("instruction", "")),
            "input_text_len": len(payload.get("input_text", "")),
            "domain": metadata.get("domain", "UNKNOWN"),
            "subdomain": metadata.get("subdomain", "UNKNOWN"),
            "source": metadata.get("source", ""),
            "schema_title": schema.get("title", ""),
            "description": description.strip(),
            "complexity_level": extract_level(description),
            "prefix": task_id.rsplit("_", 1)[0] if "_" in task_id else task_id,
            "schema_property_count": len((schema.get("properties") or {}).keys()),
        }
    return index


def load_task_artifacts(task_id: str, details_dir: Path) -> dict[str, Any]:
    task_dir = details_dir / task_id
    if not task_dir.exists():
        return {}

    task_payload = load_json(task_dir / "task.json") if (task_dir / "task.json").exists() else {}
    gold_payload = load_json(task_dir / "gold.json") if (task_dir / "gold.json").exists() else None
    prediction_payload = (
        load_json(task_dir / "prediction.json")
        if (task_dir / "prediction.json").exists()
        else None
    )
    summary_payload = (
        load_json(task_dir / "summary.json") if (task_dir / "summary.json").exists() else {}
    )
    step_summary = (
        load_json(task_dir / "steps/01-extract/summary.json")
        if (task_dir / "steps/01-extract/summary.json").exists()
        else {}
    )
    error_text = (
        (task_dir / "error.txt").read_text(encoding="utf-8").strip()
        if (task_dir / "error.txt").exists()
        else ""
    )

    metadata = task_payload.get("metadata", {})
    schema = task_payload.get("target_schema", {}) or {}
    description = schema.get("description", "")
    gold_leaf_count, gold_null_count, _ = summarize_json_shape(gold_payload) if gold_payload is not None else (0, 0, 0)
    pred_leaf_count, pred_null_count, _ = summarize_json_shape(prediction_payload) if prediction_payload is not None else (0, 0, 0)

    return {
        "task_path": (task_dir / "task.json").as_posix(),
        "task_dir": task_dir.as_posix(),
        "gold_path": (task_dir / "gold.json").as_posix() if gold_payload is not None else "",
        "prediction_path": (task_dir / "prediction.json").as_posix() if prediction_payload is not None else "",
        "prompt_path": (task_dir / "prompt.txt").as_posix() if (task_dir / "prompt.txt").exists() else "",
        "instruction": task_payload.get("instruction", ""),
        "instruction_len": len(task_payload.get("instruction", "")),
        "input_text_len": len(task_payload.get("input_text", "")),
        "domain": metadata.get("domain", "UNKNOWN"),
        "subdomain": metadata.get("subdomain", "UNKNOWN"),
        "source": metadata.get("source", ""),
        "schema_title": schema.get("title", ""),
        "description": description.strip(),
        "complexity_level": extract_level(description),
        "prefix": task_id.rsplit("_", 1)[0] if "_" in task_id else task_id,
        "schema_property_count": len((schema.get("properties") or {}).keys()),
        "gold_top_level_keys_count": len(gold_payload.keys()) if isinstance(gold_payload, dict) else 0,
        "prediction_top_level_keys_count": len(prediction_payload.keys()) if isinstance(prediction_payload, dict) else 0,
        "gold_leaf_count": gold_leaf_count,
        "prediction_leaf_count": pred_leaf_count,
        "gold_null_count": gold_null_count,
        "prediction_null_count": pred_null_count,
        "artifact_error_text": error_text,
        "artifact_error_present": bool(error_text),
        "request_count": ((summary_payload.get("trace_metrics") or {}).get("request_count")) or 0,
        "failed_request_count": ((summary_payload.get("trace_metrics") or {}).get("failed_request_count")) or 0,
        "prompt_tokens": ((((summary_payload.get("trace_metrics") or {}).get("tokens") or {}).get("prompt_tokens")) or 0),
        "completion_tokens": ((((summary_payload.get("trace_metrics") or {}).get("tokens") or {}).get("completion_tokens")) or 0),
        "total_tokens": ((((summary_payload.get("trace_metrics") or {}).get("tokens") or {}).get("total_tokens")) or 0),
        "duration_ms": ((((summary_payload.get("trace_metrics") or {}).get("timings") or {}).get("total_duration_ms")) or 0.0),
        "step_error": step_summary.get("error"),
    }


def enrich_tasks(
    results_tasks: list[dict[str, Any]],
    dataset_index: dict[str, dict[str, Any]],
    details_dir: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task in results_tasks:
        task_id = task["task_id"]
        artifact_meta = load_task_artifacts(task_id, details_dir)
        meta = artifact_meta or dataset_index.get(task_id, {})
        tps = float(task.get("tps", 0.0))
        gold_keys = int(task.get("gold_keys", 0))
        system_keys = int(task.get("system_keys", 0))
        precision = tps / system_keys if system_keys else 0.0
        recall = tps / gold_keys if gold_keys else 0.0
        instance_f1 = per_task_f1(tps, gold_keys, system_keys)
        row = {
            "task_id": task_id,
            "status": task.get("status", "UNKNOWN"),
            "error": task.get("error"),
            "tps": tps,
            "gold_keys": gold_keys,
            "system_keys": system_keys,
            "precision": precision,
            "recall": recall,
            "instance_f1": instance_f1,
            "key_balance": system_keys - gold_keys,
            "coverage_ratio": (system_keys / gold_keys) if gold_keys else 0.0,
            "outcome_type": classify_outcome(
                task.get("status", "UNKNOWN"),
                tps,
                gold_keys,
                system_keys,
            ),
            **meta,
        }
        rows.append(row)
    return rows


def print_global_summary(results: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    print("=== RUN SUMMARY ===")
    print(f"model: {results.get('config', {}).get('model', 'UNKNOWN')}")
    print(f"pipeline: {results.get('config', {}).get('pipeline', 'UNKNOWN')}")
    print(f"data_source: {results.get('config', {}).get('data_source', 'UNKNOWN')}")
    print(f"tasks: {len(rows)}")
    print(f"micro_precision: {results.get('metrics', {}).get('precision', 0.0):.6f}")
    print(f"micro_recall:    {results.get('metrics', {}).get('recall', 0.0):.6f}")
    print(f"micro_f1:        {results.get('metrics', {}).get('f1', 0.0):.6f}")
    print(f"status_counts:   {dict(Counter(row['status'] for row in rows))}")
    print(f"outcome_counts:  {dict(Counter(row['outcome_type'] for row in rows))}")
    print(f"avg_instance_f1: {safe_mean([row['instance_f1'] for row in rows]):.6f}")
    print(f"median_instance_f1: {safe_median([row['instance_f1'] for row in rows]):.6f}")
    print(f"avg_total_tokens: {safe_mean([float(row.get('total_tokens', 0)) for row in rows]):.2f}")
    print(f"avg_duration_ms: {safe_mean([float(row.get('duration_ms', 0.0)) for row in rows]):.2f}")
    print()


def print_top_bottom(rows: list[dict[str, Any]], top_k: int) -> None:
    print("=== BEST TASKS BY INSTANCE F1 ===")
    for row in sorted(rows, key=lambda item: item["instance_f1"], reverse=True)[:top_k]:
        print(
            f"{row['instance_f1']:.4f}  {row['task_id']}  "
            f"{row['domain']}/{row['subdomain']}  {row['complexity_level']}  "
            f"tokens={row.get('total_tokens', 0)}  duration_ms={row.get('duration_ms', 0):.1f}"
        )
    print()

    print("=== WORST TASKS BY INSTANCE F1 ===")
    for row in sorted(rows, key=lambda item: (item["instance_f1"], item["task_id"]))[:top_k]:
        print(
            f"{row['instance_f1']:.4f}  {row['task_id']}  "
            f"{row['domain']}/{row['subdomain']}  {row['complexity_level']}  "
            f"tokens={row.get('total_tokens', 0)}  duration_ms={row.get('duration_ms', 0):.1f}"
        )
    print()


def group_rows(rows: list[dict[str, Any]], key: str) -> list[tuple[str, list[dict[str, Any]]]]:
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key, "UNKNOWN"))].append(row)
    return sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))


def bucketize_length(value: int, cuts: list[int]) -> str:
    previous = 0
    for cut in cuts:
        if value <= cut:
            return f"{previous + 1}-{cut}"
        previous = cut
    return f"{cuts[-1] + 1}+"


def print_group_summary(rows: list[dict[str, Any]], key: str, max_samples: int) -> None:
    print(f"=== BY {key.upper()} ===")
    for group_name, group_rows_list in group_rows(rows, key):
        sample_ids = ", ".join(row["task_id"] for row in group_rows_list[:max_samples])
        print(
            f"{group_name}: count={len(group_rows_list)} "
            f"avg_f1={safe_mean([row['instance_f1'] for row in group_rows_list]):.4f} "
            f"avg_tps={safe_mean([row['tps'] for row in group_rows_list]):.4f} "
            f"avg_tokens={safe_mean([float(row.get('total_tokens', 0)) for row in group_rows_list]):.1f} "
            f"avg_ms={safe_mean([float(row.get('duration_ms', 0.0)) for row in group_rows_list]):.1f}"
        )
        print(f"  samples: {sample_ids}")
    print()


def print_length_summary(rows: list[dict[str, Any]], field: str, cuts: list[int], max_samples: int) -> None:
    print(f"=== BY {field.upper()} BUCKET ===")
    buckets: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        bucket = bucketize_length(int(row.get(field, 0)), cuts)
        buckets[bucket].append(row)
    for bucket, bucket_rows in sorted(
        buckets.items(),
        key=lambda item: (int(item[0].split("-")[0].rstrip("+")), item[0]),
    ):
        sample_ids = ", ".join(row["task_id"] for row in bucket_rows[:max_samples])
        print(
            f"{bucket}: count={len(bucket_rows)} "
            f"avg_f1={safe_mean([row['instance_f1'] for row in bucket_rows]):.4f} "
            f"avg_tps={safe_mean([row['tps'] for row in bucket_rows]):.4f} "
            f"avg_tokens={safe_mean([float(row.get('total_tokens', 0)) for row in bucket_rows]):.1f}"
        )
        print(f"  samples: {sample_ids}")
    print()


def print_token_and_latency_outliers(rows: list[dict[str, Any]], top_k: int) -> None:
    print("=== HIGHEST TOKEN TASKS ===")
    for row in sorted(rows, key=lambda item: float(item.get("total_tokens", 0)), reverse=True)[:top_k]:
        print(
            f"{int(row.get('total_tokens', 0)):4d}  {row['task_id']}  "
            f"{row['instance_f1']:.4f}  {row['domain']}/{row['subdomain']}"
        )
    print()

    print("=== SLOWEST TASKS ===")
    for row in sorted(rows, key=lambda item: float(item.get("duration_ms", 0.0)), reverse=True)[:top_k]:
        print(
            f"{float(row.get('duration_ms', 0.0)):.1f} ms  {row['task_id']}  "
            f"{row['instance_f1']:.4f}  {row['domain']}/{row['subdomain']}"
        )
    print()


def print_artifact_health(rows: list[dict[str, Any]]) -> None:
    print("=== ARTIFACT HEALTH ===")
    print(f"tasks_with_artifact_error_text: {sum(1 for row in rows if row.get('artifact_error_present'))}")
    print(f"tasks_with_failed_requests: {sum(1 for row in rows if int(row.get('failed_request_count', 0)) > 0)}")
    print(f"tasks_with_zero_completion_tokens: {sum(1 for row in rows if int(row.get('completion_tokens', 0)) == 0)}")
    print()


def write_csv(rows: list[dict[str, Any]], csv_out: Path) -> None:
    fieldnames = [
        "task_id",
        "status",
        "error",
        "outcome_type",
        "domain",
        "subdomain",
        "prefix",
        "complexity_level",
        "schema_title",
        "description",
        "instruction",
        "task_path",
        "task_dir",
        "gold_path",
        "prediction_path",
        "prompt_path",
        "source",
        "input_text_len",
        "instruction_len",
        "schema_property_count",
        "gold_top_level_keys_count",
        "prediction_top_level_keys_count",
        "gold_leaf_count",
        "prediction_leaf_count",
        "gold_null_count",
        "prediction_null_count",
        "tps",
        "gold_keys",
        "system_keys",
        "precision",
        "recall",
        "instance_f1",
        "key_balance",
        "coverage_ratio",
        "request_count",
        "failed_request_count",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "duration_ms",
        "artifact_error_present",
        "artifact_error_text",
        "step_error",
    ]
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    with csv_out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def main() -> None:
    args = parse_args()
    results_path = Path(args.results_path)
    data_path = Path(args.data_path)
    details_dir = Path(args.details_dir)

    results = load_json(results_path)
    dataset_index = build_dataset_index(data_path)
    rows = enrich_tasks(results["tasks"], dataset_index, details_dir)

    print_global_summary(results, rows)
    print_top_bottom(rows, args.top_k)
    print_group_summary(rows, "complexity_level", args.max_samples)
    print_group_summary(rows, "domain", args.max_samples)
    print_group_summary(rows, "subdomain", args.max_samples)
    print_group_summary(rows, "prefix", args.max_samples)
    print_group_summary(rows, "description", args.max_samples)
    print_length_summary(rows, "input_text_len", [300, 600, 900, 1300, 1800, 2600, 3600], args.max_samples)
    print_length_summary(rows, "instruction_len", [40, 70, 100, 130, 170], args.max_samples)
    print_token_and_latency_outliers(rows, args.top_k)
    print_artifact_health(rows)

    if args.csv_out:
        write_csv(rows, Path(args.csv_out))
        print(f"Wrote CSV to {args.csv_out}")


if __name__ == "__main__":
    main()
