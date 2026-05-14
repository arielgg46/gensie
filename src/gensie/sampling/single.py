from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from gensie.phases import PipelinePhase, VerbatimEntitiesPhase
from gensie.pipeline.context import PipelineContext
from gensie.pipeline.records import AggregationResult
from gensie.pipeline.specs import PhaseKind, PipelineSpec
from gensie.prompts import ReferenceExtractionPromptBuilder
from gensie.prompts.base import PromptBuilder
from gensie.runtime import ChatClient, ChatRequest, build_json_schema_response_format
from gensie.schemas.reasoning import unwrap_reasoning_output


@dataclass(frozen=True)
class SingleExtractionRunner:
    chat_client: ChatClient
    prompt_builder: PromptBuilder = field(default_factory=ReferenceExtractionPromptBuilder)
    phase_registry: Mapping[PhaseKind, PipelinePhase] | None = None

    def __post_init__(self) -> None:
        if self.phase_registry is None:
            object.__setattr__(
                self,
                "phase_registry",
                {PhaseKind.VERBATIM_ENTITIES: VerbatimEntitiesPhase(self.chat_client)},
            )

    def run(
        self, spec: PipelineSpec, context: PipelineContext
    ) -> dict[str, Any] | AggregationResult:
        extraction = spec.extraction
        self._run_pre_phases(extraction.phases, context)
        prompt = self.prompt_builder.build(context, extraction)
        request = ChatRequest(
            model=context.model,
            messages=prompt.messages(),
            response_format=build_json_schema_response_format(
                context.task.target_schema, extraction.reasoning
            ),
            temperature=_temperature(spec),
            metadata={
                "pipeline": spec.name,
                "extraction": extraction.name,
                **prompt.metadata,
            },
        )

        try:
            response = self.chat_client.complete(request)
        except Exception as exc:
            return {"error": f"Failed to call model: {exc}"}

        context.usage.add(response.usage)
        try:
            raw_output = json.loads(response.content)
        except (TypeError, json.JSONDecodeError) as exc:
            return {"error": f"Failed to parse model response: {exc}"}

        try:
            return unwrap_reasoning_output(
                raw_output, context.task.target_schema, extraction.reasoning
            )
        except Exception as exc:
            return {"error": f"Failed to unwrap model response: {exc}"}

    def _run_pre_phases(
        self, phases: tuple[PhaseKind, ...], context: PipelineContext
    ) -> None:
        phase_results = context.metadata.setdefault("phase_results", {})
        for phase_kind in phases:
            phase = dict(self.phase_registry or {}).get(phase_kind)
            if phase is None:
                phase_results[str(phase_kind)] = {
                    "data": {},
                    "metadata": {"error": f"No phase registered for {phase_kind}"},
                }
                continue

            result = phase.run(context)
            context.metadata.update(result.data)
            phase_results[result.name] = {
                "data": dict(result.data),
                "metadata": dict(result.metadata),
            }


def _temperature(spec: PipelineSpec) -> float | None:
    value = spec.extraction.options.get("temperature")
    if isinstance(value, (int, float)):
        return float(value)
    return None
