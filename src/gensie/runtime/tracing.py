from __future__ import annotations

import dataclasses
import json
import os
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from pydantic import BaseModel

from gensie.runtime.chat import ChatMessage, ChatRequest, ChatResponse
from gensie.task import Task


FALSE_VALUES = {"0", "false", "no", "off"}


def trace_step(
    task: Task,
    step_name: str,
    *,
    prompt_messages: Sequence[ChatMessage] | None = None,
    request_payload: Any | None = None,
    response_payload: Any | None = None,
    error: str | None = None,
    metrics: Mapping[str, Any] | None = None,
) -> None:
    trace_dir = trace_dir_for_task(task)
    if trace_dir is None:
        return

    step_index = int(task.metadata.get("_trace_step_index", 0)) + 1
    task.metadata["_trace_step_index"] = step_index
    step_dir = trace_dir / "steps" / f"{step_index:02d}-{slugify(step_name)}"
    step_dir.mkdir(parents=True, exist_ok=True)

    prompt_files = _write_prompt_files(step_dir, prompt_messages)
    if request_payload is not None:
        _write_json(step_dir / "request.json", request_payload)
    if response_payload is not None:
        _write_json(step_dir / "response.json", response_payload)
    if error:
        _write_text(step_dir / "error.txt", error)

    _write_json(
        step_dir / "summary.json",
        {
            "step_index": step_index,
            "step_name": step_name,
            "has_prompt": bool(prompt_files),
            "prompt_files": prompt_files,
            "has_request": request_payload is not None,
            "has_response": response_payload is not None,
            "error": error,
            "metrics": dict(metrics or {}),
        },
    )


_MISSING = object()


def trace_task_result(
    task: Task,
    *,
    pred: Any = _MISSING,
    gold: Any = _MISSING,
) -> None:
    trace_dir = trace_dir_for_task(task)
    if trace_dir is None:
        return

    trace_dir.mkdir(parents=True, exist_ok=True)
    if pred is not _MISSING:
        _write_json(trace_dir / "pred.json", pred)
    if gold is not _MISSING:
        _write_json(trace_dir / "gold.json", gold)


def trace_dir_for_task(task: Task) -> Path | None:
    if _env_disabled("GENSIE_TRACE_ENABLED"):
        return None

    metadata_dir = task.metadata.get("_trace_dir")
    if metadata_dir:
        return Path(str(metadata_dir))

    env_dir = os.getenv("GENSIE_TRACE_DIR")
    if not env_dir:
        return None
    return Path(env_dir) / slugify(task.id)


def tracing_enabled(task: Task) -> bool:
    return trace_dir_for_task(task) is not None


def request_payload(request: ChatRequest) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": request.model,
        "messages": messages_payload(request.messages),
    }
    if request.response_format is not None:
        payload["response_format"] = to_jsonable(request.response_format)
    if request.temperature is not None:
        payload["temperature"] = request.temperature
    if request.options:
        payload["options"] = to_jsonable(request.options)
    if request.metadata:
        payload["metadata"] = to_jsonable(request.metadata)
    return payload


def response_payload(response: ChatResponse, **extra: Any) -> dict[str, Any]:
    payload = {
        "content": response.content,
        "usage": usage_payload(response.usage),
        "raw": to_jsonable(response.raw),
        "metadata": to_jsonable(response.metadata),
    }
    payload.update({key: to_jsonable(value) for key, value in extra.items()})
    return payload


def messages_payload(messages: Sequence[ChatMessage]) -> list[dict[str, str]]:
    return [
        {"role": message.role, "content": message.content} for message in messages
    ]


def prompt_texts_by_role(messages: Sequence[ChatMessage]) -> dict[str, str]:
    grouped: dict[str, list[str]] = {}
    for message in messages:
        grouped.setdefault(message.role, []).append(message.content)
    return {role: "\n\n".join(parts) for role, parts in grouped.items()}


def render_prompt(messages: Sequence[ChatMessage]) -> str:
    sections = []
    for message in messages:
        sections.append(f"{message.role.upper()}:\n{message.content}")
    return "\n\n".join(sections)


def usage_payload(usage: Any) -> dict[str, Any]:
    if usage is None:
        return {
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
        }
    data = to_jsonable(usage)
    if not isinstance(data, dict):
        return {"raw": data}
    prompt_tokens = data.get("prompt_tokens")
    completion_tokens = data.get("completion_tokens")
    total_tokens = data.get("total_tokens")
    if (
        total_tokens is None
        and isinstance(prompt_tokens, int)
        and isinstance(completion_tokens, int)
    ):
        total_tokens = prompt_tokens + completion_tokens
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


def to_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, BaseModel):
        return to_jsonable(value.model_dump(mode="json"))
    if hasattr(value, "model_dump") and callable(value.model_dump):
        try:
            return to_jsonable(value.model_dump())
        except Exception:
            pass
    if dataclasses.is_dataclass(value):
        return to_jsonable(dataclasses.asdict(value))
    if isinstance(value, Mapping):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(item) for item in value]
    return repr(value)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9._-]+", "-", value.strip().lower())
    return slug.strip("-") or "item"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(to_jsonable(payload), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_prompt_files(
    step_dir: Path, prompt_messages: Sequence[ChatMessage] | None
) -> list[str]:
    if prompt_messages is None:
        return []

    prompt_files = []
    for role, content in prompt_texts_by_role(prompt_messages).items():
        filename = f"{slugify(role)}_prompt.txt"
        _write_text(step_dir / filename, content)
        prompt_files.append(filename)
    return prompt_files


def _env_disabled(name: str) -> bool:
    value = os.getenv(name)
    return value is not None and value.strip().lower() in FALSE_VALUES
