from __future__ import annotations

import copy
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from gensie.eval import Evaluator, flatten_json
from gensie.fsp.field_rag import normalized_schema_fingerprint
from gensie.fsp.retrieval import _field_tags
from gensie.schemas.fields import FieldInfo, parse_schema_fields
from gensie.task import Task

BASE_EXTRACTOR_PIPELINES = (
    "enriched-schema-rag",
    "enriched-inline-reasoning-rag",
)


@dataclass(frozen=True)
class RunSource:
    pipeline: str
    label: str
    directory: Path
    source_kind: str


@dataclass(frozen=True)
class PredictionRecord:
    pipeline: str
    task_id: str
    run_id: str
    source_kind: str
    response_path: Path
    final_output: Mapping[str, Any]
    step_name: str | None = None

    def manifest(self, output_path: Path) -> dict[str, Any]:
        return {
            "pipeline": self.pipeline,
            "task_id": self.task_id,
            "run_id": self.run_id,
            "source_kind": self.source_kind,
            "step_name": self.step_name,
            "response_path": str(self.response_path),
            "prediction_path": str(output_path),
        }


@dataclass
class MetricBucket:
    tps: list[float] = field(default_factory=list)
    gold_counts: list[int] = field(default_factory=list)
    system_counts: list[int] = field(default_factory=list)
    precisions: list[float] = field(default_factory=list)
    recalls: list[float] = field(default_factory=list)
    f1s: list[float] = field(default_factory=list)
    task_ids: set[str] = field(default_factory=set)

    def add(
        self,
        *,
        task_id: str,
        true_positive_score: float,
        gold_count: int,
        system_count: int,
    ) -> None:
        self.tps.append(true_positive_score)
        self.gold_counts.append(gold_count)
        self.system_counts.append(system_count)
        precision = true_positive_score / system_count if system_count > 0 else 0.0
        recall = true_positive_score / gold_count if gold_count > 0 else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall > 0
            else 0.0
        )
        self.precisions.append(precision)
        self.recalls.append(recall)
        self.f1s.append(f1)
        self.task_ids.add(task_id)

    def summary(self, evaluator: Evaluator) -> dict[str, Any]:
        metrics = evaluator.calculate_metrics(
            self.tps,
            self.gold_counts,
            self.system_counts,
        )
        return {
            "prediction_count": len(self.tps),
            "task_count": len(self.task_ids),
            "task_ids": sorted(self.task_ids),
            "tps_total": round(sum(self.tps), 6),
            "gold_count_total": sum(self.gold_counts),
            "system_count_total": sum(self.system_counts),
            "metrics": {key: round(float(value), 6) for key, value in metrics.items()},
            "average_metrics": {
                "precision": round(_average(self.precisions), 6),
                "recall": round(_average(self.recalls), 6),
                "f1": round(_average(self.f1s), 6),
            },
        }


class CachedEvaluator(Evaluator):
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        super().__init__(model_name=model_name)
        self._semantic_cache: dict[tuple[str, str], float] = {}

    def semantic_similarity(self, s1: str, s2: str) -> float:
        key = (str(s1), str(s2))
        cached = self._semantic_cache.get(key)
        if cached is not None:
            return cached
        value = super().semantic_similarity(s1, s2)
        self._semantic_cache[key] = value
        return value


def _average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def analyze_rag_experiment_artifacts(
    *,
    golden_dir: Path,
    output_dir: Path,
    enriched_schema_golden_dir: Path,
    enriched_schema_dev_dir: Path,
    enriched_inline_golden_dir: Path,
    enriched_inline_dev_dir: Path,
    mixed_dir: Path,
    evaluator: Evaluator | None = None,
) -> dict[str, Any]:
    tasks = _load_golden_tasks(golden_dir)
    scorer = evaluator or CachedEvaluator()
    output_dir.mkdir(parents=True, exist_ok=True)

    run_sources = (
        RunSource(
            pipeline="enriched-schema-rag",
            label="golden_direct",
            directory=enriched_schema_golden_dir,
            source_kind="direct_golden",
        ),
        RunSource(
            pipeline="enriched-schema-rag",
            label="dev_direct",
            directory=enriched_schema_dev_dir,
            source_kind="direct_dev",
        ),
        RunSource(
            pipeline="enriched-inline-reasoning-rag",
            label="golden_direct",
            directory=enriched_inline_golden_dir,
            source_kind="direct_golden",
        ),
        RunSource(
            pipeline="enriched-inline-reasoning-rag",
            label="dev_direct",
            directory=enriched_inline_dev_dir,
            source_kind="direct_dev",
        ),
    )

    records: list[PredictionRecord] = []
    for source in run_sources:
        records.extend(_collect_direct_predictions(source, tasks))
    records.extend(_collect_mixed_predictions(mixed_dir, tasks))

    prediction_paths = _write_predictions(output_dir, records)
    run_counts = _build_run_counts(tasks, records)
    manifest = {
        "golden_dir": str(golden_dir),
        "output_dir": str(output_dir),
        "prediction_count": len(records),
        "records": [
            record.manifest(prediction_paths[_record_key(record)]) for record in records
        ],
    }

    metrics = _build_metrics(tasks, records, scorer)
    summary_md = _render_summary(run_counts, metrics)

    _write_json(output_dir / "run_counts.json", run_counts)
    _write_json(output_dir / "prediction_manifest.json", manifest)
    metrics_dir = output_dir / "metrics"
    _write_json(metrics_dir / "by_schema.json", metrics["by_schema"])
    _write_json(metrics_dir / "by_prefix.json", metrics["by_prefix"])
    _write_json(metrics_dir / "by_field_tag.json", metrics["by_field_tag"])
    (output_dir / "summary.md").write_text(summary_md, encoding="utf-8")

    result = {
        "golden_task_count": len(tasks),
        "prediction_count": len(records),
        "output_dir": str(output_dir),
        "metrics": {
            "overall": metrics["overall"],
        },
    }
    _write_json(output_dir / "analysis_summary.json", result)
    return result


def _load_golden_tasks(golden_dir: Path) -> dict[str, Task]:
    tasks: dict[str, Task] = {}
    for path in sorted(golden_dir.rglob("*.json")):
        task = Task.load(path)
        if task.output is None:
            raise ValueError(f"golden task has no curated output: {path}")
        tasks[task.id] = task
    if not tasks:
        raise ValueError(f"no golden tasks found in {golden_dir}")
    return tasks


def _collect_direct_predictions(
    source: RunSource,
    tasks: Mapping[str, Task],
) -> list[PredictionRecord]:
    records: list[PredictionRecord] = []
    for task_id in sorted(tasks):
        response_path = _direct_response_path(source.directory, task_id)
        final_output = _read_final_output(response_path)
        if final_output is None:
            continue
        records.append(
            PredictionRecord(
                pipeline=source.pipeline,
                task_id=task_id,
                run_id=source.label,
                source_kind=source.source_kind,
                response_path=response_path,
                final_output=final_output,
                step_name="extract",
            )
        )
    return records


def _collect_mixed_predictions(
    mixed_dir: Path,
    tasks: Mapping[str, Task],
) -> list[PredictionRecord]:
    records: list[PredictionRecord] = []
    for task_id in sorted(tasks):
        steps_dir = mixed_dir / task_id / "steps"
        if not steps_dir.is_dir():
            continue
        for step_dir in sorted(path for path in steps_dir.iterdir() if path.is_dir()):
            summary = _read_json(step_dir / "summary.json")
            if not isinstance(summary, dict):
                continue
            step_name = summary.get("step_name")
            if not isinstance(step_name, str) or not step_name.startswith(
                "self_consistency_trial_"
            ):
                continue
            if summary.get("error") is not None:
                continue
            request_metadata = summary.get("request_metadata") or {}
            if not isinstance(request_metadata, dict):
                continue
            pipeline = request_metadata.get("extraction")
            if pipeline not in BASE_EXTRACTOR_PIPELINES:
                continue
            response_path = step_dir / "response.json"
            final_output = _read_final_output(response_path)
            if final_output is None:
                continue
            trial_suffix = step_name.removeprefix("self_consistency_trial_")
            records.append(
                PredictionRecord(
                    pipeline=str(pipeline),
                    task_id=task_id,
                    run_id=f"mixed_trial_{trial_suffix}",
                    source_kind="mixed_trial",
                    response_path=response_path,
                    final_output=final_output,
                    step_name=step_name,
                )
            )
    return records


def _direct_response_path(run_dir: Path, task_id: str) -> Path:
    return run_dir / task_id / "steps" / "01-extract" / "response.json"


def _read_final_output(response_path: Path) -> Mapping[str, Any] | None:
    payload = _read_json(response_path)
    if not isinstance(payload, dict):
        return None
    final_output = payload.get("final_output")
    return final_output if isinstance(final_output, dict) else None


def _read_json(path: Path) -> Any:
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_predictions(
    output_dir: Path, records: list[PredictionRecord]
) -> dict[str, Path]:
    prediction_paths: dict[str, Path] = {}
    for record in records:
        path = (
            output_dir
            / "predictions"
            / record.pipeline
            / record.task_id
            / f"{record.run_id}.json"
        )
        _write_json(path, record.final_output)
        prediction_paths[_record_key(record)] = path
    return prediction_paths


def _record_key(record: PredictionRecord) -> str:
    return "\x1f".join(
        (
            record.pipeline,
            record.task_id,
            record.run_id,
            record.source_kind,
            str(record.response_path),
        )
    )


def _build_run_counts(
    tasks: Mapping[str, Task],
    records: list[PredictionRecord],
) -> dict[str, Any]:
    counts: dict[str, Any] = {
        task_id: {
            pipeline: {"count": 0, "runs": [], "sources": {}}
            for pipeline in BASE_EXTRACTOR_PIPELINES
        }
        for task_id in sorted(tasks)
    }
    for record in records:
        item = counts[record.task_id][record.pipeline]
        item["count"] += 1
        item["runs"].append(record.run_id)
        item["sources"][record.source_kind] = (
            int(item["sources"].get(record.source_kind, 0)) + 1
        )
    return counts


def _build_metrics(
    tasks: Mapping[str, Task],
    records: list[PredictionRecord],
    evaluator: Evaluator,
) -> dict[str, Any]:
    overall = {pipeline: MetricBucket() for pipeline in BASE_EXTRACTOR_PIPELINES}
    by_prefix = {
        pipeline: defaultdict(MetricBucket) for pipeline in BASE_EXTRACTOR_PIPELINES
    }
    by_schema = {
        pipeline: defaultdict(MetricBucket) for pipeline in BASE_EXTRACTOR_PIPELINES
    }
    by_field_tag = {
        pipeline: defaultdict(MetricBucket) for pipeline in BASE_EXTRACTOR_PIPELINES
    }
    schema_metadata = _schema_metadata(tasks)

    for record in records:
        task = tasks[record.task_id]
        gold = task.output or {}
        prediction = dict(record.final_output)
        score, gold_count, system_count = _score_output(
            evaluator, gold, prediction, task.target_schema
        )
        prefix = _task_prefix(task.id)
        schema_key = normalized_schema_fingerprint(task.target_schema)

        overall[record.pipeline].add(
            task_id=task.id,
            true_positive_score=score,
            gold_count=gold_count,
            system_count=system_count,
        )
        by_prefix[record.pipeline][prefix].add(
            task_id=task.id,
            true_positive_score=score,
            gold_count=gold_count,
            system_count=system_count,
        )
        by_schema[record.pipeline][schema_key].add(
            task_id=task.id,
            true_positive_score=score,
            gold_count=gold_count,
            system_count=system_count,
        )

        for field_info, field_schema in _top_level_fields(task.target_schema):
            tags = _field_tags(field_info)
            if not tags:
                continue
            field_score, field_gold_count, field_system_count = _score_field(
                evaluator=evaluator,
                task=task,
                field_info=field_info,
                field_schema=field_schema,
                prediction=prediction,
            )
            for tag in tags:
                by_field_tag[record.pipeline][tag].add(
                    task_id=task.id,
                    true_positive_score=field_score,
                    gold_count=field_gold_count,
                    system_count=field_system_count,
                )

    return {
        "overall": {
            pipeline: bucket.summary(evaluator)
            for pipeline, bucket in overall.items()
        },
        "by_prefix": {
            "pipelines": {
                pipeline: {
                    "overall": overall[pipeline].summary(evaluator),
                    "groups": _summarize_bucket_mapping(buckets, evaluator),
                }
                for pipeline, buckets in by_prefix.items()
            }
        },
        "by_schema": {
            "pipelines": {
                pipeline: {
                    "overall": overall[pipeline].summary(evaluator),
                    "groups": _summarize_schema_buckets(
                        buckets, evaluator, schema_metadata
                    ),
                }
                for pipeline, buckets in by_schema.items()
            }
        },
        "by_field_tag": {
            "pipelines": {
                pipeline: {
                    "overall": overall[pipeline].summary(evaluator),
                    "groups": _summarize_bucket_mapping(buckets, evaluator),
                }
                for pipeline, buckets in by_field_tag.items()
            }
        },
    }


def _score_output(
    evaluator: Evaluator,
    gold: Mapping[str, Any],
    prediction: Mapping[str, Any],
    schema: Mapping[str, Any],
) -> tuple[float, int, int]:
    gold_count = len(flatten_json(gold, expand_lists=False))
    system_count = len(flatten_json(prediction, expand_lists=False))
    if gold_count == 0 and system_count == 0:
        return 0.0, 0, 0
    score = evaluator.score_instance(
        gold,
        prediction,
        dict(schema),
    )
    return float(score), gold_count, system_count


def _score_field(
    *,
    evaluator: Evaluator,
    task: Task,
    field_info: FieldInfo,
    field_schema: Mapping[str, Any],
    prediction: Mapping[str, Any],
) -> tuple[float, int, int]:
    gold = task.output or {}
    gold_present = field_info.name in gold
    system_present = field_info.name in prediction
    gold_value = gold.get(field_info.name)
    system_value = prediction.get(field_info.name)
    gold_count = _value_count(gold_value, present=gold_present)
    system_count = _value_count(system_value, present=system_present)
    if gold_count == 0 and system_count == 0:
        return 0.0, 0, 0
    if not gold_present or not system_present:
        return 0.0, gold_count, system_count
    score = evaluator.score_instance(
        gold_value,
        system_value,
        dict(field_schema),
        root_schema=task.target_schema,
    )
    return float(score), gold_count, system_count


def _value_count(value: Any, *, present: bool) -> int:
    if not present:
        return 0
    return len(flatten_json(value, expand_lists=False))


def _top_level_fields(
    schema: Mapping[str, Any],
) -> list[tuple[FieldInfo, Mapping[str, Any]]]:
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return []
    fields = parse_schema_fields(dict(schema))
    result: list[tuple[FieldInfo, Mapping[str, Any]]] = []
    for field_info in fields:
        field_schema = properties.get(field_info.name)
        if isinstance(field_schema, dict):
            result.append((field_info, copy.deepcopy(field_schema)))
    return result


def _summarize_bucket_mapping(
    buckets: Mapping[str, MetricBucket],
    evaluator: Evaluator,
) -> dict[str, Any]:
    return {
        name: bucket.summary(evaluator)
        for name, bucket in sorted(buckets.items())
    }


def _summarize_schema_buckets(
    buckets: Mapping[str, MetricBucket],
    evaluator: Evaluator,
    schema_metadata: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    groups: dict[str, Any] = {}
    for schema_key, bucket in sorted(buckets.items()):
        groups[schema_key] = {
            **schema_metadata.get(schema_key, {}),
            **bucket.summary(evaluator),
        }
    return groups


def _schema_metadata(tasks: Mapping[str, Task]) -> dict[str, dict[str, Any]]:
    metadata: dict[str, dict[str, Any]] = {}
    for task in tasks.values():
        schema_key = normalized_schema_fingerprint(task.target_schema)
        item = metadata.setdefault(
            schema_key,
            {
                "description": task.target_schema.get("description"),
                "task_ids": [],
            },
        )
        item["task_ids"].append(task.id)
    for item in metadata.values():
        item["task_ids"] = sorted(set(item["task_ids"]))
    return metadata


def _task_prefix(task_id: str) -> str:
    return re.sub(r"_\d+$", "", task_id)


def _render_summary(run_counts: Mapping[str, Any], metrics: Mapping[str, Any]) -> str:
    lines = [
        "# Resumen de análisis RAG",
        "",
        "Todas las métricas usan como referencia el output curado de `data/golden_cover`,",
        "incluso cuando la predicción proviene de una corrida sobre `data/dev`.",
        "",
        "## Corridas efectivas",
        "",
        "| Pipeline | Tasks | Total preds | Min/task | Max/task | Avg/task |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for pipeline in BASE_EXTRACTOR_PIPELINES:
        values = [int(item[pipeline]["count"]) for item in run_counts.values()]
        total = sum(values)
        avg = total / len(values) if values else 0.0
        lines.append(
            f"| `{pipeline}` | {len(values)} | {total} | "
            f"{min(values) if values else 0} | {max(values) if values else 0} | "
            f"{avg:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Métricas globales",
            "",
            "| Pipeline | Predictions | Micro P | Micro R | Micro F1 | Avg P | Avg R | Avg F1 |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    overall = metrics["overall"]
    for pipeline in BASE_EXTRACTOR_PIPELINES:
        item = overall[pipeline]
        values = item["metrics"]
        averages = item["average_metrics"]
        lines.append(
            f"| `{pipeline}` | {item['prediction_count']} | "
            f"{values['precision']:.4f} | {values['recall']:.4f} | "
            f"{values['f1']:.4f} | {averages['precision']:.4f} | "
            f"{averages['recall']:.4f} | {averages['f1']:.4f} |"
        )

    lines.extend(
        [
            "",
            "Ver detalles en `metrics/by_schema.json`, `metrics/by_prefix.json` y",
            "`metrics/by_field_tag.json`.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
