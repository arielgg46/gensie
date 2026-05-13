from __future__ import annotations

from typing import Any, Mapping, Protocol

from gensie.agent import GenSIEAgent
from gensie.pipeline.context import PipelineContext
from gensie.pipeline.records import AggregationResult
from gensie.pipeline.specs import PipelineSpec
from gensie.task import Task
from gensie.usage import UsageTracker


class PipelineRunner(Protocol):
    def run(
        self, spec: PipelineSpec, context: PipelineContext
    ) -> Mapping[str, Any] | AggregationResult:
        pass


class ComposablePipelineAgent(GenSIEAgent):
    def __init__(self, spec: PipelineSpec, runner: PipelineRunner):
        self.spec = spec
        self.runner = runner
        self.usage = UsageTracker()

    def run(self, task: Task, model: str) -> dict[str, Any]:
        self.usage.reset()
        context = PipelineContext(task=task, model=model, usage=self.usage)
        result = self.runner.run(self.spec, context)
        if isinstance(result, AggregationResult):
            return dict(result.output or {"error": "; ".join(result.errors)})
        return dict(result)
