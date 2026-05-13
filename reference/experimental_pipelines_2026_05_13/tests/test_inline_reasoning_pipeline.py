import copy
import json
from types import SimpleNamespace

from gensie.baseline import InlineReasoningAgent
import gensie.inline_reasoning as inline_reasoning
from gensie.inline_reasoning import (
    INCLUDE_INLINE_REASONING_FEW_SHOT,
    INLINE_PROMPT_SCHEMA_FINAL_VALUES,
    INLINE_PROMPT_SCHEMA_REASONING_WRAPPER,
    build_inline_reasoning_few_shot_example,
    build_inline_reasoning_prompt,
    build_inline_reasoning_prompt_schema,
    build_inline_reasoning_schema,
    unwrap_inline_reasoning_output,
)
from gensie.task import Task


def _sample_task() -> Task:
    return Task(
        id="sample",
        input_text="Ada Lovelace publico notas sobre la Maquina Analitica en 1843.",
        instruction="Extrae la persona, el ano y las etiquetas.",
        target_schema={
            "$defs": {
                "Tag": {
                    "enum": ["SCIENCE", "OTHER"],
                    "title": "Tag",
                    "type": "string",
                },
                "Mention": {
                    "additionalProperties": False,
                    "properties": {
                        "text": {"type": "string"},
                        "label": {"type": "string"},
                    },
                    "required": ["text", "label"],
                    "type": "object",
                },
            },
            "additionalProperties": False,
            "description": "Extracts historical computing facts.",
            "properties": {
                "person": {
                    "description": "Verbatim person name",
                    "title": "Person",
                    "type": "string",
                },
                "year": {
                    "anyOf": [{"type": "integer"}, {"type": "null"}],
                    "default": None,
                    "description": "Year mentioned in the text",
                    "title": "Year",
                },
                "tags": {
                    "items": {"$ref": "#/$defs/Tag"},
                    "type": "array",
                },
                "mentions": {
                    "items": {"$ref": "#/$defs/Mention"},
                    "type": "array",
                },
            },
            "required": ["person"],
            "title": "SampleSchema",
            "type": "object",
        },
    )


def test_build_inline_reasoning_schema_wraps_top_level_fields_only():
    task = _sample_task()
    original = copy.deepcopy(task.target_schema)

    reasoning_schema = build_inline_reasoning_schema(task.target_schema)

    assert task.target_schema == original
    assert reasoning_schema["required"] == ["person", "year", "tags", "mentions"]
    assert reasoning_schema["$defs"] == original["$defs"]

    person_wrapper = reasoning_schema["properties"]["person"]
    assert person_wrapper["required"] == ["reasoning", "value"]
    assert person_wrapper["additionalProperties"] is False
    assert person_wrapper["properties"]["reasoning"]["type"] == "string"
    assert person_wrapper["properties"]["value"] == original["properties"]["person"]

    mentions_value = reasoning_schema["properties"]["mentions"]["properties"]["value"]
    assert mentions_value == original["properties"]["mentions"]
    assert mentions_value["items"] == {"$ref": "#/$defs/Mention"}


def test_unwrap_inline_reasoning_output_returns_only_values():
    task = _sample_task()
    raw = {
        "person": {"reasoning": "Quoted evidence supports Ada.", "value": "Ada Lovelace"},
        "year": {"reasoning": "The text says 1843.", "value": 1843},
        "tags": {"reasoning": "Computing/science context.", "value": ["SCIENCE"]},
        "mentions": {
            "reasoning": "The person is mentioned directly.",
            "value": [{"text": "Ada Lovelace", "label": "PERSON"}],
        },
    }

    assert unwrap_inline_reasoning_output(raw, task.target_schema) == {
        "person": "Ada Lovelace",
        "year": 1843,
        "tags": ["SCIENCE"],
        "mentions": [{"text": "Ada Lovelace", "label": "PERSON"}],
    }


def test_build_inline_reasoning_prompt_schema_wraps_reasoning_for_prompt():
    task = _sample_task()

    prompt_schema = build_inline_reasoning_prompt_schema(task.target_schema)

    person_wrapper = prompt_schema["properties"]["person"]
    assert person_wrapper["description"] == "Verbatim person name"
    assert person_wrapper["properties"]["reasoning"] == {"type": "string"}
    assert "description" not in person_wrapper["properties"]["value"]
    assert person_wrapper["properties"]["value"]["type"] == "string"
    assert "additionalProperties" not in prompt_schema
    assert "required" not in prompt_schema
    assert "title" not in prompt_schema


def test_build_inline_reasoning_prompt_uses_wrapper_schema_by_default():
    prompt = build_inline_reasoning_prompt(_sample_task())

    assert "EJEMPLO FEW-SHOT:" in prompt
    assert "FORMATO DE RAZONAMIENTO:" in prompt
    assert "SCHEMA:" in prompt
    assert "TEXTO FUENTE:" in prompt
    schema_section = prompt.split("SCHEMA:", 1)[1]
    prompt_schema = json.loads(schema_section.split("TEXTO FUENTE:", 1)[0])
    assert '"reasoning"' in schema_section
    assert '"description": "Verbatim person name"' in schema_section
    assert prompt_schema["properties"]["person"]["properties"]["reasoning"] == {
        "type": "string"
    }
    assert "additionalProperties" not in schema_section
    assert '"required"' not in schema_section
    assert '"title"' not in schema_section


def test_build_inline_reasoning_few_shot_example_has_schema_and_reasoned_output():
    example = build_inline_reasoning_few_shot_example()

    assert INCLUDE_INLINE_REASONING_FEW_SHOT is True
    assert "INSTRUCCI" in example
    assert "Extrae los metadatos" in example
    assert "Complexity: L2" in example
    assert "INPUT TEXT DEL EJEMPLO:" in example
    assert "SCHEMA MODIFICADO DEL EJEMPLO:" in example
    assert "OUTPUT DEL EJEMPLO:" in example
    assert "Don Quijote de la Mancha" in example
    assert '"reasoning"' in example
    assert '"value": null' in example
    assert "no afirma" in example


def test_build_inline_reasoning_prompt_can_disable_few_shot(monkeypatch):
    monkeypatch.setattr(
        inline_reasoning,
        "INCLUDE_INLINE_REASONING_FEW_SHOT",
        False,
    )

    prompt = build_inline_reasoning_prompt(_sample_task())

    assert "EJEMPLO FEW-SHOT:" not in prompt
    assert prompt.startswith("TAREA:")


def test_build_inline_reasoning_prompt_can_use_final_value_schema(monkeypatch):
    monkeypatch.setattr(
        inline_reasoning,
        "INLINE_PROMPT_SCHEMA_VIEW",
        INLINE_PROMPT_SCHEMA_FINAL_VALUES,
    )

    prompt = build_inline_reasoning_prompt(_sample_task())

    schema_section = prompt.split("SCHEMA:", 1)[1]
    assert "reasoning" not in schema_section
    assert '"description": "Verbatim person name"' in schema_section


def test_inline_reasoning_agent_uses_wrapper_schema_and_returns_values(monkeypatch):
    task = _sample_task()
    captured = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            message = SimpleNamespace(
                content=(
                    '{"person":{"reasoning":"The text names Ada Lovelace.","value":"Ada Lovelace"},'
                    '"year":{"reasoning":"The text states 1843.","value":1843},'
                    '"tags":{"reasoning":"The topic is computing history.","value":["SCIENCE"]},'
                    '"mentions":{"reasoning":"Ada Lovelace is directly mentioned.","value":[{"text":"Ada Lovelace","label":"PERSON"}]}}'
                )
            )
            choice = SimpleNamespace(message=message)
            return SimpleNamespace(
                choices=[choice],
                model_dump=lambda: {
                    "usage": {
                        "prompt_tokens": 1,
                        "completion_tokens": 1,
                        "total_tokens": 2,
                    }
                },
            )

    class FakeClient:
        chat = SimpleNamespace(completions=FakeCompletions())

    agent = InlineReasoningAgent()
    agent.client = FakeClient()
    monkeypatch.setattr("gensie.baseline.trace_step", lambda *args, **kwargs: None)

    result = agent.run(task, "dummy-model")

    assert result == {
        "person": "Ada Lovelace",
        "year": 1843,
        "tags": ["SCIENCE"],
        "mentions": [{"text": "Ada Lovelace", "label": "PERSON"}],
    }
    generation_schema = captured["response_format"]["json_schema"]["schema"]
    assert generation_schema is not task.target_schema
    assert "reasoning" in generation_schema["properties"]["person"]["properties"]
    assert generation_schema["properties"]["person"]["properties"]["value"] == task.target_schema["properties"]["person"]
    assert INLINE_PROMPT_SCHEMA_REASONING_WRAPPER == inline_reasoning.INLINE_PROMPT_SCHEMA_VIEW
    assert "reasoning" in captured["messages"][1]["content"].split("SCHEMA:", 1)[1]
