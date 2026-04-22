import os
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict
from openai import OpenAI
from gensie.agent import GenSIEAgent, Participant, ParticipantInfo, PipelineInfo
from gensie.task import Task
from gensie.tracing import trace_step
from dotenv import load_dotenv

load_dotenv()


def _default_chat_client() -> ChatClient:
    return OpenAIChatClient()


    def run(self, task: Task, model: str) -> Dict[str, Any]:
        """
        Executes the extraction using OpenAI's response_format for strict schema compliance.
        """
        prompt = task.get_input_prompt()
        messages = [
            {
                "role": "system",
                "content": "You are a precise data extraction agent.",
            },
            {"role": "user", "content": prompt},
        ]
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "extraction",
                "schema": task.target_schema,
                "strict": True,
            },
        }
        request_payload = {
            "model": model,
            "messages": messages,
            "response_format": response_format,
        }

        started_at = datetime.now(timezone.utc)
        started_perf = time.perf_counter()

        try:
            # Call OpenAI with the task's JSON schema
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                response_format=response_format,
            )
            completed_at = datetime.now(timezone.utc)
            duration_ms = (time.perf_counter() - started_perf) * 1000
            raw_response = (
                response.model_dump()
                if hasattr(response, "model_dump")
                else {"raw": str(response)}
            )
            usage = raw_response.get("usage") or {}
            trace_step(
                task,
                "extract",
                prompt=prompt,
                request_payload=request_payload,
                response_payload=raw_response,
                metrics={
                    "tokens": {
                        "prompt_tokens": usage.get("prompt_tokens"),
                        "completion_tokens": usage.get("completion_tokens"),
                        "total_tokens": usage.get("total_tokens"),
                    },
                    "timings": {
                        "started_at": started_at.isoformat(),
                        "completed_at": completed_at.isoformat(),
                        "total_duration_ms": round(duration_ms, 3),
                        "time_to_first_token_ms": None,
                        "time_to_first_token_note": "Not captured by the current non-streaming baseline.",
                    },
                },
            )
        except Exception as e:
            completed_at = datetime.now(timezone.utc)
            duration_ms = (time.perf_counter() - started_perf) * 1000
            trace_step(
                task,
                "extract",
                prompt=prompt,
                request_payload=request_payload,
                error=str(e),
                metrics={
                    "tokens": {
                        "prompt_tokens": None,
                        "completion_tokens": None,
                        "total_tokens": None,
                    },
                    "timings": {
                        "started_at": started_at.isoformat(),
                        "completed_at": completed_at.isoformat(),
                        "total_duration_ms": round(duration_ms, 3),
                        "time_to_first_token_ms": None,
                        "time_to_first_token_note": "Not captured by the current non-streaming baseline.",
                    },
                },
            )
            raise

def _spec(name: str) -> PipelineSpec:
    for spec in default_pipeline_specs():
        if spec.name == name:
            return spec
    raise KeyError(f"unknown default pipeline: {name}")


class _DefaultPipelineAgent(ComposablePipelineAgent):
    pipeline_name: str

    def __init__(self, chat_client: ChatClient | None = None):
        client = chat_client or _default_chat_client()
        super().__init__(_spec(self.pipeline_name), _runner(client))


class BasicAgent(_DefaultPipelineAgent):
    pipeline_name = "baseline"


class InlineReasoningAgent(_DefaultPipelineAgent):
    pipeline_name = "inline-reasoning"


class EnrichedInlineReasoningAgent(_DefaultPipelineAgent):
    pipeline_name = "enriched-inline-reasoning"


class EnrichedInlineReasoningRagAgent(_DefaultPipelineAgent):
    pipeline_name = "enriched-inline-reasoning-rag"


class EnrichedSchemaAgent(_DefaultPipelineAgent):
    pipeline_name = "enriched-schema"


class VerbatimEntitiesEnrichedInlineReasoningAgent(_DefaultPipelineAgent):
    pipeline_name = "verbatim-entities-enriched-inline-reasoning"


class EnrichedDeepInlineReasoningAgent(_DefaultPipelineAgent):
    pipeline_name = "enriched-inline-reasoning-deep"


class EnrichedInlineReasoningSuperFspAgent(_DefaultPipelineAgent):
    pipeline_name = "enriched-inline-reasoning-super-fsp"


class EnrichedInlineReasoningSelfConsistencyAgent(_DefaultPipelineAgent):
    pipeline_name = "enriched-inline-reasoning-self-consistency"


class EnrichedInlineReasoningSuperFspSelfConsistencyAgent(_DefaultPipelineAgent):
    pipeline_name = "enriched-inline-reasoning-super-fsp-self-consistency"


class EnrichedInlineReasoningJudgeSelfConsistencyAgent(_DefaultPipelineAgent):
    pipeline_name = "enriched-inline-reasoning-self-consistency-judge"


class EnrichedInlineReasoningVerdictJudgeSelfConsistencyAgent(_DefaultPipelineAgent):
    pipeline_name = "enriched-inline-reasoning-self-consistency-verdict-judge"


class MixedExtractorsJudgeSelfConsistencyAgent(_DefaultPipelineAgent):
    pipeline_name = "mixed-extractors-self-consistency-judge"


class MixedExtractorsVerdictJudgeSelfConsistencyAgent(_DefaultPipelineAgent):
    pipeline_name = "mixed-extractors-self-consistency-verdict-judge"


class MixedExtractorsVerdictJudgeRagSelfConsistencyAgent(_DefaultPipelineAgent):
    pipeline_name = "mixed-extractors-self-consistency-verdict-judge-rag"


class MixedExtractorsVerdictJudgeRagSlotsSelfConsistencyAgent(_DefaultPipelineAgent):
    pipeline_name = "mixed-extractors-self-consistency-verdict-judge-rag-slots"


class OfficialParticipant(Participant):
    def __init__(self, chat_client: ChatClient | None = None):
        self.registry: PipelineRegistry = build_default_registry()
        client = chat_client or _default_chat_client()
        runner = _runner(client)
        self.pipelines: dict[str, GenSIEAgent] = {
            spec.name: ComposablePipelineAgent(spec, runner) for spec in self.registry
        }

    def get_info(self) -> ParticipantInfo:
        return ParticipantInfo(
            team_name="GenSIE Baseline Team",
            institution="Official",
            pipelines=self.registry.pipeline_infos(),
        )

    def get_agent(self, pipeline_name: str) -> GenSIEAgent:
        return self.pipelines.get(pipeline_name, self.pipelines["baseline"])
