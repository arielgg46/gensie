from gensie.baseline import (
    EnrichedInlineReasoningJudgeSelfConsistencyAgent,
    EnrichedInlineReasoningSelfConsistencyAgent,
    EnrichedInlineReasoningSuperFspSelfConsistencyAgent,
    OfficialParticipant,
)
from gensie.pipeline import (
    AggregationMode,
    AggregationSpec,
    ComposablePipelineAgent,
    ExtractionSpec,
    PipelineSpec,
    ReasoningMode,
    SamplingSpec,
    SchemaPromptMode,
    TrialGroupSpec,
)
from gensie.runtime import ChatResponse
from gensie.sampling import PipelineExecutionRunner
from gensie.task import Task


class QueueChatClient:
    def __init__(self, contents):
        self.contents = list(contents)
        self.requests = []

    def complete(self, request):
        self.requests.append(request)
        content = self.contents.pop(0)
        return ChatResponse(
            content=content,
            usage={"prompt_tokens": 10, "completion_tokens": 5},
            raw={"id": f"response-{len(self.requests)}"},
        )


def _task() -> Task:
    return Task(
        id="sample",
        input_text="Ada Lovelace publicó notas en 1843 y mencionó fatiga y cefalea.",
        instruction="Extrae persona, año y síntomas.",
        target_schema={
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "person": {"type": "string"},
                "year": {"type": "integer"},
                "symptoms": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["person", "year", "symptoms"],
        },
    )


def test_self_consistency_agent_runs_trials_and_aggregates(monkeypatch):
    monkeypatch.setenv("GENSIE_SC_TRIALS", "3")
    fake = QueueChatClient(
        [
            '{"person":{"reasoning":"name","value":"Ada Lovelace"},'
            '"year":{"reasoning":"year","value":1843},'
            '"symptoms":{"reasoning":"items","value":["fatiga"]}}',
            '{"person":{"reasoning":"name","value":"Ada Lovelace"},'
            '"year":{"reasoning":"year","value":1843},'
            '"symptoms":{"reasoning":"items","value":["cefalea"]}}',
            '{"person":{"reasoning":"name","value":"Ada Lovelace"},'
            '"year":{"reasoning":"year","value":1843},'
            '"symptoms":{"reasoning":"items","value":["fatiga","cefalea"]}}',
        ]
    )
    agent = EnrichedInlineReasoningSelfConsistencyAgent(chat_client=fake)

    output = agent.run(_task(), model="demo")

    assert len(fake.requests) == 3
    assert all(request.temperature == 0.5 for request in fake.requests)
    assert output["person"] == "Ada Lovelace"
    assert output["year"] == 1843
    assert set(output["symptoms"]) == {"fatiga", "cefalea"}


def test_super_fsp_self_consistency_uses_super_fsp_prompt(monkeypatch):
    monkeypatch.setenv("GENSIE_SC_TRIALS", "2")
    content = (
        '{"person":{"reasoning":"name","value":"Ada Lovelace"},'
        '"year":{"reasoning":"year","value":1843},'
        '"symptoms":{"reasoning":"items","value":[]}}'
    )
    fake = QueueChatClient([content, content])
    agent = EnrichedInlineReasoningSuperFspSelfConsistencyAgent(chat_client=fake)

    output = agent.run(_task(), model="demo")

    assert output["person"] == "Ada Lovelace"
    prompt = fake.requests[0].messages[1].content
    assert "Atlas-IE presenta avances" in prompt
    assert "Don Quijote de la Mancha" not in prompt


def test_official_participant_registers_self_consistency_pipelines():
    names = [pipeline.name for pipeline in OfficialParticipant().get_info().pipelines]

    assert "enriched-inline-reasoning-self-consistency" in names
    assert "enriched-inline-reasoning-super-fsp-self-consistency" in names
    assert "enriched-inline-reasoning-self-consistency-judge" in names
    assert "enriched-inline-reasoning-self-consistency-verdict-judge" in names
    assert "mixed-extractors-self-consistency-judge" in names
    assert "mixed-extractors-self-consistency-verdict-judge" in names
    assert "mixed-extractors-self-consistency-verdict-judge-rag" in names
    assert "mixed-extractors-self-consistency-verdict-judge-rag-slots" in names


def test_multi_trial_runner_supports_heterogeneous_trial_groups(monkeypatch):
    monkeypatch.setenv("GENSIE_SC_DYNAMIC_TRIALS", "0")
    fake = QueueChatClient(
        [
            '{"person":"Ada Lovelace","year":1843,"symptoms":["fatiga"]}',
            '{"person":{"reasoning":"name","value":"Ada Lovelace"},'
            '"year":{"reasoning":"year","value":1843},'
            '"symptoms":{"reasoning":"items","value":["fatiga"]}}',
            '{"person":{"reasoning":"name","value":"Ada Lovelace"},'
            '"year":{"reasoning":"year","value":1843},'
            '"symptoms":{"reasoning":"items","value":['
            '{"reasoning":"item","value":"fatiga"}]}}',
        ]
    )
    spec = PipelineSpec(
        name="mixed-sc",
        description="mixed",
        extraction=ExtractionSpec(name="baseline"),
        sampling=SamplingSpec(
            total_trials=3,
            interleave=False,
            groups=(
                TrialGroupSpec(
                    name="baseline",
                    extraction=ExtractionSpec(name="baseline"),
                    count=1,
                ),
                TrialGroupSpec(
                    name="enriched",
                    extraction=ExtractionSpec(
                        name="enriched-inline-reasoning",
                        reasoning=ReasoningMode.TOP_LEVEL,
                        schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
                    ),
                    count=1,
                ),
                TrialGroupSpec(
                    name="deep",
                    extraction=ExtractionSpec(
                        name="enriched-inline-reasoning-deep",
                        reasoning=ReasoningMode.DEEP,
                        schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
                    ),
                    count=1,
                ),
            ),
        ),
        aggregation=AggregationSpec(mode=AggregationMode.HEURISTIC_SELF_CONSISTENCY),
    )
    agent = ComposablePipelineAgent(spec, PipelineExecutionRunner(fake))

    output = agent.run(_task(), model="demo")

    assert output == {
        "person": "Ada Lovelace",
        "year": 1843,
        "symptoms": ["fatiga"],
    }
    assert [request.metadata["extraction"] for request in fake.requests] == [
        "baseline",
        "enriched-inline-reasoning",
        "enriched-inline-reasoning-deep",
    ]


def test_registered_mixed_extractors_judge_pipeline_runs_all_groups(monkeypatch):
    monkeypatch.setenv("GENSIE_SC_TRIALS", "3")
    monkeypatch.setenv("GENSIE_SC_DYNAMIC_TRIALS", "0")
    fake = QueueChatClient(
        [
            '{"person":"Ada Lovelace","year":1843,"symptoms":["fatiga"]}',
            '{"person":"Ada Lovelace","year":1843,"symptoms":["cefalea"]}',
            '{"person":{"reasoning":"name","value":"Ada Lovelace"},'
            '"year":{"reasoning":"year","value":1843},'
            '"symptoms":{"reasoning":"items","value":["fatiga","cefalea"]}}',
            '{"symptoms":{"reasoning":"fatiga y cefalea tienen soporte en el texto.",'
            '"value":["fatiga","cefalea"]}}',
        ]
    )
    agent = OfficialParticipant(chat_client=fake).get_agent(
        "mixed-extractors-self-consistency-judge"
    )

    output = agent.run(_task(), model="demo")

    assert output == {
        "person": "Ada Lovelace",
        "year": 1843,
        "symptoms": ["fatiga", "cefalea"],
    }
    assert [request.metadata.get("extraction") for request in fake.requests[:3]] == [
        "baseline",
        "enriched-schema",
        "enriched-inline-reasoning",
    ]
    assert fake.requests[-1].metadata["aggregation"] == "self_consistency_judge"


def test_registered_mixed_extractors_verdict_judge_pipeline_runs_all_groups(monkeypatch):
    monkeypatch.setenv("GENSIE_SC_TRIALS", "3")
    monkeypatch.setenv("GENSIE_SC_DYNAMIC_TRIALS", "0")
    fake = QueueChatClient(
        [
            '{"person":"Ada Lovelace","year":1843,"symptoms":["fatiga"]}',
            '{"person":"Ada Lovelace","year":1843,"symptoms":["cefalea"]}',
            '{"person":{"reasoning":"name","value":"Ada Lovelace"},'
            '"year":{"reasoning":"year","value":1843},'
            '"symptoms":{"reasoning":"items","value":["fatiga","cefalea"]}}',
            '{"symptoms":{"field":"El campo pide síntomas mencionados.",'
            '"candidates":['
            '{"candidate_value":"fatiga","evidence":"Fragmento: \\"fatiga y cefalea\\". Fatiga aparece explícitamente.","include":true},'
            '{"candidate_value":"cefalea","evidence":"Fragmento: \\"fatiga y cefalea\\". Cefalea aparece explícitamente.","include":true}'
            ']}}',
        ]
    )
    agent = OfficialParticipant(chat_client=fake).get_agent(
        "mixed-extractors-self-consistency-verdict-judge"
    )

    output = agent.run(_task(), model="demo")

    assert output == {
        "person": "Ada Lovelace",
        "year": 1843,
        "symptoms": ["fatiga", "cefalea"],
    }
    assert [request.metadata.get("extraction") for request in fake.requests[:3]] == [
        "baseline",
        "enriched-schema",
        "enriched-inline-reasoning",
    ]
    assert fake.requests[-1].metadata["aggregation"] == "self_consistency_verdict_judge"


def test_registered_mixed_extractors_verdict_judge_rag_pipeline_uses_rag_fsp(monkeypatch):
    monkeypatch.setenv("GENSIE_SC_TRIALS", "3")
    monkeypatch.setenv("GENSIE_SC_DYNAMIC_TRIALS", "0")
    fake = QueueChatClient(
        [
            '{"person":"Ada Lovelace","year":1843,"symptoms":["fatiga"]}',
            '{"person":"Ada Lovelace","year":1843,"symptoms":["cefalea"]}',
            '{"person":{"reasoning":"name","value":"Ada Lovelace"},'
            '"year":{"reasoning":"year","value":1843},'
            '"symptoms":{"reasoning":"items","value":["fatiga","cefalea"]}}',
            '{"symptoms":{"field":"El campo pide síntomas mencionados.",'
            '"candidates":['
            '{"candidate_value":"fatiga","evidence":"Fragmento: \\"fatiga y cefalea\\". Fatiga aparece explícitamente.","include":true},'
            '{"candidate_value":"cefalea","evidence":"Fragmento: \\"fatiga y cefalea\\". Cefalea aparece explícitamente.","include":true}'
            ']}}',
        ]
    )
    agent = OfficialParticipant(chat_client=fake).get_agent(
        "mixed-extractors-self-consistency-verdict-judge-rag"
    )

    output = agent.run(_task(), model="demo")

    assert output == {
        "person": "Ada Lovelace",
        "year": 1843,
        "symptoms": ["fatiga", "cefalea"],
    }
    assert [request.metadata.get("extraction") for request in fake.requests[:3]] == [
        "baseline",
        "enriched-schema",
        "enriched-inline-reasoning",
    ]
    judge_request = fake.requests[-1]
    assert judge_request.metadata["aggregation"] == "self_consistency_verdict_judge"
    assert judge_request.metadata["judge_fsp_provider"] == "RagVerdictJudgeFspProvider"
    assert "Caso RAG: cultural_literature_quijote" in judge_request.messages[1].content
    assert '"candidate_value": "Don Quijote de la Mancha"' in judge_request.messages[1].content


def test_registered_mixed_extractors_verdict_judge_rag_slots_pipeline(monkeypatch):
    monkeypatch.setenv("GENSIE_SC_TRIALS", "3")
    monkeypatch.setenv("GENSIE_SC_DYNAMIC_TRIALS", "0")
    fake = QueueChatClient(
        [
            '{"person":"Ada Lovelace","year":1843,"symptoms":["fatiga"]}',
            '{"person":"Ada Lovelace","year":1843,"symptoms":["cefalea"]}',
            '{"person":{"reasoning":"name","value":"Ada Lovelace"},'
            '"year":{"reasoning":"year","value":1843},'
            '"symptoms":{"reasoning":"items","value":["fatiga","cefalea"]}}',
            '{"symptoms":{"field":"El campo pide síntomas mencionados.",'
            '"candidates":{'
            '"1":{"candidate_value":"fatiga","evidence":"Fatiga aparece.","include":true},'
            '"2":{"candidate_value":"cefalea","evidence":"Cefalea aparece.","include":true}'
            '}}}',
        ]
    )
    agent = OfficialParticipant(chat_client=fake).get_agent(
        "mixed-extractors-self-consistency-verdict-judge-rag-slots"
    )

    output = agent.run(_task(), model="demo")

    assert output == {
        "person": "Ada Lovelace",
        "year": 1843,
        "symptoms": ["fatiga", "cefalea"],
    }
    judge_request = fake.requests[-1]
    assert judge_request.metadata["candidate_layout"] == "slots"
    assert judge_request.metadata["judge_fsp_provider"] == "RagVerdictJudgeFspProvider"
    assert 'claves requeridas "1", "2", ...' in judge_request.messages[1].content


def test_judge_self_consistency_agent_class_uses_registered_pipeline(monkeypatch):
    monkeypatch.setenv("GENSIE_SC_TRIALS", "1")
    fake = QueueChatClient(
        [
            '{"person":{"reasoning":"name","value":"Ada Lovelace"},'
            '"year":{"reasoning":"year","value":1843},'
            '"symptoms":{"reasoning":"items","value":["fatiga"]}}',
        ]
    )
    agent = EnrichedInlineReasoningJudgeSelfConsistencyAgent(chat_client=fake)

    output = agent.run(_task(), model="demo")

    assert output == {
        "person": "Ada Lovelace",
        "year": 1843,
        "symptoms": ["fatiga"],
    }
    assert len(fake.requests) == 1
