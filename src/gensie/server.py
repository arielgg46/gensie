from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from gensie.task import Task
from gensie.agent import Participant
from gensie.runtime import trace_task_result
from typing import Any
import importlib
import os
import traceback

from logging import getLogger

logger = getLogger("gensie")

app = FastAPI(title="GenSIE Agent Server")

# Global participant instance
participant: Participant = None


def get_participant() -> Participant:
    global participant
    if participant is None:
        # Load participant from environment or default to OfficialParticipant
        participant_path = os.getenv(
            "PARTICIPANT_PATH", "gensie.baseline.OfficialParticipant"
        )
        try:
            module_name, class_name = participant_path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            participant_class = getattr(module, class_name)
            participant = participant_class()
        except Exception as e:
            raise RuntimeError(f"Failed to load participant {participant_path}: {e}")
    return participant


@app.get("/info")
async def info():
    """Returns metadata about the participant and available pipelines."""
    return get_participant().get_info()


@app.post("/run")
async def run_task(
    task: Task,
    pipeline: str = Query("baseline", description="Name of the pipeline to execute"),
    model: str = Query(..., description="The exact model name to use for inference"),
) -> Any:
    """Executes the extraction task using the specified pipeline and model.

    The response body is the extracted JSON object. If the agent exposes a
    ``usage`` tracker (see ``gensie.usage.UsageTracker``), its tally is reported
    in the ``X-GenSIE-Token-Usage`` response header.
    """
    try:
        p = get_participant()
        agent = p.get_agent(pipeline)

        trace_task_result(task, gold=task.output)
        result = agent.run(task, model=model)
        trace_task_result(task, pred=result, gold=task.output)
        headers = {}
        tracker = getattr(agent, "usage", None)
        if tracker is not None and hasattr(tracker, "header_value"):
            headers["X-GenSIE-Token-Usage"] = tracker.header_value()
        usage_info = headers.get("X-GenSIE-Token-Usage", "n/a")

        # The pipeline swallows model-call / parsing failures into an ``error``
        # field and still returns a valid dict. That would otherwise be reported
        # as a healthy 200 with empty usage (calls=0), hiding the real problem.
        # Surface it loudly in the terminal instead.
        pipeline_error = result.get("error") if isinstance(result, dict) else None
        if pipeline_error:
            logger.error(
                "Task returned an error (pipeline=%s, model=%s, usage=%s): %s",
                pipeline,
                model,
                usage_info,
                pipeline_error,
            )
            print(
                f"[ERROR] Pipeline returned an error (pipeline={pipeline}, "
                f"model={model}, usage={usage_info}): {pipeline_error}",
                flush=True,
            )
        else:
            logger.info(
                "Task completed (pipeline=%s, model=%s, usage=%s)",
                pipeline,
                model,
                usage_info,
            )
            print(
                f"[200] Task completed (pipeline={pipeline}, model={model}, usage={usage_info})",
                flush=True,
            )
        return JSONResponse(content=result, headers=headers)
    except Exception as e:
        tb = traceback.format_exc()
        logger.error("Error running task (pipeline=%s, model=%s):\n%s", pipeline, model, tb)
        # Also print directly to the terminal so the full traceback is always
        # visible even if logging is not configured to surface it.
        print(tb, flush=True)
        raise HTTPException(status_code=500, detail=str(e))
