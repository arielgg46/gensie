from __future__ import annotations

from gensie.agent import GenSIEAgent, Participant, ParticipantInfo
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
