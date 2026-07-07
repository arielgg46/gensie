from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gensie.eval import Evaluator, flatten_json
from gensie.schemas.inspect import (
    JsonDict,
    deref,
    schema_type,
    unwrap_nullable_anyof,
)
from gensie.task import Task


@dataclass
class TypeBucket:
    tps: float = 0.0
    gold_count: int = 0
    system_count: int = 0
    tasks_with_gold: set[str] | None = None
    tasks_with_system: set[str] | None = None

    def __post_init__(self) -> None:
        if self.tasks_with_gold is None:
            self.tasks_with_gold = set()
        if self.tasks_with_system is None:
            self.tasks_with_system = set()

    def metrics(self) -> dict[str, Any]:
        precision = self.tps / self.system_count if self.system_count else 0.0
        recall = self.tps / self.gold_count if self.gold_count else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall > 0.0
            else 0.0
        )
        return {
            "tps": self.tps,
            "gold_count": self.gold_count,
            "system_count": self.system_count,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tasks_with_gold": len(self.tasks_with_gold or ()),
            "tasks_with_system": len(self.tasks_with_system or ()),
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compute micro precision/recall/F1 by coarse schema type from "
            "GenSIE details directories."
        )
    )
    parser.add_argument(
        "--run",
        action="append",
        default=[],
        metavar="LABEL=DETAILS_DIR",
        help=(
            "Details directory for one run. Repeat for multiple pipelines/models, "
            "for example --run schema=local-results/enriched-schema-rag/..."
        ),
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        help="Optional CSV output path.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Optional JSON output path.",
    )
    parser.add_argument(
        "--model-name",
        default="BAAI/bge-small-en-v1.5",
        help="Embedding model used by the official text scorer.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Do not print the Markdown table to stdout.",
    )
    parser.add_argument(
        "--lexical-only",
        action="store_true",
        help="Use lexical string similarity instead of loading fastembed.",
    )
    args = parser.parse_args()

    if not args.run:
        parser.error("Provide at least one --run LABEL=DETAILS_DIR.")

    runs = [_parse_run_arg(raw) for raw in args.run]
    evaluator = _build_evaluator(args.model_name, lexical_only=args.lexical_only)
    rows: list[dict[str, Any]] = []
    for label, details_dir in runs:
        rows.extend(analyze_run(label, details_dir, evaluator))

    rows.sort(key=lambda row: (row["run"], _type_sort_key(row["coarse_type"])))
    if args.output_csv:
        _write_csv(args.output_csv, rows)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(rows, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    if not args.quiet:
        print(_markdown_table(rows))


def analyze_run(
    label: str,
    details_dir: Path,
    evaluator: Evaluator,
) -> list[dict[str, Any]]:
    buckets: defaultdict[str, TypeBucket] = defaultdict(TypeBucket)
    task_count = 0
    for task_dir in _iter_task_dirs(details_dir):
        task = Task.load(task_dir / "task.json")
        gold = _load_json(task_dir / "gold.json")
        prediction = _load_prediction(task_dir)
        if not isinstance(gold, Mapping):
            gold = task.output or {}
        if not isinstance(prediction, Mapping):
            prediction = {}
        task_count += 1
        _accumulate_task(
            evaluator=evaluator,
            task=task,
            gold=dict(gold),
            prediction=dict(prediction),
            buckets=buckets,
        )

    rows: list[dict[str, Any]] = []
    for coarse_type, bucket in buckets.items():
        metrics = bucket.metrics()
        rows.append(
            {
                "run": label,
                "coarse_type": coarse_type,
                "tasks": task_count,
                **_rounded_metrics(metrics),
            }
        )
    return rows


def _accumulate_task(
    *,
    evaluator: Evaluator,
    task: Task,
    gold: dict[str, Any],
    prediction: dict[str, Any],
    buckets: defaultdict[str, TypeBucket],
) -> None:
    root_schema = task.target_schema
    gold_flat = flatten_json(gold, expand_lists=False)
    system_flat = flatten_json(prediction, expand_lists=False)

    for path, system_value in system_flat.items():
        coarse_type = coarse_type_for_path(root_schema, path)
        bucket = buckets[coarse_type]
        bucket.system_count += 1
        bucket.tasks_with_system.add(task.id)

    for path, gold_value in gold_flat.items():
        field_schema = schema_for_flat_path(root_schema, path)
        coarse_type = coarse_type_for_schema(field_schema, root_schema)
        bucket = buckets[coarse_type]
        bucket.gold_count += 1
        bucket.tasks_with_gold.add(task.id)
        if path not in system_flat:
            continue
        bucket.tps += evaluator.score_instance(
            gold_value,
            system_flat[path],
            field_schema,
            root_schema=root_schema,
        )


def schema_for_flat_path(root_schema: JsonDict, path: str) -> JsonDict:
    current = deref(root_schema, root_schema)
    for part in [item for item in path.split(".") if item]:
        current, _ = unwrap_nullable_anyof(current, root_schema)
        current = deref(current, root_schema)
        if schema_type(current) == "array":
            item_schema = current.get("items")
            current = item_schema if isinstance(item_schema, dict) else {}
            current = deref(current, root_schema)
        if schema_type(current) != "object":
            return current if isinstance(current, dict) else {}
        properties = current.get("properties")
        if not isinstance(properties, dict):
            return {}
        next_schema = properties.get(part)
        if not isinstance(next_schema, dict):
            return {}
        current = next_schema
    return current if isinstance(current, dict) else {}


def coarse_type_for_path(root_schema: JsonDict, path: str) -> str:
    return coarse_type_for_schema(schema_for_flat_path(root_schema, path), root_schema)


def coarse_type_for_schema(schema: JsonDict, root_schema: JsonDict) -> str:
    if not schema:
        return "unknown_extra"
    schema, _ = unwrap_nullable_anyof(schema, root_schema)
    schema = deref(schema, root_schema)

    if "enum" in schema:
        return "enum"

    for key in ("anyOf", "oneOf"):
        alternatives = schema.get(key)
        if not isinstance(alternatives, list):
            continue
        non_null = [
            deref(item, root_schema)
            for item in alternatives
            if isinstance(item, dict)
            and deref(item, root_schema).get("type") != "null"
        ]
        labels = sorted(
            {coarse_type_for_schema(item, root_schema) for item in non_null}
        )
        if len(labels) == 1:
            return labels[0]
        return "union"

    current_type = schema.get("type")
    if isinstance(current_type, list):
        non_null_types = sorted(str(item) for item in current_type if item != "null")
        if len(non_null_types) == 1:
            schema = {**schema, "type": non_null_types[0]}
            return coarse_type_for_schema(schema, root_schema)
        return "union"

    if current_type in {"integer", "number"}:
        return "numeric"
    if current_type == "boolean":
        return "boolean"
    if current_type == "string":
        if schema.get("format") in {"date", "date-time", "time"}:
            return "temporal_string"
        return "string"
    if current_type == "array":
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            inner = coarse_type_for_schema(item_schema, root_schema)
            return f"array[{inner}]"
        return "array[unknown]"
    if current_type == "object":
        return "object"
    return "unknown"


def _build_evaluator(model_name: str, *, lexical_only: bool = False) -> Evaluator:
    if lexical_only:
        return _lexical_evaluator()
    try:
        return Evaluator(model_name=model_name)
    except Exception as exc:
        print(
            f"Warning: could not initialize fastembed scorer ({exc}); "
            "falling back to lexical string similarity.",
            file=sys.stderr,
        )
        return _lexical_evaluator()


def _lexical_evaluator() -> Evaluator:
    evaluator = Evaluator.__new__(Evaluator)
    evaluator.model = None
    evaluator.alpha = 0.7
    return evaluator


def _iter_task_dirs(details_dir: Path) -> Iterable[Path]:
    details_dir = details_dir.resolve()
    for task_json in sorted(details_dir.rglob("task.json")):
        task_dir = task_json.parent
        if (task_dir / "gold.json").exists() and (
            (task_dir / "pred.json").exists()
            or (task_dir / "prediction.json").exists()
        ):
            yield task_dir


def _load_prediction(task_dir: Path) -> Any:
    pred_path = task_dir / "pred.json"
    if not pred_path.exists():
        pred_path = task_dir / "prediction.json"
    return _load_json(pred_path)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_run_arg(raw: str) -> tuple[str, Path]:
    if "=" not in raw:
        raise SystemExit(f"--run must have LABEL=DETAILS_DIR form: {raw}")
    label, path = raw.split("=", 1)
    label = label.strip()
    if not label:
        raise SystemExit(f"Run label must not be empty: {raw}")
    details_dir = Path(path)
    if not details_dir.exists():
        raise SystemExit(f"Details directory does not exist: {details_dir}")
    return label, details_dir


def _rounded_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    rounded = dict(metrics)
    for key in ("tps", "precision", "recall", "f1"):
        rounded[key] = round(float(rounded[key]), 6)
    return rounded


def _type_sort_key(value: str) -> tuple[int, str]:
    order = {
        "string": 0,
        "temporal_string": 1,
        "numeric": 2,
        "boolean": 3,
        "enum": 4,
        "object": 5,
        "unknown": 98,
        "unknown_extra": 99,
    }
    if value.startswith("array["):
        return (6, value)
    return (order.get(value, 50), value)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "run",
        "coarse_type",
        "tasks",
        "tasks_with_gold",
        "tasks_with_system",
        "tps",
        "gold_count",
        "system_count",
        "precision",
        "recall",
        "f1",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _markdown_table(rows: list[dict[str, Any]]) -> str:
    headers = [
        "run",
        "coarse_type",
        "gold",
        "system",
        "precision",
        "recall",
        "f1",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["run"]),
                    str(row["coarse_type"]),
                    str(row["gold_count"]),
                    str(row["system_count"]),
                    f'{row["precision"]:.6f}',
                    f'{row["recall"]:.6f}',
                    f'{row["f1"]:.6f}',
                ]
            )
            + " |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
