from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from gensie.pipeline.context import PipelineContext
from gensie.pipeline.records import AggregationResult
from gensie.pipeline.specs import PipelineSpec
from gensie.prompts import ReferenceExtractionPromptBuilder
from gensie.prompts.base import PromptBuilder
from gensie.runtime import ChatClient, ChatRequest, build_json_schema_response_format
from gensie.schemas.reasoning import unwrap_reasoning_output


@dataclass(frozen=True)
class SingleExtractionRunner:
    chat_client: ChatClient
    prompt_builder: PromptBuilder = field(default_factory=ReferenceExtractionPromptBuilder)

    def run(
        self, spec: PipelineSpec, context: PipelineContext
    ) -> dict[str, Any] | AggregationResult:
        extraction = spec.extraction
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


def _temperature(spec: PipelineSpec) -> float | None:
    value = spec.extraction.options.get("temperature")
    if isinstance(value, (int, float)):
        return float(value)
    return None
