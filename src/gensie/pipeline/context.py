from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from gensie.task import Task
from gensie.usage import UsageTracker


@dataclass
class PipelineContext:
    task: Task
    model: str
    usage: UsageTracker
    metadata: dict[str, Any] = field(default_factory=dict)
