from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from gensie.phases import PipelinePhase, VerbatimEntitiesPhase
from gensie.pipeline.context import PipelineContext
from gensie.pipeline.records import AggregationResult
from gensie.pipeline.specs import PhaseKind, PipelineSpec
from gensie.prompts import ReferenceExtractionPromptBuilder
from gensie.prompts.base import PromptBuilder
from gensie.runtime import (
    ChatClient,
    ChatRequest,
    ChatResponse,
    build_json_schema_response_format,
    request_payload,
    response_payload,
    trace_step,
    usage_payload,
)
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

        started_at = datetime.now(timezone.utc)
        started_perf = time.perf_counter()
        try:
            response = self.chat_client.complete(request)
        except Exception as exc:
            error = f"Failed to call model: {exc}"
            _trace_extraction_step(
                context,
                request,
                started_at=started_at,
                started_perf=started_perf,
                error=error,
            )
            return {"error": error}

        context.usage.add(response.usage)
        try:
            raw_output = json.loads(response.content)
        except (TypeError, json.JSONDecodeError) as exc:
            error = f"Failed to parse model response: {exc}"
            _trace_extraction_step(
                context,
                request,
                response=response,
                started_at=started_at,
                started_perf=started_perf,
                error=error,
            )
            return {"error": error}

        try:
            final_output = unwrap_reasoning_output(
                raw_output, context.task.target_schema, extraction.reasoning
            )
        except Exception as exc:
            error = f"Failed to unwrap model response: {exc}"
            _trace_extraction_step(
                context,
                request,
                response=response,
                raw_output=raw_output,
                started_at=started_at,
                started_perf=started_perf,
                error=error,
            )
            return {"error": error}

        _trace_extraction_step(
            context,
            request,
            response=response,
            raw_output=raw_output,
            final_output=final_output,
            started_at=started_at,
            started_perf=started_perf,
        )
        return final_output

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


def _trace_extraction_step(
    context: PipelineContext,
    request: ChatRequest,
    *,
    started_at: datetime,
    started_perf: float,
    response: ChatResponse | None = None,
    raw_output: Any | None = None,
    final_output: Mapping[str, Any] | None = None,
    error: str | None = None,
) -> None:
    completed_at = datetime.now(timezone.utc)
    duration_ms = (time.perf_counter() - started_perf) * 1000
    payload = (
        response_payload(
            response,
            parsed_output=raw_output,
            final_output=final_output,
        )
        if response is not None
        else {"parsed_output": raw_output, "final_output": final_output}
    )
    trace_step(
        context.task,
        "extract",
        prompt_messages=request.messages,
        request_payload=request_payload(request),
        response_payload=payload,
        error=error,
        metrics={
            "tokens": usage_payload(response.usage if response is not None else None),
            "timings": {
                "started_at": started_at.isoformat(),
                "completed_at": completed_at.isoformat(),
                "total_duration_ms": round(duration_ms, 3),
                "time_to_first_token_ms": None,
                "time_to_first_token_note": "Not captured by the current non-streaming pipeline.",
            },
        },
    )
