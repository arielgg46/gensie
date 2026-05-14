from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from gensie.phases import PipelinePhase, VerbatimEntitiesPhase
from gensie.pipeline.context import PipelineContext
from gensie.pipeline.records import AggregationResult, ExtractionResult
from gensie.pipeline.specs import ExtractionSpec, PhaseKind, PipelineSpec
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
from gensie.schemas import extract_reasoning_view
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
        result = self.run_extraction(spec, context)
        if result.is_valid:
            return dict(result.output or {})
        error = "; ".join(result.errors) or "Failed to run extraction."
        return {"error": error}

    def run_extraction(
        self,
        spec: PipelineSpec,
        context: PipelineContext,
        *,
        extraction_override: ExtractionSpec | None = None,
        step_name: str = "extract",
        generation_options: Mapping[str, Any] | None = None,
    ) -> ExtractionResult:
        extraction = spec.extraction
        if extraction_override is not None:
            extraction = extraction_override
        self._run_pre_phases(extraction.phases, context)
        prompt = self.prompt_builder.build(context, extraction)
        options = {**dict(extraction.options), **dict(generation_options or {})}
        temperature, request_options = _request_generation_options(options)
        request = ChatRequest(
            model=context.model,
            messages=prompt.messages(),
            response_format=build_json_schema_response_format(
                context.task.target_schema,
                extraction.reasoning,
                name=str(options.get("response_format_name") or "extraction"),
            ),
            temperature=temperature,
            options=request_options,
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
                step_name=step_name,
                started_at=started_at,
                started_perf=started_perf,
                error=error,
            )
            return ExtractionResult(output=None, errors=(error,))

        context.usage.add(response.usage)
        try:
            raw_output = json.loads(response.content)
        except (TypeError, json.JSONDecodeError) as exc:
            error = f"Failed to parse model response: {exc}"
            _trace_extraction_step(
                context,
                request,
                step_name=step_name,
                response=response,
                started_at=started_at,
                started_perf=started_perf,
                error=error,
            )
            return ExtractionResult(
                output=None,
                raw_output=response.content,
                errors=(error,),
                metadata={"response": response_payload(response)},
            )

        try:
            final_output = unwrap_reasoning_output(
                raw_output, context.task.target_schema, extraction.reasoning
            )
            reasoning_view = extract_reasoning_view(
                raw_output, context.task.target_schema, extraction.reasoning
            )
        except Exception as exc:
            error = f"Failed to unwrap model response: {exc}"
            _trace_extraction_step(
                context,
                request,
                step_name=step_name,
                response=response,
                raw_output=raw_output,
                started_at=started_at,
                started_perf=started_perf,
                error=error,
            )
            return ExtractionResult(
                output=None,
                raw_output=raw_output,
                errors=(error,),
                metadata={"response": response_payload(response)},
            )

        _trace_extraction_step(
            context,
            request,
            step_name=step_name,
            response=response,
            raw_output=raw_output,
            final_output=final_output,
            started_at=started_at,
            started_perf=started_perf,
        )
        return ExtractionResult(
            output=final_output,
            raw_output=raw_output,
            reasoning=reasoning_view,
            metadata={
                "request": request_payload(request),
                "response": response_payload(response),
            },
        )

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


def _request_generation_options(
    options: Mapping[str, Any]
) -> tuple[float | None, dict[str, Any]]:
    value = options.get("temperature")
    temperature = float(value) if isinstance(value, (int, float)) else None
    request_options: dict[str, Any] = {}
    for key in ("top_p", "max_tokens", "extra_body"):
        if key in options:
            request_options[key] = options[key]
    top_k = options.get("top_k")
    if isinstance(top_k, int):
        request_options["extra_body"] = {
            **dict(request_options.get("extra_body") or {}),
            "top_k": top_k,
        }
    return temperature, request_options


def _trace_extraction_step(
    context: PipelineContext,
    request: ChatRequest,
    *,
    step_name: str,
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
        step_name,
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
