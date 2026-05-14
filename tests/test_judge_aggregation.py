from gensie.aggregation import build_judge_scope
from gensie.baseline import EnrichedInlineReasoningJudgeSelfConsistencyAgent
from gensie.pipeline import ExtractionResult, ExtractionSpec, ReasoningMode, TrialRecord
from gensie.runtime import ChatResponse
from gensie.task import Task


class QueueChatClient:
    def __init__(self, contents, *, fail_after=None):
        self.contents = list(contents)
        self.fail_after = fail_after
        self.requests = []

    def complete(self, request):
        self.requests.append(request)
        if self.fail_after is not None and len(self.requests) > self.fail_after:
            raise RuntimeError("judge unavailable")
        return ChatResponse(
            content=self.contents.pop(0),
            usage={"prompt_tokens": 10, "completion_tokens": 5},
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


def _record(index, output):
    return TrialRecord(
        index=index,
        group_name="enriched",
        extraction=ExtractionSpec(name="enriched", reasoning=ReasoningMode.TOP_LEVEL),
        result=ExtractionResult(output=output),
    )


def test_judge_scope_treats_arrays_with_same_items_as_stable():
    task = _task()
    records = [
        _record(0, {"person": "Ada", "year": 1843, "symptoms": ["fatiga", "cefalea"]}),
        _record(1, {"person": "Ada", "year": 1843, "symptoms": ["cefalea", "fatiga"]}),
    ]

    scope = build_judge_scope(records, task.target_schema)

    assert scope.disputed_fields == ()
    assert scope.stable_fields["symptoms"] == ["fatiga", "cefalea"]


def test_judge_only_receives_disputed_fields_and_merges_stable_fields(monkeypatch):
    monkeypatch.setenv("GENSIE_SC_TRIALS", "3")
    monkeypatch.setenv("GENSIE_SC_JUDGE_INCLUDE_ARRAY_REASONINGS", "1")
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
            '{"symptoms":{"reasoning":"Ambos elementos tienen soporte y aparecen en el texto.",'
            '"value":["fatiga","cefalea"]}}',
        ]
    )
    agent = EnrichedInlineReasoningJudgeSelfConsistencyAgent(chat_client=fake)

    output = agent.run(_task(), model="demo")

    assert len(fake.requests) == 4
    assert output == {
        "person": "Ada Lovelace",
        "year": 1843,
        "symptoms": ["fatiga", "cefalea"],
    }
    judge_request = fake.requests[-1]
    judge_schema = judge_request.response_format["json_schema"]["schema"]
    assert list(judge_schema["properties"]) == ["symptoms"]
    judge_prompt = judge_request.messages[1].content
    assert "INSTRUCCIÓN ORIGINAL:" in judge_prompt
    assert "INSTRUCCIÓN DEL JUEZ:" in judge_prompt
    assert "Don Quijote de la Mancha" in judge_prompt
    assert "CAMPO `title`" in judge_prompt
    assert "Candidato `Don Quijote de la Mancha` (3/4)" in judge_prompt
    assert "Candidato null (2/4)" in judge_prompt
    assert "Candidato de frase completa (2/4)" in judge_prompt
    assert "SALIDA:" in judge_prompt
    assert "SALIDA ESPERADA DEL JUEZ SOLO PARA CAMPOS DISPUTADOS:" not in judge_prompt
    assert "CAMPOS YA CONSENSUADOS:" not in judge_prompt
    assert "No devuelvas campos ya consensuados" not in judge_prompt
    assert "- author:" not in judge_prompt
    assert "CAMPO `symptoms` (lista)" in judge_prompt
    assert "Trials válidos: 3" in judge_prompt
    assert "[grupos:" not in judge_prompt
    assert "CAMPO `person`" not in judge_prompt
    assert "Ada Lovelace" in judge_prompt


def test_judge_can_include_stable_fields_when_enabled(monkeypatch):
    monkeypatch.setenv("GENSIE_SC_TRIALS", "3")
    monkeypatch.setenv("GENSIE_SC_JUDGE_INCLUDE_STABLE_FIELDS", "1")
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
            '{"symptoms":{"reasoning":"Ambos elementos tienen soporte y aparecen en el texto.",'
            '"value":["fatiga","cefalea"]}}',
        ]
    )
    agent = EnrichedInlineReasoningJudgeSelfConsistencyAgent(chat_client=fake)

    agent.run(_task(), model="demo")

    judge_prompt = fake.requests[-1].messages[1].content
    assert "CAMPOS YA CONSENSUADOS:" in judge_prompt
    assert "- person: \"Ada Lovelace\"" in judge_prompt
    assert "- year: 1843" in judge_prompt
    assert "- author: \"Miguel de Cervantes Saavedra\"" in judge_prompt
    assert "No devuelvas campos ya consensuados" in judge_prompt


def test_judge_can_hide_support_counts_when_disabled(monkeypatch):
    monkeypatch.setenv("GENSIE_SC_TRIALS", "3")
    monkeypatch.setenv("GENSIE_SC_JUDGE_INCLUDE_SUPPORT_COUNTS", "0")
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
            '{"symptoms":{"reasoning":"Ambos elementos tienen soporte y aparecen en el texto.",'
            '"value":["fatiga","cefalea"]}}',
        ]
    )
    agent = EnrichedInlineReasoningJudgeSelfConsistencyAgent(chat_client=fake)

    agent.run(_task(), model="demo")

    judge_prompt = fake.requests[-1].messages[1].content
    assert "Trials válidos:" not in judge_prompt
    assert "Candidato `Don Quijote de la Mancha`:" in judge_prompt
    assert "Candidato `Don Quijote de la Mancha` (3/4)" not in judge_prompt
    assert "2/3" not in judge_prompt
    assert "3/4" not in judge_prompt
    assert "- \"fatiga\"" in judge_prompt


def test_judge_falls_back_to_first_valid_trial_on_judge_error(monkeypatch):
    monkeypatch.setenv("GENSIE_SC_TRIALS", "2")
    fake = QueueChatClient(
        [
            '{"person":{"reasoning":"name","value":"Ada Lovelace"},'
            '"year":{"reasoning":"year","value":1843},'
            '"symptoms":{"reasoning":"items","value":["fatiga"]}}',
            '{"person":{"reasoning":"name","value":"Ada Lovelace"},'
            '"year":{"reasoning":"year","value":1843},'
            '"symptoms":{"reasoning":"items","value":["cefalea"]}}',
        ],
        fail_after=2,
    )
    agent = EnrichedInlineReasoningJudgeSelfConsistencyAgent(chat_client=fake)

    output = agent.run(_task(), model="demo")

    assert len(fake.requests) == 3
    assert output == {
        "person": "Ada Lovelace",
        "year": 1843,
        "symptoms": ["fatiga"],
    }
