import pytest

from gensie.aggregation.verdict_schema import (
    VERDICT_EVIDENCE_MAX_LENGTH,
    VERDICT_EVIDENCE_MAX_LENGTH_SCHEMA_ENV,
    build_verdict_generation_schema,
    build_verdict_plan,
    build_verdict_response_format,
    reconstruct_verdict_output,
    reconstruct_verdict_output_with_report,
)
from gensie.aggregation import build_judge_scope
from gensie.aggregation.judge import JudgeAggregator
from gensie.aggregation.verdict_judge import VerdictJudgeAggregator
from gensie.baseline import (
    EnrichedInlineReasoningJudgeSelfConsistencyAgent,
    EnrichedInlineReasoningVerdictJudgeSelfConsistencyAgent,
)
from gensie.pipeline import (
    AggregationMode,
    AggregationResult,
    AggregationSpec,
    ExtractionResult,
    ExtractionSpec,
    PipelineContext,
    PipelineSpec,
    ReasoningMode,
    SamplingSpec,
    SchemaPromptMode,
    TrialRecord,
)
from gensie.runtime import ChatResponse
from gensie.sampling import PipelineExecutionRunner
from gensie.task import Task
from gensie.usage import UsageTracker


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


def _run_with_details(agent, task, *, model="demo"):
    agent.usage.reset()
    result = agent.runner.run(
        agent.spec,
        PipelineContext(task=task, model=model, usage=agent.usage),
    )
    assert isinstance(result, AggregationResult)
    return result


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


def test_judge_normalizes_unicode_in_final_output_stable_fields():
    task = _task()
    records = [
        _record(0, {"person": "Ada\\u00e9", "year": 1843, "symptoms": ["fatiga"]}),
        _record(1, {"person": "Ada\\u00e9", "year": 1843, "symptoms": ["cefalea"]}),
    ]
    fake = QueueChatClient(
        [
            '{"symptoms":{"reasoning":"items","value":["fatiga"]}}',
        ]
    )
    context = PipelineContext(task=task, model="demo", usage=UsageTracker())

    result = JudgeAggregator(fake).aggregate(records, context)

    assert result.output["person"] == "Adaé"
    assert result.output["symptoms"] == ["fatiga"]


def test_verdict_generation_schema_uses_candidate_arrays_without_literal_candidates():
    task = _task()
    records = [
        _record(0, {"person": "Ada Lovelace", "year": 1843, "symptoms": ["fatiga"]}),
        _record(1, {"person": "Ada Lovelace", "year": 1843, "symptoms": ["cefalea"]}),
        _record(
            2,
            {
                "person": "Ada Lovelace",
                "year": 1843,
                "symptoms": ["fatiga", "cefalea"],
            },
        ),
    ]
    scope = build_judge_scope(records, task.target_schema)
    plan = build_verdict_plan(task, records, scope)

    schema = build_verdict_generation_schema(task.target_schema, plan)

    assert list(schema["properties"]) == ["symptoms"]
    assert "fatiga" not in str(schema)
    assert "cefalea" not in str(schema)
    verdict_ref = schema["properties"]["symptoms"]["$ref"].rsplit("/", 1)[-1]
    verdict_schema = schema["$defs"][verdict_ref]
    assert verdict_schema["properties"]["candidates"]["type"] == "array"
    assert "value" not in verdict_schema["properties"]
    candidate_ref = (
        verdict_schema["properties"]["candidates"]["items"]["$ref"].rsplit("/", 1)[-1]
    )
    candidate_schema = schema["$defs"][candidate_ref]
    assert candidate_schema["properties"]["candidate_value"] == {"type": "string"}
    assert candidate_schema["properties"]["evidence"] == {"type": "string"}
    assert candidate_schema["properties"]["include"] == {"type": "boolean"}


def test_verdict_response_format_can_enable_evidence_max_length(monkeypatch):
    monkeypatch.setenv(VERDICT_EVIDENCE_MAX_LENGTH_SCHEMA_ENV, "1")
    task = _task()
    records = [
        _record(0, {"person": "Ada Lovelace", "year": 1843, "symptoms": ["fatiga"]}),
        _record(1, {"person": "Ada Lovelace", "year": 1843, "symptoms": ["cefalea"]}),
    ]
    scope = build_judge_scope(records, task.target_schema)
    plan = build_verdict_plan(task, records, scope)

    response_format = build_verdict_response_format(task, plan)
    schema = response_format["json_schema"]["schema"]
    verdict_ref = schema["properties"]["symptoms"]["$ref"].rsplit("/", 1)[-1]
    verdict_schema = schema["$defs"][verdict_ref]
    candidate_ref = (
        verdict_schema["properties"]["candidates"]["items"]["$ref"].rsplit("/", 1)[-1]
    )
    candidate_schema = schema["$defs"][candidate_ref]

    assert candidate_schema["properties"]["evidence"] == {
        "type": "string",
        "maxLength": VERDICT_EVIDENCE_MAX_LENGTH,
    }


def test_verdict_generation_schema_can_force_candidate_slots():
    task = _task()
    records = [
        _record(0, {"person": "Ada Lovelace", "year": 1843, "symptoms": ["fatiga"]}),
        _record(1, {"person": "Ada Lovelace", "year": 1843, "symptoms": ["cefalea"]}),
        _record(
            2,
            {
                "person": "Ada Lovelace",
                "year": 1843,
                "symptoms": ["fatiga", "cefalea"],
            },
        ),
    ]
    scope = build_judge_scope(records, task.target_schema)
    plan = build_verdict_plan(task, records, scope)

    schema = build_verdict_generation_schema(
        task.target_schema,
        plan,
        candidate_layout="slots",
    )

    verdict_ref = schema["properties"]["symptoms"]["$ref"].rsplit("/", 1)[-1]
    assert len(verdict_ref) == 1
    verdict_schema = schema["$defs"][verdict_ref]
    candidates_schema = verdict_schema["properties"]["candidates"]
    assert candidates_schema["type"] == "object"
    assert candidates_schema["additionalProperties"] is False
    assert list(candidates_schema["properties"]) == ["1", "2"]
    assert candidates_schema["required"] == ["1", "2"]
    candidate_ref = candidates_schema["properties"]["1"]["$ref"].rsplit("/", 1)[-1]
    assert len(candidate_ref) == 1
    assert schema["$defs"][candidate_ref]["properties"]["candidate_value"] == {
        "type": "string"
    }


def test_verdict_plan_merges_normalized_duplicate_string_candidates():
    task = _task()
    records = [
        _record(0, {"person": "Ada Lovelace", "year": 1843, "symptoms": ["Fatiga"]}),
        _record(
            1,
            {
                "person": "Ada Lovelace",
                "year": 1843,
                "symptoms": ["Fatiga", "fatíga"],
            },
        ),
        _record(2, {"person": "Ada Lovelace", "year": 1843, "symptoms": ["fatiga"]}),
        _record(3, {"person": "Ada Lovelace", "year": 1843, "symptoms": ["cefalea"]}),
    ]
    scope = build_judge_scope(records, task.target_schema)
    plan = build_verdict_plan(task, records, scope)

    symptoms = next(field for field in plan.fields if field.name == "symptoms")

    assert [(candidate.value, candidate.count) for candidate in symptoms.candidates] == [
        ("Fatiga", 4),
        ("cefalea", 1),
    ]
    assert symptoms.candidates[0].trial_indices == (1, 2, 3)


def test_verdict_plan_normalizes_literal_unicode_escape_representatives():
    task = _task()
    records = [
        _record(
            0,
            {"person": "Ada Lovelace", "year": 1843, "symptoms": ["F\\u00e1tiga"]},
        ),
        _record(
            1,
            {"person": "Ada Lovelace", "year": 1843, "symptoms": ["F\\u00e1tiga"]},
        ),
        _record(2, {"person": "Ada Lovelace", "year": 1843, "symptoms": ["Fatiga"]}),
        _record(3, {"person": "Ada Lovelace", "year": 1843, "symptoms": ["cefalea"]}),
    ]
    scope = build_judge_scope(records, task.target_schema)
    plan = build_verdict_plan(task, records, scope)

    symptoms = next(field for field in plan.fields if field.name == "symptoms")

    assert symptoms.candidates[0].value == "Fátiga"
    assert symptoms.candidates[0].count == 3


def test_verdict_reconstruction_validates_candidate_order_and_values():
    task = _task()
    records = [
        _record(0, {"person": "Ada Lovelace", "year": 1843, "symptoms": ["fatiga"]}),
        _record(1, {"person": "Ada Lovelace", "year": 1843, "symptoms": ["cefalea"]}),
        _record(
            2,
            {
                "person": "Ada Lovelace",
                "year": 1843,
                "symptoms": ["fatiga", "cefalea"],
            },
        ),
    ]
    scope = build_judge_scope(records, task.target_schema)
    plan = build_verdict_plan(task, records, scope)

    output = reconstruct_verdict_output(
        plan,
        scope,
        {
            "symptoms": {
                "field": "síntomas mencionados",
                "candidates": [
                    {
                        "candidate_value": "fatiga",
                        "evidence": "Fragmento: \"fatiga y cefalea\". Fatiga aparece en el texto.",
                        "include": True,
                    },
                    {
                        "candidate_value": "cefalea",
                        "evidence": "Fragmento: \"fatiga y cefalea\". Cefalea aparece en el texto.",
                        "include": True,
                    },
                ],
            }
        },
    )

    assert output == {
        "person": "Ada Lovelace",
        "year": 1843,
        "symptoms": ["fatiga", "cefalea"],
    }
    with pytest.raises(ValueError, match="candidate value mismatch"):
        reconstruct_verdict_output(
            plan,
            scope,
            {
                "symptoms": {
                    "field": "síntomas mencionados",
                    "candidates": [
                        {
                            "candidate_value": "cefalea",
                            "evidence": "wrong order",
                            "include": True,
                        },
                        {
                            "candidate_value": "fatiga",
                            "evidence": "wrong order",
                            "include": True,
                        },
                    ],
                }
            },
        )


def test_verdict_reconstruction_accepts_candidate_slots():
    task = _task()
    records = [
        _record(0, {"person": "Ada Lovelace", "year": 1843, "symptoms": ["fatiga"]}),
        _record(1, {"person": "Ada Lovelace", "year": 1843, "symptoms": ["cefalea"]}),
        _record(
            2,
            {
                "person": "Ada Lovelace",
                "year": 1843,
                "symptoms": ["fatiga", "cefalea"],
            },
        ),
    ]
    scope = build_judge_scope(records, task.target_schema)
    plan = build_verdict_plan(task, records, scope)

    output = reconstruct_verdict_output(
        plan,
        scope,
        {
            "symptoms": {
                "field": "síntomas mencionados",
                "candidates": {
                    "1": {
                        "candidate_value": "fatiga",
                        "evidence": "Fatiga aparece en el texto.",
                        "include": True,
                    },
                    "2": {
                        "candidate_value": "cefalea",
                        "evidence": "Cefalea aparece en el texto.",
                        "include": True,
                    },
                },
            }
        },
        candidate_layout="slots",
    )

    assert output == {
        "person": "Ada Lovelace",
        "year": 1843,
        "symptoms": ["fatiga", "cefalea"],
    }


def test_verdict_reconstruction_slots_uses_expected_values_when_unicode_is_corrupted():
    task = _task()
    spanish = "Espa\u00f1ol"
    realismo = "Realismo literario espa\u00f1ol"
    destino = "Destino tr\u00e1gico"
    records = [
        _record(0, {"person": spanish, "year": 1843, "symptoms": [realismo, destino]}),
        _record(1, {"person": spanish, "year": 1843, "symptoms": [realismo]}),
        _record(2, {"person": "Catalan", "year": 1843, "symptoms": []}),
    ]
    scope = build_judge_scope(records, task.target_schema)
    plan = build_verdict_plan(task, records, scope)

    reconstruction = reconstruct_verdict_output_with_report(
        plan,
        scope,
        {
            "person": {
                "field": "persona",
                "candidates": {
                    "1": {
                        "candidate_value": "Espa" + "\x1f" + "ol",
                        "evidence": "bad escape from provider",
                    },
                    "2": {
                        "candidate_value": "Catalan",
                        "evidence": "alternate candidate",
                    },
                },
                "value": "Espa" + "\x1f" + "ol",
            },
            "symptoms": {
                "field": "items",
                "candidates": {
                    "1": {
                        "candidate_value": "Realismo literario espa" + "\x1f" + "ol",
                        "evidence": "bad escape from provider",
                        "include": True,
                    },
                    "2": {
                        "candidate_value": "Destino tr" + "\x1f" + "ico",
                        "evidence": "bad escape from provider",
                        "include": True,
                    },
                },
            },
        },
        enforce_validation=False,
        report_validation=True,
        fallback_output=records[0].result.output,
        candidate_layout="slots",
    )

    assert reconstruction.output == {
        "person": spanish,
        "year": 1843,
        "symptoms": [realismo, destino],
    }
    assert "\x1f" not in str(reconstruction.output)
    assert {
        issue["code"] for issue in reconstruction.validation_issues
    } >= {"candidate_value_mismatch", "value_not_expected_candidate"}


def test_verdict_reconstruction_can_report_without_enforcing_validation():
    task = _task()
    records = [
        _record(0, {"person": "Ada Lovelace", "year": 1843, "symptoms": ["fatiga"]}),
        _record(1, {"person": "Ada Lovelace", "year": 1843, "symptoms": ["cefalea"]}),
        _record(
            2,
            {
                "person": "Ada Lovelace",
                "year": 1843,
                "symptoms": ["fatiga", "cefalea"],
            },
        ),
    ]
    scope = build_judge_scope(records, task.target_schema)
    plan = build_verdict_plan(task, records, scope)

    reconstruction = reconstruct_verdict_output_with_report(
        plan,
        scope,
        {
            "symptoms": {
                "field": "symptoms mentioned",
                "candidates": [
                    {
                        "candidate_value": "cefalea",
                        "evidence": "reordered but valid candidate",
                        "include": True,
                    },
                    {
                        "candidate_value": "fatiga",
                        "evidence": "reordered but valid candidate",
                        "include": True,
                    },
                ],
            }
        },
        enforce_validation=False,
        report_validation=True,
        fallback_output=records[0].result.output,
    )

    assert reconstruction.output == {
        "person": "Ada Lovelace",
        "year": 1843,
        "symptoms": ["fatiga", "cefalea"],
    }
    assert [issue["code"] for issue in reconstruction.validation_issues] == [
        "candidate_value_mismatch",
        "candidate_value_mismatch",
    ]


def test_verdict_judge_pipeline_reconstructs_from_candidate_verdicts(monkeypatch):
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
            '{"symptoms":{"field":"El campo pide síntomas mencionados.",'
            '"candidates":['
            '{"candidate_value":"fatiga","evidence":"Fragmento: \\"fatiga y cefalea\\". Fatiga aparece explícitamente.","include":true},'
            '{"candidate_value":"cefalea","evidence":"Fragmento: \\"fatiga y cefalea\\". Cefalea aparece explícitamente.","include":true}'
            ']}}',
        ]
    )
    agent = EnrichedInlineReasoningVerdictJudgeSelfConsistencyAgent(chat_client=fake)

    output = agent.run(_task(), model="demo")

    assert output == {
        "person": "Ada Lovelace",
        "year": 1843,
        "symptoms": ["fatiga", "cefalea"],
    }
    judge_request = fake.requests[-1]
    assert judge_request.metadata["aggregation"] == "self_consistency_verdict_judge"
    assert judge_request.metadata["include_evidence_max_length"] is False
    judge_schema_text = str(judge_request.response_format["json_schema"]["schema"])
    assert "fatiga" not in judge_schema_text
    assert "cefalea" not in judge_schema_text
    assert "maxLength" not in judge_schema_text
    prompt = judge_request.messages[1].content
    assert "class SingleCandidate[T]" in prompt
    assert "class ArrayCandidate[T]" in prompt
    assert "publication_year: SingleVerdict[Nullable[int]]" in prompt
    assert "key_themes: ArrayVerdict[str]" in prompt
    assert "literary_impact_evidence: SingleVerdict[str]" in prompt
    assert "Valores candidatos, en este orden:" in prompt or "Elementos candidatos, en este orden:" in prompt
    assert f"máximo {VERDICT_EVIDENCE_MAX_LENGTH} caracteres" in prompt
    assert "no uses secuencias escapadas \\uXXXX" in judge_request.messages[0].content
    assert '1. (2/3): "fatiga"' in prompt
    assert '2. (2/3): "cefalea"' in prompt


def test_verdict_judge_pipeline_can_use_rag_fsp(monkeypatch):
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
            '{"symptoms":{"field":"El campo pide síntomas mencionados.",'
            '"candidates":['
            '{"candidate_value":"fatiga","evidence":"Fragmento: \\"fatiga y cefalea\\". Fatiga aparece explícitamente.","include":true},'
            '{"candidate_value":"cefalea","evidence":"Fragmento: \\"fatiga y cefalea\\". Cefalea aparece explícitamente.","include":true}'
            ']}}',
        ]
    )
    spec = PipelineSpec(
        name="rag-verdict-judge-test",
        description="Test candidate-verdict judge with RAG FSP.",
        extraction=ExtractionSpec(
            name="enriched-inline-reasoning",
            reasoning=ReasoningMode.TOP_LEVEL,
            schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
        ),
        sampling=SamplingSpec(total_trials=3),
        aggregation=AggregationSpec(
            mode=AggregationMode.JUDGE,
            options={"variant": "candidate_verdicts", "judge_fsp": "rag"},
        ),
    )
    context = PipelineContext(task=_task(), model="demo", usage=UsageTracker())

    result = PipelineExecutionRunner(fake).run(spec, context)

    assert isinstance(result, AggregationResult)
    assert result.output == {
        "person": "Ada Lovelace",
        "year": 1843,
        "symptoms": ["fatiga", "cefalea"],
    }
    judge_request = fake.requests[-1]
    assert judge_request.metadata["judge_fsp_provider"] == "RagVerdictJudgeFspProvider"
    prompt = judge_request.messages[1].content
    assert "Caso RAG: cultural_literature_quijote" in prompt
    assert '"candidate_value": "Don Quijote de la Mancha"' in prompt
    assert "genres: ArrayVerdict[str]" in prompt
    assert "literary_impact_evidence" not in prompt
    assert '1. (2/3): "fatiga"' in prompt
    assert '2. (2/3): "cefalea"' in prompt


def test_verdict_judge_pipeline_can_use_candidate_slots(monkeypatch):
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
            '{"symptoms":{"field":"El campo pide síntomas mencionados.",'
            '"candidates":{'
            '"1":{"candidate_value":"fatiga","evidence":"Fatiga aparece.","include":true},'
            '"2":{"candidate_value":"cefalea","evidence":"Cefalea aparece.","include":true}'
            '}}}',
        ]
    )
    spec = PipelineSpec(
        name="slots-verdict-judge-test",
        description="Test candidate-verdict judge with fixed candidate slots.",
        extraction=ExtractionSpec(
            name="enriched-inline-reasoning",
            reasoning=ReasoningMode.TOP_LEVEL,
            schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
        ),
        sampling=SamplingSpec(total_trials=3),
        aggregation=AggregationSpec(
            mode=AggregationMode.JUDGE,
            options={"variant": "candidate_verdicts", "candidate_layout": "slots"},
        ),
    )
    context = PipelineContext(task=_task(), model="demo", usage=UsageTracker())

    result = PipelineExecutionRunner(fake).run(spec, context)

    assert isinstance(result, AggregationResult)
    assert result.output == {
        "person": "Ada Lovelace",
        "year": 1843,
        "symptoms": ["fatiga", "cefalea"],
    }
    judge_request = fake.requests[-1]
    assert judge_request.metadata["candidate_layout"] == "slots"
    prompt = judge_request.messages[1].content
    assert 'claves requeridas "1", "2", ...' in prompt
    assert "candidates: dict[str, ArrayCandidate[T]]" in prompt
    schema_text = str(judge_request.response_format["json_schema"]["schema"])
    assert "'required': ['1', '2']" in schema_text


def test_verdict_judge_normalizes_unicode_in_final_output_stable_fields():
    task = _task()
    records = [
        _record(0, {"person": "Ada\\u00e9", "year": 1843, "symptoms": ["fatiga"]}),
        _record(1, {"person": "Ada\\u00e9", "year": 1843, "symptoms": ["cefalea"]}),
    ]
    fake = QueueChatClient(
        [
            '{"symptoms":{"field":"El campo pide síntomas mencionados.",'
            '"candidates":['
            '{"candidate_value":"fatiga","evidence":"Fatiga aparece.","include":true},'
            '{"candidate_value":"cefalea","evidence":"Cefalea aparece.","include":true}'
            ']}}',
        ]
    )
    context = PipelineContext(task=task, model="demo", usage=UsageTracker())

    result = VerdictJudgeAggregator(fake).aggregate(records, context)

    assert result.output["person"] == "Adaé"
    assert result.output["symptoms"] == ["fatiga", "cefalea"]


def test_verdict_judge_reports_validation_issues_without_fallback(monkeypatch):
    monkeypatch.setenv("GENSIE_SC_TRIALS", "3")
    monkeypatch.delenv("GENSIE_SC_VERDICT_JUDGE_ENFORCE_VALIDATION", raising=False)
    monkeypatch.delenv("GENSIE_SC_VERDICT_JUDGE_REPORT_VALIDATION", raising=False)
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
            '{"symptoms":{"field":"symptoms mentioned",'
            '"candidates":['
            '{"candidate_value":"cefalea","evidence":"reordered","include":true},'
            '{"candidate_value":"fatiga","evidence":"reordered","include":true}'
            ']}}',
        ]
    )
    agent = EnrichedInlineReasoningVerdictJudgeSelfConsistencyAgent(chat_client=fake)

    result = _run_with_details(agent, _task())

    assert result.output == {
        "person": "Ada Lovelace",
        "year": 1843,
        "symptoms": ["fatiga", "cefalea"],
    }
    assert result.metadata["fallback_used"] is False
    assert result.metadata["validation_enforced"] is False
    assert result.metadata["validation_reported"] is True
    assert result.metadata["validation_issue_count"] == 2
    assert {
        issue["code"] for issue in result.metadata["validation_issues"]
    } == {"candidate_value_mismatch"}


def test_verdict_judge_can_enforce_validation_and_fallback(monkeypatch):
    monkeypatch.setenv("GENSIE_SC_TRIALS", "3")
    monkeypatch.setenv("GENSIE_SC_VERDICT_JUDGE_ENFORCE_VALIDATION", "1")
    monkeypatch.setenv("GENSIE_SC_VERDICT_JUDGE_REPORT_VALIDATION", "1")
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
            '{"symptoms":{"field":"symptoms mentioned",'
            '"candidates":['
            '{"candidate_value":"cefalea","evidence":"reordered","include":true},'
            '{"candidate_value":"fatiga","evidence":"reordered","include":true}'
            ']}}',
        ]
    )
    agent = EnrichedInlineReasoningVerdictJudgeSelfConsistencyAgent(chat_client=fake)

    result = _run_with_details(agent, _task())

    assert result.output == {
        "person": "Ada Lovelace",
        "year": 1843,
        "symptoms": ["fatiga"],
    }
    assert result.metadata["fallback_used"] is True
    assert result.metadata["fallback_reason"] == "judge_failed"
    assert result.metadata["validation_enforced"] is True
    assert result.metadata["validation_issue_count"] == 1
    assert result.metadata["validation_issues"][0]["code"] == "candidate_value_mismatch"
