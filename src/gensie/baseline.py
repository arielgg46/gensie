from __future__ import annotations

import os
import threading
import time
from typing import Any

from openai import OpenAI

from gensie.agent import GenSIEAgent, Participant, ParticipantInfo, PipelineInfo
from gensie.parse_pipeline import ParsePipelineAgent
from gensie.pipeline import ComposablePipelineAgent
from gensie.pipeline.defaults import (
    build_default_registry,
    default_pipeline_specs,
)
from gensie.pipeline.registry import PipelineRegistry
from gensie.pipeline.specs import PipelineSpec
from gensie.runtime import ChatClient, OpenAIChatClient
from gensie.sampling import PipelineExecutionRunner
from dotenv import load_dotenv

load_dotenv()

DEFAULT_OPENAI_REQUEST_DELAY_S = 3.0
_OPENAI_REQUEST_LOCK = threading.Lock()
_OPENAI_LAST_REQUEST_STARTED_AT = 0.0


def _create_chat_completion(client: OpenAI, **kwargs: Any) -> Any:
    delay_s = _get_openai_request_delay_s()
    if delay_s > 0:
        global _OPENAI_LAST_REQUEST_STARTED_AT
        with _OPENAI_REQUEST_LOCK:
            now = time.monotonic()
            wait_s = (_OPENAI_LAST_REQUEST_STARTED_AT + delay_s) - now
            if wait_s > 0:
                time.sleep(wait_s)
            _OPENAI_LAST_REQUEST_STARTED_AT = time.monotonic()

    return client.chat.completions.create(**kwargs)


def _get_openai_request_delay_s() -> float:
    raw_value = os.getenv(
        "OPENAI_REQUEST_DELAY_S", str(DEFAULT_OPENAI_REQUEST_DELAY_S)
    )
    try:
        return max(float(raw_value), 0.0)
    except ValueError:
        return DEFAULT_OPENAI_REQUEST_DELAY_S


def _env_int(name: str, default: int, *, minimum: int = 0) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return max(int(raw_value), minimum)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _default_chat_client() -> ChatClient:
    return OpenAIChatClient()


def _runner(chat_client: ChatClient) -> PipelineExecutionRunner:
    return PipelineExecutionRunner(chat_client=chat_client)


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


class SelectiveInlineReasoningRagAgent(_DefaultPipelineAgent):
    pipeline_name = "selective-inline-reasoning-rag"


class EnrichedSchemaAgent(_DefaultPipelineAgent):
    pipeline_name = "enriched-schema"


class EnrichedSchemaRagAgent(_DefaultPipelineAgent):
    pipeline_name = "enriched-schema-rag"


class VerbatimEntitiesEnrichedInlineReasoningAgent(_DefaultPipelineAgent):
    pipeline_name = "verbatim-entities-enriched-inline-reasoning"


class EnrichedDeepInlineReasoningAgent(_DefaultPipelineAgent):
    pipeline_name = "enriched-inline-reasoning-deep"


class EnrichedInlineReasoningSuperFspAgent(_DefaultPipelineAgent):
    pipeline_name = "enriched-inline-reasoning-super-fsp"


class EnrichedInlineReasoningSelfConsistencyAgent(_DefaultPipelineAgent):
    pipeline_name = "enriched-inline-reasoning-self-consistency"


class MixedExtractorsRagSelfConsistencyAgent(_DefaultPipelineAgent):
    pipeline_name = "mixed-extractors-self-consistency-rag"


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


SUBMITTED_PIPELINES = (
    "enriched-schema-rag",
    "enriched-inline-reasoning-rag",
    "mixed-extractors-self-consistency-rag",
)

class OfficialParticipant(Participant):
    def __init__(self, chat_client: ChatClient | None = None):
        default_registry = build_default_registry()
        self.registry = PipelineRegistry()
        for name in SUBMITTED_PIPELINES:
            self.registry.register(default_registry.get(name))

        client = chat_client or _default_chat_client()
        runner = _runner(client)
        self.pipelines: dict[str, GenSIEAgent] = {
            spec.name: ComposablePipelineAgent(spec, runner) for spec in self.registry
        }

    def get_info(self) -> ParticipantInfo:
        return ParticipantInfo(
            team_name="DRILLER",
            institution="Universidad de La Habana",
            pipelines=self.registry.pipeline_infos(),
        )

    def get_agent(self, pipeline_name: str) -> GenSIEAgent:
        try:
            return self.pipelines[pipeline_name]
        except KeyError as exc:
            raise KeyError(f"unknown submitted pipeline: {pipeline_name}") from exc
