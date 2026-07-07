from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


UNORDERED_SCHEMA_ARRAY_KEYS = frozenset({"required", "enum", "type"})


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Report test-schema overlap with dev and per-run metrics over "
            "seen/unseen schema subsets."
        )
    )
    parser.add_argument("--dev-dir", type=Path, default=Path("data/dev"))
    parser.add_argument("--test-dir", type=Path, default=Path("data/test"))
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument(
        "--results-glob",
        default="final_results*.json",
        help="Glob used inside --results-dir.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("analysis/test_schema_subsets"),
    )
    args = parser.parse_args()

    dev_tasks = _load_tasks(args.dev_dir)
    test_tasks = _load_tasks(args.test_dir)
    result_paths = sorted(args.results_dir.glob(args.results_glob))
    if not result_paths:
        raise SystemExit(f"no result files matched {args.results_dir / args.results_glob}")

    dev_fingerprints = {task["fingerprint"] for task in dev_tasks}
    test_by_id = {task["id"]: task for task in test_tasks}
    test_aliases = _build_task_aliases(test_tasks)

    schema_rows = _schema_overlap_rows(test_tasks, dev_fingerprints)
    overlap_summary = _overlap_summary(schema_rows)

    result_payloads = [_read_json(path) for path in result_paths]
    common_zero_call_ids = _common_zero_call_task_ids(result_payloads, test_aliases)
    metrics_rows = _metrics_rows(
        result_paths=result_paths,
        result_payloads=result_payloads,
        test_by_id=test_by_id,
        test_aliases=test_aliases,
        common_zero_call_ids=common_zero_call_ids,
        dev_fingerprints=dev_fingerprints,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        args.output_dir / "schema_overlap.json",
        {
            "dev_dir": str(args.dev_dir),
            "test_dir": str(args.test_dir),
            "fingerprint_method": _fingerprint_method_description(),
            "summary": overlap_summary,
            "schemas": schema_rows,
        },
    )
    _write_json(
        args.output_dir / "subset_metrics.json",
        {
            "results_dir": str(args.results_dir),
            "results_glob": args.results_glob,
            "common_zero_call_task_count": len(common_zero_call_ids),
            "common_zero_call_task_ids": sorted(common_zero_call_ids),
            "subsets": _subset_descriptions(),
            "runs": metrics_rows,
        },
    )
    _write_schema_overlap_markdown(
        args.output_dir / "schema_overlap.md",
        overlap_summary,
        schema_rows,
    )
    _write_metrics_csv(args.output_dir / "subset_metrics.csv", metrics_rows)
    _write_metrics_markdown(args.output_dir / "subset_metrics.md", metrics_rows)

    print(_render_console_summary(overlap_summary, common_zero_call_ids, args.output_dir))


def _load_tasks(directory: Path) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        payload = _read_json(path)
        schema = payload["target_schema"]
        metadata = payload.get("metadata") or {}
        task_id = str(payload.get("id") or path.stem)
        tasks.append(
            {
                "id": task_id,
                "path": str(path),
                "schema_title": str(schema.get("title") or "Unknown"),
                "domain": str(metadata.get("domain") or "unknown"),
                "subdomain": str(metadata.get("subdomain") or "unknown"),
                "fingerprint": normalized_schema_fingerprint(schema),
            }
        )
    if not tasks:
        raise ValueError(f"no JSON tasks found in {directory}")
    return tasks


def normalized_schema_fingerprint(schema: Any) -> str:
    """Match DRILLER's structural schema fingerprint used for same-schema RAG."""
    return _canonical_json(_normalize_schema_for_fingerprint(schema))


def _normalize_schema_for_fingerprint(value: Any, parent_key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {
            key: (
                ""
                if key == "description"
                else _normalize_schema_for_fingerprint(item, key)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        normalized = [
            _normalize_schema_for_fingerprint(item, parent_key) for item in value
        ]
        if parent_key in UNORDERED_SCHEMA_ARRAY_KEYS:
            return sorted(normalized, key=_canonical_json)
        return normalized
    return value


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _schema_overlap_rows(
    test_tasks: list[dict[str, Any]], dev_fingerprints: set[str]
) -> list[dict[str, Any]]:
    by_schema: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task in test_tasks:
        by_schema[task["fingerprint"]].append(task)

    rows: list[dict[str, Any]] = []
    for fingerprint, tasks in by_schema.items():
        titles = sorted({task["schema_title"] for task in tasks})
        domains = sorted({task["domain"] for task in tasks})
        seen = fingerprint in dev_fingerprints
        rows.append(
            {
                "schema_title": " / ".join(titles),
                "schema_hash": _short_hash(fingerprint),
                "seen_in_dev": seen,
                "test_task_count": len(tasks),
                "domains": domains,
                "task_ids": sorted(task["id"] for task in tasks),
                "fingerprint": fingerprint,
            }
        )

    return sorted(
        rows,
        key=lambda row: (
            not bool(row["seen_in_dev"]),
            str(row["schema_title"]),
            str(row["schema_hash"]),
        ),
    )


def _overlap_summary(schema_rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_schemas = len(schema_rows)
    total_tasks = sum(int(row["test_task_count"]) for row in schema_rows)
    seen_schemas = sum(1 for row in schema_rows if row["seen_in_dev"])
    seen_tasks = sum(
        int(row["test_task_count"]) for row in schema_rows if row["seen_in_dev"]
    )
    unseen_schemas = total_schemas - seen_schemas
    unseen_tasks = total_tasks - seen_tasks
    return {
        "total_schemas": total_schemas,
        "seen_schemas": seen_schemas,
        "seen_schemas_pct": _pct(seen_schemas, total_schemas),
        "unseen_schemas": unseen_schemas,
        "unseen_schemas_pct": _pct(unseen_schemas, total_schemas),
        "total_tasks": total_tasks,
        "seen_schema_tasks": seen_tasks,
        "seen_schema_tasks_pct": _pct(seen_tasks, total_tasks),
        "unseen_schema_tasks": unseen_tasks,
        "unseen_schema_tasks_pct": _pct(unseen_tasks, total_tasks),
    }


def _build_task_aliases(tasks: list[dict[str, Any]]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for task in tasks:
        task_id = task["id"]
        candidates = {task_id}
        if task_id.startswith("test_"):
            candidates.add(task_id.removeprefix("test_"))
        else:
            candidates.add(f"test_{task_id}")
        for candidate in candidates:
            existing = aliases.get(candidate)
            if existing is not None and existing != task_id:
                raise ValueError(f"ambiguous task alias {candidate!r}: {existing}, {task_id}")
            aliases[candidate] = task_id
    return aliases


def _common_zero_call_task_ids(
    result_payloads: list[dict[str, Any]], test_aliases: dict[str, str]
) -> set[str]:
    zero_sets: list[set[str]] = []
    for payload in result_payloads:
        zero_ids = set()
        for task in payload.get("tasks", []):
            canonical_id = _canonical_task_id(str(task["task_id"]), test_aliases)
            if int((task.get("tokens") or {}).get("calls") or 0) == 0:
                zero_ids.add(canonical_id)
        zero_sets.append(zero_ids)
    if not zero_sets:
        return set()
    common = set(zero_sets[0])
    for zero_ids in zero_sets[1:]:
        common &= zero_ids
    return common


def _metrics_rows(
    *,
    result_paths: list[Path],
    result_payloads: list[dict[str, Any]],
    test_by_id: dict[str, dict[str, Any]],
    test_aliases: dict[str, str],
    common_zero_call_ids: set[str],
    dev_fingerprints: set[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path, payload in zip(result_paths, result_payloads):
        config = payload.get("config") or {}
        model = str(config.get("model") or "")
        pipeline = str(config.get("pipeline") or "")
        tasks = []
        for task in payload.get("tasks", []):
            canonical_id = _canonical_task_id(str(task["task_id"]), test_aliases)
            test_task = test_by_id[canonical_id]
            tasks.append(
                {
                    "result": task,
                    "canonical_id": canonical_id,
                    "seen_in_dev": test_task["fingerprint"] in dev_fingerprints,
                    "common_zero_call": canonical_id in common_zero_call_ids,
                }
            )

        subsets = {
            "all": tasks,
            "seen_schema": [task for task in tasks if task["seen_in_dev"]],
            "unseen_schema": [task for task in tasks if not task["seen_in_dev"]],
            "without_common_zero_call": [
                task for task in tasks if not task["common_zero_call"]
            ],
        }
        subsets["without_common_zero_call_seen_schema"] = [
            task for task in subsets["without_common_zero_call"] if task["seen_in_dev"]
        ]
        subsets["without_common_zero_call_unseen_schema"] = [
            task
            for task in subsets["without_common_zero_call"]
            if not task["seen_in_dev"]
        ]

        per_run_zero_call = sum(
            1
            for task in tasks
            if int((task["result"].get("tokens") or {}).get("calls") or 0) == 0
        )
        for subset_name, subset_tasks in subsets.items():
            summary = _metric_summary([task["result"] for task in subset_tasks])
            rows.append(
                {
                    "file": path.name,
                    "model": model,
                    "pipeline": pipeline,
                    "subset": subset_name,
                    "n_tasks": summary["n_tasks"],
                    "precision": summary["precision"],
                    "recall": summary["recall"],
                    "f1": summary["f1"],
                    "tps": summary["tps"],
                    "gold_keys": summary["gold_keys"],
                    "system_keys": summary["system_keys"],
                    "total_input_tokens": summary["total_input_tokens"],
                    "total_output_tokens": summary["total_output_tokens"],
                    "total_tokens": summary["total_tokens"],
                    "avg_tokens_per_task": summary["avg_tokens_per_task"],
                    "total_calls": summary["total_calls"],
                    "zero_call_tasks_in_subset": summary["zero_call_tasks"],
                    "avg_elapsed_s": summary["avg_elapsed_s"],
                    "max_elapsed_s": summary["max_elapsed_s"],
                    "run_zero_call_tasks": per_run_zero_call,
                    "common_zero_call_tasks": len(common_zero_call_ids),
                }
            )
    return rows


def _metric_summary(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    tps = sum(float(task.get("tps") or 0.0) for task in tasks)
    gold_keys = sum(int(task.get("gold_keys") or 0) for task in tasks)
    system_keys = sum(int(task.get("system_keys") or 0) for task in tasks)
    precision = tps / system_keys if system_keys else 0.0
    recall = tps / gold_keys if gold_keys else 0.0
    f1 = (
        2.0 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    total_input = 0
    total_output = 0
    total_tokens = 0
    total_calls = 0
    zero_call_tasks = 0
    elapsed_values: list[float] = []
    for task in tasks:
        tokens = task.get("tokens") or {}
        calls = int(tokens.get("calls") or 0)
        total_input += int(tokens.get("input") or 0)
        total_output += int(tokens.get("output") or 0)
        total_tokens += int(tokens.get("total") or 0)
        total_calls += calls
        zero_call_tasks += int(calls == 0)
        if task.get("elapsed_s") is not None:
            elapsed_values.append(float(task["elapsed_s"]))

    n_tasks = len(tasks)
    return {
        "n_tasks": n_tasks,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tps": tps,
        "gold_keys": gold_keys,
        "system_keys": system_keys,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_tokens": total_tokens,
        "avg_tokens_per_task": total_tokens / n_tasks if n_tasks else 0.0,
        "total_calls": total_calls,
        "zero_call_tasks": zero_call_tasks,
        "avg_elapsed_s": (
            sum(elapsed_values) / len(elapsed_values) if elapsed_values else 0.0
        ),
        "max_elapsed_s": max(elapsed_values) if elapsed_values else 0.0,
    }


def _canonical_task_id(raw_id: str, aliases: dict[str, str]) -> str:
    canonical_id = aliases.get(raw_id)
    if canonical_id is None:
        raise KeyError(f"result task_id {raw_id!r} was not found in test set")
    return canonical_id


def _write_schema_overlap_markdown(
    path: Path, summary: dict[str, Any], schema_rows: list[dict[str, Any]]
) -> None:
    lines = [
        "# Test schema overlap with dev",
        "",
        "Fingerprint method: neutralize `description`, sort unordered schema arrays "
        "(`required`, `enum`, `type`), and canonicalize JSON with sorted keys.",
        "",
        "## Summary",
        "",
        "| Quantity | Count | Percent |",
        "|---|---:|---:|",
        (
            f"| Seen schemas / total schemas | {summary['seen_schemas']} / "
            f"{summary['total_schemas']} | {_fmt_pct(summary['seen_schemas_pct'])} |"
        ),
        (
            f"| Unseen schemas / total schemas | {summary['unseen_schemas']} / "
            f"{summary['total_schemas']} | {_fmt_pct(summary['unseen_schemas_pct'])} |"
        ),
        (
            f"| Tasks with seen schemas / total tasks | "
            f"{summary['seen_schema_tasks']} / {summary['total_tasks']} | "
            f"{_fmt_pct(summary['seen_schema_tasks_pct'])} |"
        ),
        (
            f"| Tasks with unseen schemas / total tasks | "
            f"{summary['unseen_schema_tasks']} / {summary['total_tasks']} | "
            f"{_fmt_pct(summary['unseen_schema_tasks_pct'])} |"
        ),
        "",
        "## Schemas",
        "",
        "| Seen in dev | Schema title | Schema hash | Test tasks | Domains |",
        "|---|---|---|---:|---|",
    ]
    for row in schema_rows:
        lines.append(
            "| "
            f"{'yes' if row['seen_in_dev'] else 'no'} | "
            f"{_escape_pipe(str(row['schema_title']))} | "
            f"`{row['schema_hash']}` | "
            f"{row['test_task_count']} | "
            f"{_escape_pipe(', '.join(row['domains']))} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_metrics_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "file",
        "model",
        "pipeline",
        "subset",
        "n_tasks",
        "precision",
        "recall",
        "f1",
        "tps",
        "gold_keys",
        "system_keys",
        "total_input_tokens",
        "total_output_tokens",
        "total_tokens",
        "avg_tokens_per_task",
        "total_calls",
        "zero_call_tasks_in_subset",
        "avg_elapsed_s",
        "max_elapsed_s",
        "run_zero_call_tasks",
        "common_zero_call_tasks",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_metrics_markdown(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Metrics by schema-overlap subset",
        "",
        "Subsets:",
        "",
    ]
    for name, description in _subset_descriptions().items():
        lines.append(f"- `{name}`: {description}")
    lines.extend(
        [
            "",
            "| Model | Pipeline | Subset | n | P | R | F1 | Avg tokens | Calls | Zero-call n | Avg s |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in rows:
        lines.append(
            "| "
            f"{_escape_pipe(str(row['model']))} | "
            f"{_escape_pipe(str(row['pipeline']))} | "
            f"`{row['subset']}` | "
            f"{row['n_tasks']} | "
            f"{float(row['precision']):.4f} | "
            f"{float(row['recall']):.4f} | "
            f"{float(row['f1']):.4f} | "
            f"{float(row['avg_tokens_per_task']):.0f} | "
            f"{row['total_calls']} | "
            f"{row['zero_call_tasks_in_subset']} | "
            f"{float(row['avg_elapsed_s']):.2f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _render_console_summary(
    summary: dict[str, Any], common_zero_call_ids: set[str], output_dir: Path
) -> str:
    return "\n".join(
        [
            "Schema overlap:",
            (
                f"  seen schemas: {summary['seen_schemas']}/"
                f"{summary['total_schemas']} ({_fmt_pct(summary['seen_schemas_pct'])})"
            ),
            (
                f"  unseen schemas: {summary['unseen_schemas']}/"
                f"{summary['total_schemas']} ({_fmt_pct(summary['unseen_schemas_pct'])})"
            ),
            (
                f"  tasks with seen schemas: {summary['seen_schema_tasks']}/"
                f"{summary['total_tasks']} "
                f"({_fmt_pct(summary['seen_schema_tasks_pct'])})"
            ),
            (
                f"  tasks with unseen schemas: {summary['unseen_schema_tasks']}/"
                f"{summary['total_tasks']} "
                f"({_fmt_pct(summary['unseen_schema_tasks_pct'])})"
            ),
            f"Common zero-call tasks excluded by subset: {len(common_zero_call_ids)}",
            f"Wrote reports under {output_dir}",
        ]
    )


def _subset_descriptions() -> dict[str, str]:
    return {
        "all": "all result tasks",
        "seen_schema": "tasks whose structural schema fingerprint appears in dev",
        "unseen_schema": "tasks whose structural schema fingerprint does not appear in dev",
        "without_common_zero_call": (
            "all tasks except the common zero-call task ids shared by every result run"
        ),
        "without_common_zero_call_seen_schema": (
            "without_common_zero_call restricted to seen schemas"
        ),
        "without_common_zero_call_unseen_schema": (
            "without_common_zero_call restricted to unseen schemas"
        ),
    }


def _fingerprint_method_description() -> str:
    return (
        "description fields are replaced with empty strings; arrays under required, "
        "enum, and type are sorted; JSON is serialized with sorted object keys."
    )


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _short_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]


def _pct(part: int | float, total: int | float) -> float:
    return float(part) / float(total) if total else 0.0


def _fmt_pct(value: float) -> str:
    return f"{100.0 * value:.1f}%"


def _escape_pipe(value: str) -> str:
    return value.replace("|", "\\|")


if __name__ == "__main__":
    main()
