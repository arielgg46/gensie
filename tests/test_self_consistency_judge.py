from types import SimpleNamespace

from gensie.baseline import (
    EnrichedInlineReasoningJudgeSelfConsistencyAgent,
    OfficialParticipant,
)
from gensie.self_consistency_judge import build_judge_vote_summary
from gensie.task import Task


def _task() -> Task:
    return Task(
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


def test_judge_vote_summary_groups_scalars_and_array_items():
    task = _task()
    trials = [
        {
            "trial_index": 0,
            "inline_reasoning_output": {
                "person": {"reasoning": "Ada appears.", "value": "Ada Lovelace"},
                "year": {"reasoning": "1843 appears.", "value": 1843},
                "symptoms": {"reasoning": "Only fatigue.", "value": ["fatiga"]},
            },
            "final_candidate": {
                "person": "Ada Lovelace",
                "year": 1843,
                "symptoms": ["fatiga"],
            },
        },
        {
            "trial_index": 1,
            "inline_reasoning_output": {
                "person": {"reasoning": "Ada named.", "value": "Ada Lovelace"},
                "year": {"reasoning": "Wrong year.", "value": 1842},
                "symptoms": {"reasoning": "Both symptoms.", "value": ["fatiga", "cefalea"]},
            },
            "final_candidate": {
                "person": "Ada Lovelace",
                "year": 1842,
                "symptoms": ["fatiga", "cefalea"],
            },
        },
        {
            "trial_index": 2,
            "inline_reasoning_output": {
                "person": {"reasoning": "Ada named again.", "value": "Ada Lovelace"},
                "year": {"reasoning": "1843 appears again.", "value": 1843},
                "symptoms": {"reasoning": "Only headache.", "value": ["cefalea"]},
            },
            "final_candidate": {
                "person": "Ada Lovelace",
                "year": 1843,
                "symptoms": ["cefalea"],
            },
        },
    ]

    summary = build_judge_vote_summary(
        task,
        trials,
        include_scalar_reasonings=True,
        include_array_reasonings=False,
    )

    year_values = summary["fields"]["year"]["distinct_values"]
    symptoms = summary["fields"]["symptoms"]

    assert year_values[0]["value"] == 1843
    assert year_values[0]["count"] == 2
    assert len(year_values[0]["reasonings"]) == 2
    assert symptoms["kind"] == "array_items"
    assert "distinct_values" not in symptoms
    assert symptoms["distinct_items"] == [
        {"value": "fatiga", "count": 2, "trial_indices": [1, 2]},
        {"value": "cefalea", "count": 2, "trial_indices": [2, 3]},
    ]
    assert "trial_reasonings" not in symptoms


def test_judge_self_consistency_agent_calls_judge_after_trials(monkeypatch):
    task = _task()
    contents = [
        (
            '{"person":{"reasoning":"name","value":"Ada Lovelace"},'
            '"year":{"reasoning":"year","value":1843},'
            '"symptoms":{"reasoning":"items","value":["fatiga"]}}'
        ),
        (
            '{"person":{"reasoning":"name","value":"Ada Lovelace"},'
            '"year":{"reasoning":"wrong year","value":1842},'
            '"symptoms":{"reasoning":"items","value":["cefalea"]}}'
        ),
        (
            '{"person":{"reasoning":"name","value":"Ada Lovelace"},'
            '"year":{"reasoning":"year","value":1843},'
            '"symptoms":{"reasoning":"items","value":["fatiga","cefalea"]}}'
        ),
        (
            '{"person":{"reasoning":"El juez conserva el valor unanime.","value":"Ada Lovelace"},'
            '"year":{"reasoning":"1843 tiene soporte 2 y aparece en el texto.","value":1843},'
            '"symptoms":{"reasoning":"Ambos elementos aparecen en los intentos y el texto.","value":["fatiga","cefalea"]}}'
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
    monkeypatch.setenv("GENSIE_SC_JUDGE_INCLUDE_SCALAR_REASONINGS", "0")
    monkeypatch.setenv("GENSIE_SC_JUDGE_INCLUDE_ARRAY_REASONINGS", "1")
    trace_calls = []
    monkeypatch.setattr(
        "gensie.baseline.trace_step",
        lambda *args, **kwargs: trace_calls.append((args, kwargs)),
    )
    agent = EnrichedInlineReasoningJudgeSelfConsistencyAgent()
    agent.client = FakeClient()

    result = agent.run(task, "dummy-model")

    assert len(calls) == 4
    assert result == {
        "person": "Ada Lovelace",
        "year": 1843,
        "symptoms": ["fatiga", "cefalea"],
    }
    assert calls[0]["response_format"]["json_schema"]["name"].endswith("_trial")
    assert calls[-1]["response_format"]["json_schema"]["name"] == (
        "enriched_inline_reasoning_self_consistency_judge"
    )
    judge_prompt = calls[-1]["messages"][1]["content"]
    assert "Trials válidos: 3" in judge_prompt
    assert "CAMPO `symptoms` (lista)" in judge_prompt
    assert "- 2/3: \"fatiga\"" in judge_prompt
    assert "(T1" not in judge_prompt
    assert "Razones de trials para este campo:" in judge_prompt
    assert '"distinct_items"' not in judge_prompt
    assert '"array_reasonings_included"' not in judge_prompt
    assert "Ada appears" not in judge_prompt
    assert [args[1] for args, _ in trace_calls] == [
        "self_consistency_trial_01",
        "self_consistency_trial_02",
        "self_consistency_trial_03",
        "self_consistency_judge",
    ]
    assert trace_calls[-1][1]["metrics"]["request"]["is_model_request"] is True
    assert trace_calls[-1][1]["metrics"]["request"]["role"] == "judge"


def test_judge_self_consistency_agent_skips_judge_for_single_valid_trial(monkeypatch):
    task = _task()
    contents = [
        (
            '{"person":{"reasoning":"name","value":"Ada Lovelace"},'
            '"year":{"reasoning":"year","value":1843},'
            '"symptoms":{"reasoning":"items","value":["fatiga"]}}'
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
    monkeypatch.setenv("GENSIE_SC_TRIALS", "1")
    trace_calls = []
    monkeypatch.setattr(
        "gensie.baseline.trace_step",
        lambda *args, **kwargs: trace_calls.append((args, kwargs)),
    )
    agent = EnrichedInlineReasoningJudgeSelfConsistencyAgent()
    agent.client = FakeClient()

    result = agent.run(task, "dummy-model")

    assert len(calls) == 1
    assert result == {
        "person": "Ada Lovelace",
        "year": 1843,
        "symptoms": ["fatiga"],
    }
    assert [args[1] for args, _ in trace_calls] == [
        "self_consistency_trial_01",
        "self_consistency_judge_fallback",
    ]
    fallback_trace = trace_calls[-1][1]
    assert fallback_trace["metrics"]["request"]["is_model_request"] is False
    assert fallback_trace["metrics"]["request"]["role"] == (
        "single_valid_trial_fallback"
    )
    assert fallback_trace["response_payload"]["fallback_reason"] == (
        "single_valid_trial"
    )


def test_judge_self_consistency_agent_falls_back_to_valid_trial_on_judge_error(
    monkeypatch,
):
    task = _task()
    contents = [
        (
            '{"person":{"reasoning":"name","value":"Ada Lovelace"},'
            '"year":{"reasoning":"year","value":1843},'
            '"symptoms":{"reasoning":"items","value":["fatiga"]}}'
        ),
        (
            '{"person":{"reasoning":"name","value":"Ada Lovelace"},'
            '"year":{"reasoning":"wrong year","value":1842},'
            '"symptoms":{"reasoning":"items","value":["cefalea"]}}'
        ),
    ]
    calls = []

    class FakeCompletions:
        def create(self, **kwargs):
            calls.append(kwargs)
            if len(calls) > len(contents):
                raise RuntimeError("judge unavailable")
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
    monkeypatch.setenv("GENSIE_SC_TRIALS", "2")
    trace_calls = []
    monkeypatch.setattr(
        "gensie.baseline.trace_step",
        lambda *args, **kwargs: trace_calls.append((args, kwargs)),
    )
    agent = EnrichedInlineReasoningJudgeSelfConsistencyAgent()
    agent.client = FakeClient()

    result = agent.run(task, "dummy-model")

    assert len(calls) == 3
    assert result == {
        "person": "Ada Lovelace",
        "year": 1843,
        "symptoms": ["fatiga"],
    }
    assert [args[1] for args, _ in trace_calls] == [
        "self_consistency_trial_01",
        "self_consistency_trial_02",
        "self_consistency_judge",
    ]
    judge_trace = trace_calls[-1][1]
    assert "judge unavailable" in judge_trace["error"]
    assert judge_trace["response_payload"]["fallback_used"] is True
    assert judge_trace["response_payload"]["fallback_reason"] == "judge_failed"
    assert judge_trace["response_payload"]["final_output"] == result


def test_official_participant_registers_judge_self_consistency():
    names = [p.name for p in OfficialParticipant().get_info().pipelines]

    assert "enriched-inline-reasoning-self-consistency-judge" in names
