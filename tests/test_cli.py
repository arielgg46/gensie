import json
import shutil
import uuid
from pathlib import Path

from gensie.cli import _write_task_details
from gensie.task import Task


def test_write_task_details_persists_artifacts_and_trace_metrics():
    task = Task(
        id="sample_task",
        input_text="Ada Lovelace wrote notes on the Analytical Engine.",
        instruction="Extract the person name.",
        target_schema={
            "type": "object",
            "properties": {"name": {"type": "string"}},
        },
        output={"name": "Ada Lovelace"},
    )

    base_dir = Path("test-artifacts") / f"cli-{uuid.uuid4().hex}"
    try:
        step_dir = base_dir / "sample_task" / "steps" / "01-extract"
        step_dir.mkdir(parents=True, exist_ok=True)
        with open(step_dir / "summary.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "step_index": 1,
                    "step_name": "extract",
                    "error": None,
                    "metrics": {
                        "tokens": {
                            "prompt_tokens": 12,
                            "completion_tokens": 7,
                            "total_tokens": 19,
                        },
                        "timings": {
                            "total_duration_ms": 123.4,
                            "time_to_first_token_ms": None,
                        },
                    },
                },
                f,
                indent=2,
            )

        summary = _write_task_details(
            base_dir,
            task,
            system_output={"name": "Ada Lovelace"},
            tps=1.0,
            gold_keys=1,
            system_keys=1,
            status="PASS",
        )

        task_dir = base_dir / "sample_task"
        assert (task_dir / "prompt.txt").exists()
        assert (task_dir / "task.json").exists()
        assert (task_dir / "gold.json").exists()
        assert (task_dir / "prediction.json").exists()
        assert (task_dir / "summary.json").exists()

        assert summary["trace_metrics"]["tokens"]["prompt_tokens"] == 12
        assert summary["trace_metrics"]["tokens"]["completion_tokens"] == 7
        assert summary["trace_metrics"]["tokens"]["total_tokens"] == 19
        assert summary["trace_metrics"]["timings"]["total_duration_ms"] == 123.4
        assert summary["trace_metrics"]["timings"]["time_to_first_token_ms"] is None

        with open(task_dir / "summary.json", "r", encoding="utf-8") as f:
            saved_summary = json.load(f)

        assert saved_summary["trace_metrics"]["request_count"] == 1
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)
