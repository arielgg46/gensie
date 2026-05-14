import json
import shutil
from pathlib import Path

from gensie.pipeline import ExtractionSpec, PipelineContext, PipelineSpec, ReasoningMode
from gensie.runtime import ChatMessage, ChatResponse, trace_step, trace_task_result
from gensie.sampling import SingleExtractionRunner
from gensie.task import Task
from gensie.usage import UsageTracker


class FakeChatClient:
    def __init__(self, content: str):
        self.content = content

    def complete(self, request):
        return ChatResponse(
            content=self.content,
            usage={"prompt_tokens": 10, "completion_tokens": 4},
            raw={"id": "chatcmpl-test"},
        )


def _task(trace_dir: Path) -> Task:
    return Task(
        id="sample_task",
        input_text="Ada Lovelace wrote notes.",
        instruction="Extract the person.",
        target_schema={
            "type": "object",
            "properties": {"person": {"type": "string"}},
            "required": ["person"],
        },
        output={"person": "Ada Lovelace"},
        metadata={"_trace_dir": str(trace_dir / "sample_task")},
    )


def test_trace_step_creates_incrementing_step_artifacts():
    trace_dir = Path("test-artifacts/unit-tracing-step")
    shutil.rmtree(trace_dir, ignore_errors=True)
    try:
        task = _task(trace_dir)

        trace_step(
            task,
            "plan",
            prompt_messages=(
                ChatMessage(role="system", content="Plan."),
                ChatMessage(role="user", content="plan"),
            ),
            request_payload={
                "messages": [
                    {"role": "system", "content": "Plan."},
                    {"role": "user", "content": "plan"},
                ]
            },
            response_payload={"content": "Done"},
            metrics={"tokens": {"total_tokens": 8}},
        )
        trace_step(
            task,
            "extract",
            prompt_messages=(ChatMessage(role="user", content="Extract."),),
            request_payload={"messages": [{"role": "user", "content": "extract"}]},
            response_payload={"content": '{"person": "Ada Lovelace"}'},
            metrics={"tokens": {"total_tokens": 14}},
        )

        first_step = trace_dir / "sample_task" / "steps" / "01-plan"
        second_step = trace_dir / "sample_task" / "steps" / "02-extract"
        assert not (first_step / "prompt.txt").exists()
        assert (first_step / "system_prompt.txt").read_text(encoding="utf-8") == "Plan."
        assert (first_step / "user_prompt.txt").read_text(encoding="utf-8") == "plan"
        assert (second_step / "user_prompt.txt").read_text(encoding="utf-8") == "Extract."
        assert (second_step / "response.json").exists()
        summary = json.loads((second_step / "summary.json").read_text(encoding="utf-8"))
        assert summary["step_index"] == 2
        assert summary["step_name"] == "extract"
        assert summary["prompt_files"] == ["user_prompt.txt"]
        assert summary["metrics"]["tokens"]["total_tokens"] == 14
    finally:
        shutil.rmtree(trace_dir, ignore_errors=True)


def test_single_extraction_runner_traces_request_response_and_final_output():
    trace_dir = Path("test-artifacts/unit-tracing-runner")
    shutil.rmtree(trace_dir, ignore_errors=True)
    try:
        task = _task(trace_dir)
        context = PipelineContext(task=task, model="demo", usage=UsageTracker())
        spec = PipelineSpec(
            name="baseline",
            description="baseline",
            extraction=ExtractionSpec(name="baseline", reasoning=ReasoningMode.NONE),
        )
        runner = SingleExtractionRunner(FakeChatClient('{"person":"Ada Lovelace"}'))

        output = runner.run(spec, context)

        assert output == {"person": "Ada Lovelace"}
        step_dir = trace_dir / "sample_task" / "steps" / "01-extract"
        assert (step_dir / "system_prompt.txt").exists()
        assert (step_dir / "user_prompt.txt").exists()
        assert not (step_dir / "prompt.txt").exists()
        request = json.loads((step_dir / "request.json").read_text(encoding="utf-8"))
        response = json.loads((step_dir / "response.json").read_text(encoding="utf-8"))
        assert request["model"] == "demo"
        assert request["metadata"]["pipeline"] == "baseline"
        assert response["parsed_output"] == {"person": "Ada Lovelace"}
        assert response["final_output"] == {"person": "Ada Lovelace"}
        assert response["raw"] == {"id": "chatcmpl-test"}
    finally:
        shutil.rmtree(trace_dir, ignore_errors=True)


def test_trace_task_result_writes_pred_and_gold_next_to_steps():
    trace_dir = Path("test-artifacts/unit-tracing-task-result")
    shutil.rmtree(trace_dir, ignore_errors=True)
    try:
        task = _task(trace_dir)

        trace_task_result(task, pred={"person": "Ada Lovelace"}, gold=task.output)

        task_dir = trace_dir / "sample_task"
        pred = json.loads((task_dir / "pred.json").read_text(encoding="utf-8"))
        gold = json.loads((task_dir / "gold.json").read_text(encoding="utf-8"))
        assert pred == {"person": "Ada Lovelace"}
        assert gold == {"person": "Ada Lovelace"}
    finally:
        shutil.rmtree(trace_dir, ignore_errors=True)
