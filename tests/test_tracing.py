import json
import shutil
import uuid
from pathlib import Path

from gensie.task import Task
from gensie.tracing import trace_step


def test_trace_step_creates_incrementing_step_artifacts_with_metrics():
    base_dir = Path(".test-tracing") / f"trace-{uuid.uuid4().hex}"
    task = Task(
        id="sample_task",
        input_text="Ada Lovelace wrote notes on the Analytical Engine.",
        instruction="Extract the person name.",
        target_schema={
            "type": "object",
            "properties": {"name": {"type": "string"}},
        },
        output={"name": "Ada Lovelace"},
        metadata={"_trace_dir": str(base_dir / "sample_task")},
    )

    try:
        trace_step(
            task,
            "plan",
            prompt="Think about the schema first.",
            request_payload={"messages": [{"role": "user", "content": "plan"}]},
            response_payload={"content": "Done"},
            metrics={
                "tokens": {
                    "prompt_tokens": 5,
                    "completion_tokens": 3,
                    "total_tokens": 8,
                },
                "timings": {
                    "total_duration_ms": 50.0,
                    "time_to_first_token_ms": None,
                },
            },
        )
        trace_step(
            task,
            "extract",
            prompt="Return JSON now.",
            request_payload={"messages": [{"role": "user", "content": "extract"}]},
            response_payload={"content": '{"name": "Ada Lovelace"}'},
            metrics={
                "tokens": {
                    "prompt_tokens": 10,
                    "completion_tokens": 6,
                    "total_tokens": 16,
                },
                "timings": {
                    "total_duration_ms": 125.5,
                    "time_to_first_token_ms": None,
                },
            },
        )

        steps_dir = base_dir / "sample_task" / "steps"
        first_step = steps_dir / "01-plan"
        second_step = steps_dir / "02-extract"

        assert first_step.exists()
        assert second_step.exists()
        assert (first_step / "prompt.txt").exists()
        assert (second_step / "response.json").exists()

        with open(second_step / "summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)

        assert summary["step_index"] == 2
        assert summary["step_name"] == "extract"
        assert summary["metrics"]["tokens"]["total_tokens"] == 16
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)
        shutil.rmtree(base_dir.parent, ignore_errors=True)
