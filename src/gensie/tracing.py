import json
import re
from pathlib import Path
from typing import Any, Optional, Dict

from gensie.task import Task


def _write_json(path: Path, payload: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def _write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9._-]+", "-", value.strip().lower())
    return slug.strip("-") or "step"


def _get_trace_dir(task: Task) -> Optional[Path]:
    trace_dir = task.metadata.get("_trace_dir")
    if not trace_dir:
        return None
    return Path(trace_dir)


def trace_step(
    task: Task,
    step_name: str,
    prompt: Optional[str] = None,
    request_payload: Optional[Any] = None,
    response_payload: Optional[Any] = None,
    error: Optional[str] = None,
    metrics: Optional[Dict[str, Any]] = None,
):
    trace_dir = _get_trace_dir(task)
    if trace_dir is None:
        return

    steps_dir = trace_dir / "steps"
    steps_dir.mkdir(parents=True, exist_ok=True)

    step_index = int(task.metadata.get("_trace_step_index", 0)) + 1
    task.metadata["_trace_step_index"] = step_index
    step_dir = steps_dir / f"{step_index:02d}-{_slugify(step_name)}"
    step_dir.mkdir(parents=True, exist_ok=True)

    if prompt is not None:
        _write_text(step_dir / "prompt.txt", prompt)
    if request_payload is not None:
        _write_json(step_dir / "request.json", request_payload)
    if response_payload is not None:
        _write_json(step_dir / "response.json", response_payload)
    if error:
        _write_text(step_dir / "error.txt", error)

    summary = {
        "step_index": step_index,
        "step_name": step_name,
        "has_prompt": prompt is not None,
        "has_request": request_payload is not None,
        "has_response": response_payload is not None,
        "error": error,
        "metrics": metrics or {},
    }
    _write_json(step_dir / "summary.json", summary)
