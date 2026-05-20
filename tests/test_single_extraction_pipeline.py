from types import SimpleNamespace

from gensie.baseline import (
    BasicAgent,
    EnrichedDeepInlineReasoningAgent,
    EnrichedInlineReasoningAgent,
    EnrichedInlineReasoningRagAgent,
    EnrichedSchemaAgent,
    EnrichedInlineReasoningSuperFspAgent,
    InlineReasoningAgent,
    MixedExtractorsJudgeSelfConsistencyAgent,
    MixedExtractorsVerdictJudgeRagSelfConsistencyAgent,
    MixedExtractorsVerdictJudgeRagSlotsSelfConsistencyAgent,
    MixedExtractorsVerdictJudgeSelfConsistencyAgent,
    OfficialParticipant,
    VerbatimEntitiesEnrichedInlineReasoningAgent,
)
from gensie.phases import build_verbatim_entity_response_format
from gensie.pipeline import (
    ComposablePipelineAgent,
    ExtractionSpec,
    PipelineSpec,
    ReasoningMode,
    SchemaPromptMode,
)
from gensie.runtime import ChatResponse, OpenAIChatClient
from gensie.sampling import SingleExtractionRunner
from gensie.prompts.system import STRICT_ANCHORING_RULE
from gensie.task import Task


class FakeChatClient:
    def __init__(self, content: str):
        self.content = content
        self.requests = []

    def complete(self, request):
        self.requests.append(request)
        return ChatResponse(
            content=self.content,
            usage={"prompt_tokens": 11, "completion_tokens": 7},
        )


class QueueChatClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def complete(self, request):
        self.requests.append(request)
        content, usage = self.responses.pop(0)
        return ChatResponse(content=content, usage=usage)


def _task() -> Task:
    return Task(
        id="sample",
        input_text="Ada Lovelace published notes about the Analytical Engine in 1843.",
        instruction="Extract the person, year, and labels.",
        target_schema={
            "$defs": {
                "Mention": {
                    "additionalProperties": False,
                    "properties": {
                        "text": {"type": "string"},
                        "label": {"type": "string"},
                    },
                    "required": ["text", "label"],
                    "type": "object",
                }
            },
            "additionalProperties": False,
            "description": "Extracts historical computing facts.",
            "properties": {
                "person": {"description": "Person name", "type": "string"},
                "year": {
                    "anyOf": [{"type": "integer"}, {"type": "null"}],
                    "default": None,
                    "description": "Year",
                },
                "mentions": {"items": {"$ref": "#/$defs/Mention"}, "type": "array"},
            },
            "required": ["person"],
            "type": "object",
        },
    )


def test_basic_agent_uses_original_schema_and_tracks_usage():
    fake = FakeChatClient(
        '{"person":"Ada Lovelace","year":1843,'
        '"mentions":[{"text":"Ada Lovelace","label":"PERSON"}]}'
    )
    agent = BasicAgent(chat_client=fake)

    output = agent.run(_task(), model="demo-model")

    assert output == {
        "person": "Ada Lovelace",
        "year": 1843,
        "mentions": [{"text": "Ada Lovelace", "label": "PERSON"}],
    }
    request = fake.requests[0]
    assert request.model == "demo-model"
    generation_schema = request.response_format["json_schema"]["schema"]
    assert generation_schema == _task().target_schema
    assert STRICT_ANCHORING_RULE not in request.messages[0].content
    assert STRICT_ANCHORING_RULE not in request.messages[1].content
    assert agent.usage.snapshot() == {
        "input_tokens": 11,
        "output_tokens": 7,
        "total_tokens": 18,
        "calls": 1,
    }


def test_single_extraction_runner_unwraps_top_level_reasoning_output():
    fake = FakeChatClient(
        '{"person":{"reasoning":"Named directly.","value":"Ada Lovelace"},'
        '"year":{"reasoning":"The text states 1843.","value":1843},'
        '"mentions":{"reasoning":"The person is mentioned.","value":[{"text":"Ada Lovelace","label":"PERSON"}]}}'
    )
    spec = PipelineSpec(
        name="reasoned",
        description="reasoned",
        extraction=ExtractionSpec(
            name="reasoned",
            reasoning=ReasoningMode.TOP_LEVEL,
            schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
        ),
    )
    agent = ComposablePipelineAgent(spec, SingleExtractionRunner(fake))

    output = agent.run(_task(), model="demo")

    assert output["person"] == "Ada Lovelace"
    request = fake.requests[0]
    generation_schema = request.response_format["json_schema"]["schema"]
    assert "reasoning" in generation_schema["properties"]["person"]["properties"]
    assert "FORMATO DE RAZONAMIENTO:" in request.messages[1].content
    assert "Eres un extractor de información estructurada" in request.messages[1].content
    assert STRICT_ANCHORING_RULE in request.messages[0].content
    assert STRICT_ANCHORING_RULE in request.messages[1].content


def test_inline_agent_uses_reference_spanish_prompt_and_don_quijote_fsp():
    fake = FakeChatClient(
        '{"person":{"reasoning":"Named directly.","value":"Ada Lovelace"},'
        '"year":{"reasoning":"The text states 1843.","value":1843},'
        '"mentions":{"reasoning":"The person is mentioned.","value":[{"text":"Ada Lovelace","label":"PERSON"}]}}'
    )
    agent = InlineReasoningAgent(chat_client=fake)

    agent.run(_task(), model="demo")

    prompt = fake.requests[0].messages[1].content
    assert prompt.startswith("EJEMPLO:")
    assert "Don Quijote de la Mancha" in prompt
    assert "SCHEMA DEL EJEMPLO:" in prompt
    assert "TAREA:" in prompt
    assert "Extrae información estructurada del TEXTO FUENTE en español." in prompt
    assert STRICT_ANCHORING_RULE in fake.requests[0].messages[0].content
    assert STRICT_ANCHORING_RULE in prompt
    assert "Extract structured information from the SOURCE TEXT" not in prompt


def test_enriched_agent_uses_reference_pydantic_prompt_and_don_quijote_fsp():
    fake = FakeChatClient(
        '{"person":{"reasoning":"Named directly.","value":"Ada Lovelace"},'
        '"year":{"reasoning":"The text states 1843.","value":1843},'
        '"mentions":{"reasoning":"The person is mentioned.","value":[{"text":"Ada Lovelace","label":"PERSON"}]}}'
    )
    agent = EnrichedInlineReasoningAgent(chat_client=fake)

    agent.run(_task(), model="demo")

    prompt = fake.requests[0].messages[1].content
    assert prompt.startswith("TAREA:")
    assert "SCHEMA PYDANTIC DEL EJEMPLO:" in prompt
    assert "Don Quijote de la Mancha" in prompt
    assert "literary_impact_evidence" in prompt
    assert "Reasoned[T] significa" in prompt
    assert STRICT_ANCHORING_RULE in fake.requests[0].messages[0].content
    assert STRICT_ANCHORING_RULE in prompt
    assert "Extract structured information from the SOURCE TEXT" not in prompt


def test_enriched_rag_agent_uses_registered_rag_fsp_pipeline():
    fake = FakeChatClient(
        '{"person":{"reasoning":"Named directly.","value":"Ada Lovelace"},'
        '"year":{"reasoning":"The text states 1843.","value":1843},'
        '"mentions":{"reasoning":"The person is mentioned.","value":[{"text":"Ada Lovelace","label":"PERSON"}]}}'
    )
    agent = EnrichedInlineReasoningRagAgent(chat_client=fake)

    output = agent.run(_task(), model="demo")

    request = fake.requests[0]
    prompt = request.messages[1].content
    assert output["person"] == "Ada Lovelace"
    assert request.metadata["pipeline"] == "enriched-inline-reasoning-rag"
    assert request.metadata["extraction"] == "enriched-inline-reasoning-rag"
    assert request.metadata["reasoning"] == "top_level"
    assert "EJEMPLOS FEW-SHOT:" in prompt
    assert "Ejemplo 1: cultural_literature_quijote" in prompt
    assert "SCHEMA PYDANTIC DEL EJEMPLO:" in prompt
    assert "Don Quijote de la Mancha" in prompt
    assert "literary_impact_evidence" not in prompt
    assert "SCHEMA PYDANTIC:" in prompt
    assert STRICT_ANCHORING_RULE in request.messages[0].content
    assert STRICT_ANCHORING_RULE in prompt


def test_enriched_schema_agent_uses_plain_pydantic_prompt_without_reasoning_or_fsp():
    fake = FakeChatClient(
        '{"person":"Ada Lovelace","year":1843,'
        '"mentions":[{"text":"Ada Lovelace","label":"PERSON"}]}'
    )
    agent = EnrichedSchemaAgent(chat_client=fake)

    output = agent.run(_task(), model="demo")

    assert output["person"] == "Ada Lovelace"
    request = fake.requests[0]
    prompt = request.messages[1].content
    assert request.metadata["prompt_style"] == "enriched-schema"
    assert request.response_format["json_schema"]["schema"] == _task().target_schema
    assert "SCHEMA PYDANTIC:" in prompt
    assert "Nullable[T] = T | null" in prompt
    assert "class Output(BaseModel):" in prompt
    assert "year: Nullable[int]" in prompt
    assert "from __future__ import annotations" not in prompt
    assert "from typing import Any, List, Optional, Literal" not in prompt
    assert "from pydantic import BaseModel, Field" not in prompt
    assert "No incluyas campos `reasoning`, `value`" in prompt
    assert "Reasoned[" not in prompt
    assert "class Reasoned" not in prompt
    assert "SCHEMA PYDANTIC DEL EJEMPLO:" not in prompt
    assert "Don Quijote de la Mancha" not in prompt
    assert STRICT_ANCHORING_RULE not in request.messages[0].content
    assert STRICT_ANCHORING_RULE not in prompt


def test_verbatim_entities_enriched_agent_runs_phase_and_injects_entities():
    fake = QueueChatClient(
        [
            (
                '{"personas":["Ada Lovelace"],'
                '"organizaciones":[],'
                '"fechas":["1843"],'
                '"lugares":[],'
                '"otros":["Analytical Engine"]}',
                {"prompt_tokens": 5, "completion_tokens": 3},
            ),
            (
                '{"person":{"reasoning":"Entity list and source text name Ada.","value":"Ada Lovelace"},'
                '"year":{"reasoning":"The source text states 1843.","value":1843},'
                '"mentions":{"reasoning":"The person is mentioned.","value":[{"text":"Ada Lovelace","label":"PERSON"}]}}',
                {"prompt_tokens": 11, "completion_tokens": 7},
            ),
        ]
    )
    agent = VerbatimEntitiesEnrichedInlineReasoningAgent(chat_client=fake)

    output = agent.run(_task(), model="demo")

    assert output["person"] == "Ada Lovelace"
    assert len(fake.requests) == 2
    phase_request, extraction_request = fake.requests
    assert phase_request.temperature == 0.0
    assert phase_request.response_format == build_verbatim_entity_response_format()
    assert "Extrae entidades verbatim" in phase_request.messages[1].content
    prompt = extraction_request.messages[1].content
    assert "ENTIDADES PREEXTRAIDAS:" in prompt
    assert '"Ada Lovelace"' in prompt
    assert '"1843"' in prompt
    assert '"Analytical Engine"' in prompt
    assert STRICT_ANCHORING_RULE in extraction_request.messages[0].content
    assert STRICT_ANCHORING_RULE in prompt
    assert agent.usage.snapshot() == {
        "input_tokens": 16,
        "output_tokens": 10,
        "total_tokens": 26,
        "calls": 2,
    }


def test_deep_agent_unwraps_recursive_reasoning_output():
    fake = FakeChatClient(
        '{"person":{"reasoning":"Named directly.","value":"Ada Lovelace"},'
        '"year":{"reasoning":"The text states 1843.","value":1843},'
        '"mentions":{"reasoning":"The person is mentioned.","value":['
        '{"reasoning":"Person item.","value":{'
        '"text":{"reasoning":"Exact span.","value":"Ada Lovelace"},'
        '"label":{"reasoning":"It is a person.","value":"PERSON"}}}]}}'
    )
    agent = EnrichedDeepInlineReasoningAgent(chat_client=fake)

    output = agent.run(_task(), model="demo")

    assert output == {
        "person": "Ada Lovelace",
        "year": 1843,
        "mentions": [{"text": "Ada Lovelace", "label": "PERSON"}],
    }
    generation_schema = fake.requests[0].response_format["json_schema"]["schema"]
    mention_def = generation_schema["$defs"]["Mention"]
    assert "reasoning" in mention_def["properties"]["text"]["properties"]
    assert "text: Reasoned[str]" in fake.requests[0].messages[1].content
    assert STRICT_ANCHORING_RULE in fake.requests[0].messages[0].content
    assert STRICT_ANCHORING_RULE in fake.requests[0].messages[1].content


def test_super_fsp_agent_includes_static_super_example():
    fake = FakeChatClient(
        '{"person":{"reasoning":"Named directly.","value":"Ada Lovelace"},'
        '"year":{"reasoning":"The text states 1843.","value":1843},'
        '"mentions":{"reasoning":"The person is mentioned.","value":[{"text":"Ada Lovelace","label":"PERSON"}]}}'
    )
    agent = EnrichedInlineReasoningSuperFspAgent(chat_client=fake)

    output = agent.run(_task(), model="demo")

    assert output["person"] == "Ada Lovelace"
    prompt = fake.requests[0].messages[1].content
    assert "EJEMPLO:" in prompt
    assert "INSTRUCCIÓN DEL EJEMPLO:" in prompt
    assert "Atlas-IE" in prompt
    assert "Atlas-IE presenta avances en extracción de información" in prompt
    assert "Lucía Ferrer" in prompt
    assert "Andrés Núñez" in prompt
    assert "pilot_outcome: Reasoned[PilotOutcome]" in prompt
    assert "entities: Reasoned[List[Entity]]" in prompt
    assert "registry_code: Reasoned[Nullable[str]]" in prompt
    assert "Don Quijote de la Mancha" not in prompt
    assert "SCHEMA PYDANTIC:" in prompt
    assert STRICT_ANCHORING_RULE in fake.requests[0].messages[0].content
    assert STRICT_ANCHORING_RULE in prompt


def test_official_participant_exposes_default_specs_and_fallback_agent():
    participant = OfficialParticipant(chat_client=FakeChatClient('{"person":"Ada"}'))

    names = [pipeline.name for pipeline in participant.get_info().pipelines]

    assert names == [
        "baseline",
        "inline-reasoning",
        "enriched-inline-reasoning",
        "enriched-inline-reasoning-rag",
        "enriched-schema",
        "verbatim-entities-enriched-inline-reasoning",
        "enriched-inline-reasoning-deep",
        "enriched-inline-reasoning-super-fsp",
        "enriched-inline-reasoning-self-consistency",
        "enriched-inline-reasoning-super-fsp-self-consistency",
        "enriched-inline-reasoning-self-consistency-judge",
        "enriched-inline-reasoning-self-consistency-verdict-judge",
        "mixed-extractors-self-consistency-judge",
        "mixed-extractors-self-consistency-verdict-judge",
        "mixed-extractors-self-consistency-verdict-judge-rag",
        "mixed-extractors-self-consistency-verdict-judge-rag-slots",
    ]
    assert participant.get_agent("missing") is participant.get_agent("baseline")
    assert (
        MixedExtractorsJudgeSelfConsistencyAgent.pipeline_name
        == "mixed-extractors-self-consistency-judge"
    )
    assert (
        MixedExtractorsVerdictJudgeSelfConsistencyAgent.pipeline_name
        == "mixed-extractors-self-consistency-verdict-judge"
    )
    assert (
        MixedExtractorsVerdictJudgeRagSelfConsistencyAgent.pipeline_name
        == "mixed-extractors-self-consistency-verdict-judge-rag"
    )
    assert (
        MixedExtractorsVerdictJudgeRagSlotsSelfConsistencyAgent.pipeline_name
        == "mixed-extractors-self-consistency-verdict-judge-rag-slots"
    )


def test_openai_chat_client_maps_request_to_chat_completion():
    captured = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content='{"answer":"ok"}')
                    )
                ],
                usage={"prompt_tokens": 1, "completion_tokens": 2},
            )

    raw_client = SimpleNamespace(
        chat=SimpleNamespace(completions=FakeCompletions())
    )
    client = OpenAIChatClient(client=raw_client)

    from gensie.runtime import ChatMessage, ChatRequest

    response = client.complete(
        ChatRequest(
            model="demo",
            messages=(ChatMessage(role="user", content="hello"),),
            response_format={"type": "json_object"},
            temperature=0.0,
        )
    )

    assert response.content == '{"answer":"ok"}'
    assert response.usage == {"prompt_tokens": 1, "completion_tokens": 2}
    assert captured == {
        "model": "demo",
        "messages": [{"role": "user", "content": "hello"}],
        "response_format": {"type": "json_object"},
        "temperature": 0.0,
    }
