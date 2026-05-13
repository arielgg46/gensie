from types import SimpleNamespace

from gensie.baseline import (
    EnrichedInlineReasoningSelfConsistencyAgent,
    EnrichedInlineReasoningSuperFspSelfConsistencyAgent,
    OfficialParticipant,
)
from gensie.self_consistency import (
    HeuristicIdentityFieldSelector,
    LexicalStringSimilarity,
    RecallBiasedMbrArrayCandidateSelector,
    SchemaAwareSelfConsistencyAggregator,
    SelfConsistencyConfig,
)
from gensie.task import Task


def _aggregator(**config_overrides):
    return SchemaAwareSelfConsistencyAggregator(
        config=SelfConsistencyConfig(**config_overrides),
        string_similarity=LexicalStringSimilarity(),
    )


def test_string_fields_use_cluster_medoid_not_exact_repetition():
    schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
        },
    }
    outputs = [
        {"summary": "dolor en el sitio de inyeccion"},
        {"summary": "dolor en sitio de inyeccion"},
        {"summary": "cefalea aislada"},
    ]

    result = _aggregator(scalar_string_threshold=0.65).aggregate(outputs, schema)

    assert "dolor" in result["summary"]
    assert "cefalea" not in result["summary"]


def test_array_of_strings_is_built_item_wise():
    schema = {
        "type": "object",
        "properties": {
            "symptoms": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
    }
    outputs = [
        {"symptoms": ["fatiga", "cefalea"]},
        {"symptoms": ["cefalea", "dolor en sitio de inyeccion"]},
        {"symptoms": ["fatiga", "dolor en el sitio de inyeccion"]},
    ]

    result = _aggregator(array_string_threshold=0.65).aggregate(outputs, schema)
    symptoms = result["symptoms"]

    assert len(symptoms) == 3
    assert any("fatiga" in item for item in symptoms)
    assert any("cefalea" in item for item in symptoms)
    assert any("dolor" in item for item in symptoms)
    assert symptoms not in [output["symptoms"] for output in outputs]


def test_array_of_objects_clusters_without_identity_field():
    schema = {
        "type": "object",
        "properties": {
            "side_effects": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "reaction": {"type": "string"},
                        "frequency": {
                            "type": "string",
                            "enum": ["COMMON", "RARE"],
                        },
                    },
                    "required": ["reaction", "frequency"],
                },
            },
        },
    }
    outputs = [
        {
            "side_effects": [
                {"reaction": "fatiga", "frequency": "COMMON"},
                {"reaction": "cefalea", "frequency": "COMMON"},
            ]
        },
        {
            "side_effects": [
                {"reaction": "fatiga leve", "frequency": "COMMON"},
                {"reaction": "dolor", "frequency": "RARE"},
            ]
        },
        {
            "side_effects": [
                {"reaction": "cefalea", "frequency": "COMMON"},
                {"reaction": "fatiga", "frequency": "COMMON"},
            ]
        },
    ]

    result = _aggregator(object_item_threshold=0.62).aggregate(outputs, schema)
    side_effects = result["side_effects"]
    reactions = [item["reaction"] for item in side_effects]

    assert len(side_effects) == 2
    assert any("fatiga" in reaction for reaction in reactions)
    assert any("cefalea" in reaction for reaction in reactions)
    assert not any(reaction == "dolor" for reaction in reactions)
    assert all(item["frequency"] == "COMMON" for item in side_effects)


def test_identity_field_selector_prefers_entity_text_and_reaction_fields():
    selector = HeuristicIdentityFieldSelector()
    config = SelfConsistencyConfig()
    entity_schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "label": {"type": "string", "enum": ["PERSON", "LOCATION"]},
        },
        "required": ["text", "label"],
    }
    side_effect_schema = {
        "type": "object",
        "properties": {
            "reaction": {"type": "string"},
            "system_organ_class": {"type": "string"},
            "probability": {"type": "string", "enum": ["HIGH", "LOW"]},
            "impact": {"type": "string"},
        },
        "required": ["reaction", "system_organ_class", "probability", "impact"],
    }

    entity_decision = selector.select(entity_schema, entity_schema, config=config)
    side_effect_decision = selector.select(
        side_effect_schema,
        side_effect_schema,
        config=config,
    )

    assert entity_decision.field_name == "text"
    assert side_effect_decision.field_name == "reaction"


def test_array_of_objects_uses_identity_field_before_aggregating_subfields():
    schema = {
        "type": "object",
        "properties": {
            "entities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "text": {"type": "string"},
                        "label": {
                            "type": "string",
                            "enum": ["LOCATION", "MISCELLANEOUS"],
                        },
                    },
                    "required": ["text", "label"],
                },
            },
        },
    }
    outputs = [
        {"entities": [{"text": "Nakatomi", "label": "LOCATION"}]},
        {"entities": [{"text": "Nakatomi", "label": "MISCELLANEOUS"}]},
        {"entities": [{"text": "Nakatomi", "label": "LOCATION"}]},
    ]

    aggregator = _aggregator()
    result, diagnostics = aggregator.aggregate_with_diagnostics(outputs, schema)

    assert result["entities"] == [{"text": "Nakatomi", "label": "LOCATION"}]
    field_diagnostics = diagnostics["fields"]["entities"]
    assert field_diagnostics["cluster_similarity"] == "identity_field"
    assert field_diagnostics["identity_field_decision"]["field_name"] == "text"


def test_recall_biased_array_selection_keeps_near_tie_longer_candidate():
    schema = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
    }
    outputs = (
        [{"items": ["A", "B"]} for _ in range(4)]
    )
    outputs = list(outputs) + [{"items": ["A", "B", "C"]} for _ in range(3)]

    result = _aggregator().aggregate(outputs, schema)

    assert result["items"] == ["A", "B", "C"]


def test_self_consistency_agent_runs_trials_and_aggregates(monkeypatch):
    task = Task(
        id="sample",
        input_text="Ada Lovelace publico notas en 1843 y menciono fatiga y cefalea.",
        instruction="Extrae persona, ano y sintomas.",
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

    contents = [
        (
            '{"person":{"reasoning":"name","value":"Ada Lovelace"},'
            '"year":{"reasoning":"year","value":1843},'
            '"symptoms":{"reasoning":"items","value":["fatiga"]}}'
        ),
        (
            '{"person":{"reasoning":"name","value":"Ada Lovelace"},'
            '"year":{"reasoning":"year","value":1843},'
            '"symptoms":{"reasoning":"items","value":["cefalea"]}}'
        ),
        (
            '{"person":{"reasoning":"name","value":"Ada Lovelace"},'
            '"year":{"reasoning":"year","value":1843},'
            '"symptoms":{"reasoning":"items","value":["fatiga","cefalea"]}}'
        ),
    ]
    calls = []

    class FakeCompletions:
        def create(self, **kwargs):
            calls.append(kwargs)
            message = SimpleNamespace(content=contents[len(calls) - 1])
            choice = SimpleNamespace(message=message)
            return SimpleNamespace(
                choices=[choice],
                model_dump=lambda: {
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 5,
                        "total_tokens": 15,
                    }
                },
            )

    class FakeClient:
        chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setenv("OPENAI_REQUEST_DELAY_S", "0")
    monkeypatch.setenv("GENSIE_SC_TRIALS", "3")
    trace_calls = []
    monkeypatch.setattr(
        "gensie.baseline.trace_step",
        lambda *args, **kwargs: trace_calls.append((args, kwargs)),
    )
    agent = EnrichedInlineReasoningSelfConsistencyAgent()
    agent.client = FakeClient()

    result = agent.run(task, "dummy-model")

    assert len(calls) == 3
    assert result["person"] == "Ada Lovelace"
    assert result["year"] == 1843
    assert set(result["symptoms"]) == {"fatiga", "cefalea"}
    assert all(call["temperature"] == 0.5 for call in calls)
    assert [args[1] for args, _ in trace_calls] == [
        "self_consistency_trial_01",
        "self_consistency_trial_02",
        "self_consistency_trial_03",
        "self_consistency_aggregate",
    ]
    assert trace_calls[0][1]["metrics"]["request"]["is_model_request"] is True
    assert trace_calls[-1][1]["metrics"]["request"]["is_model_request"] is False
    assert "aggregation_diagnostics" in trace_calls[-1][1]["response_payload"]


def test_self_consistency_agent_limits_trials_per_task_by_token_budget(monkeypatch):
    task = Task(
        id="sample",
        input_text="Ada Lovelace publico notas en 1843.",
        instruction="Extrae persona y ano.",
        target_schema={
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "person": {"type": "string"},
                "year": {"type": "integer"},
            },
            "required": ["person", "year"],
        },
    )
    content = (
        '{"person":{"reasoning":"name","value":"Ada Lovelace"},'
        '"year":{"reasoning":"year","value":1843}}'
    )
    calls = []

    class FakeCompletions:
        def create(self, **kwargs):
            calls.append(kwargs)
            message = SimpleNamespace(content=content)
            choice = SimpleNamespace(message=message)
            return SimpleNamespace(
                choices=[choice],
                model_dump=lambda: {
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 20,
                        "total_tokens": 30,
                    }
                },
            )

    class FakeClient:
        chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setenv("OPENAI_REQUEST_DELAY_S", "0")
    monkeypatch.setenv("GENSIE_SC_MAX_TRIALS", "5")
    monkeypatch.setenv("GENSIE_SC_TOKEN_BUDGET", "40")
    monkeypatch.setenv("GENSIE_SC_TOKEN_BUDGET_RATIO", "1")
    monkeypatch.setenv("GENSIE_SC_COMPLETION_TOKEN_SAFETY_FACTOR", "1")
    trace_calls = []
    monkeypatch.setattr(
        "gensie.baseline.trace_step",
        lambda *args, **kwargs: trace_calls.append((args, kwargs)),
    )
    agent = EnrichedInlineReasoningSelfConsistencyAgent()
    agent.client = FakeClient()

    result = agent.run(task, "dummy-model")

    assert len(calls) == 1
    assert result == {"person": "Ada Lovelace", "year": 1843}
    assert [args[1] for args, _ in trace_calls] == [
        "self_consistency_trial_01",
        "self_consistency_aggregate",
    ]


def test_self_consistency_default_cap_allows_budget_to_choose_more_than_three(monkeypatch):
    monkeypatch.delenv("GENSIE_SC_TRIALS", raising=False)
    monkeypatch.delenv("GENSIE_SC_MAX_TRIALS", raising=False)
    monkeypatch.setenv("OPENAI_REQUEST_DELAY_S", "0")

    agent = EnrichedInlineReasoningSelfConsistencyAgent()

    assert agent.trial_planner.config.max_trials == 12


def test_super_fsp_self_consistency_uses_super_fsp_prompt(monkeypatch):
    task = Task(
        id="sample",
        input_text="Ada Lovelace publico notas en 1843.",
        instruction="Extrae persona y ano.",
        target_schema={
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "person": {"type": "string"},
                "year": {"type": "integer"},
            },
            "required": ["person", "year"],
        },
    )
    content = (
        '{"person":{"reasoning":"name","value":"Ada Lovelace"},'
        '"year":{"reasoning":"year","value":1843}}'
    )
    calls = []

    class FakeCompletions:
        def create(self, **kwargs):
            calls.append(kwargs)
            message = SimpleNamespace(content=content)
            choice = SimpleNamespace(message=message)
            return SimpleNamespace(
                choices=[choice],
                model_dump=lambda: {
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 5,
                        "total_tokens": 15,
                    }
                },
            )

    class FakeClient:
        chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setenv("OPENAI_REQUEST_DELAY_S", "0")
    monkeypatch.setenv("GENSIE_SC_TRIALS", "2")
    monkeypatch.setattr("gensie.baseline.trace_step", lambda *args, **kwargs: None)
    agent = EnrichedInlineReasoningSuperFspSelfConsistencyAgent()
    agent.client = FakeClient()

    result = agent.run(task, "dummy-model")

    assert len(calls) == 2
    assert result == {"person": "Ada Lovelace", "year": 1843}
    prompt = calls[0]["messages"][1]["content"]
    assert "Atlas-IE presenta avances" in prompt
    assert "entities: Reasoned[List[Entity]]" in prompt
    assert "Don Quijote de la Mancha" not in prompt
    assert (
        calls[0]["response_format"]["json_schema"]["name"]
        == "enriched_inline_reasoning_super_fsp_self_consistency"
    )


def test_official_participant_registers_self_consistency():
    names = [p.name for p in OfficialParticipant().get_info().pipelines]

    assert "enriched-inline-reasoning-self-consistency" in names
    assert "enriched-inline-reasoning-super-fsp-self-consistency" in names
