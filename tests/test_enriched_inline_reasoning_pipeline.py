from types import SimpleNamespace

from gensie.baseline import (
    EnrichedDeepInlineReasoningAgent,
    EnrichedInlineReasoningAgent,
    EnrichedInlineReasoningSuperFspAgent,
    OfficialParticipant,
)
from gensie.enriched_inline_reasoning import (
    INCLUDE_ENRICHED_INLINE_REASONING_FEW_SHOT,
    build_deep_inline_reasoning_schema,
    build_enriched_deep_inline_reasoning_prompt,
    build_enriched_inline_reasoning_few_shot_example,
    build_enriched_inline_reasoning_prompt,
    build_enriched_inline_reasoning_super_fsp_prompt,
    render_reasoned_pydantic_schema,
    render_deep_reasoned_pydantic_schema,
    unwrap_deep_inline_reasoning_output,
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


def test_render_reasoned_pydantic_schema_is_compact_and_reasoned():
    code = render_reasoned_pydantic_schema(_sample_task().target_schema)

    assert "from __future__" not in code
    assert "from typing" not in code
    assert "from pydantic" not in code
    assert "Optional[" not in code
    assert code.startswith("Nullable[T] = T | null\n\nclass Reasoned[T](BaseModel):")
    assert "class Reasoned[T](BaseModel):" in code
    assert code.count("class Reasoned[T](BaseModel):") == 1
    assert "Nullable[T] = T | null" in code
    assert "class Output(BaseModel):" in code
    assert "class SampleSchema(BaseModel):" not in code
    assert "class ReasonedPerson" not in code
    assert "Tag = Literal[\"SCIENCE\", \"OTHER\"]" in code
    assert "class Mention(BaseModel):" in code
    assert "text: str" in code
    assert "person: Reasoned[str] = Field(description=\"Verbatim person name\")" in code
    assert "year: Reasoned[Nullable[int]] = Field(description=\"Year mentioned in the text\")" in code
    assert "tags: Reasoned[List[Tag]]" in code
    assert "mentions: Reasoned[List[Mention]]" in code


def test_deep_reasoning_schema_wraps_nested_fields_and_array_items():
    schema = build_deep_inline_reasoning_schema(_sample_task().target_schema)

    person = schema["properties"]["person"]
    assert person["properties"]["reasoning"]["type"] == "string"
    assert person["properties"]["value"]["type"] == "string"

    tag_item = schema["properties"]["tags"]["properties"]["value"]["items"]
    assert tag_item["properties"]["reasoning"]["type"] == "string"
    assert tag_item["properties"]["value"]["$ref"] == "#/$defs/Tag"

    mention_item = schema["properties"]["mentions"]["properties"]["value"]["items"]
    assert mention_item["properties"]["value"]["$ref"] == "#/$defs/Mention"
    mention_def = schema["$defs"]["Mention"]
    assert mention_def["properties"]["text"]["properties"]["value"]["type"] == "string"
    assert mention_def["properties"]["label"]["properties"]["value"]["type"] == "string"


def test_render_deep_reasoned_pydantic_schema_wraps_nested_fields_and_items():
    code = render_deep_reasoned_pydantic_schema(_sample_task().target_schema)

    assert code.startswith("Nullable[T] = T | null\n\nclass Reasoned[T](BaseModel):")
    assert "class Reasoned[T](BaseModel):" in code
    assert code.count("class Reasoned[T](BaseModel):") == 1
    assert "text: Reasoned[str]" in code
    assert "label: Reasoned[str]" in code
    assert "tags: Reasoned[List[Reasoned[Tag]]]" in code
    assert "mentions: Reasoned[List[Reasoned[Mention]]]" in code
    assert "person: Reasoned[str] = Field(description=\"Verbatim person name\")" in code


def test_unwrap_deep_inline_reasoning_output_returns_final_values():
    task = _sample_task()
    raw = {
        "person": {"reasoning": "name", "value": "Ada Lovelace"},
        "year": {"reasoning": "year", "value": 1843},
        "tags": {
            "reasoning": "tags",
            "value": [{"reasoning": "science", "value": "SCIENCE"}],
        },
        "mentions": {
            "reasoning": "mentions",
            "value": [
                {
                    "reasoning": "person mention",
                    "value": {
                        "text": {"reasoning": "verbatim", "value": "Ada Lovelace"},
                        "label": {"reasoning": "type", "value": "PERSON"},
                    },
                }
            ],
        },
    }

    result = unwrap_deep_inline_reasoning_output(raw, task.target_schema)

    assert result == {
        "person": "Ada Lovelace",
        "year": 1843,
        "tags": ["SCIENCE"],
        "mentions": [{"text": "Ada Lovelace", "label": "PERSON"}],
    }


def test_enriched_inline_few_shot_uses_pydantic_schema():
    example = build_enriched_inline_reasoning_few_shot_example()

    assert INCLUDE_ENRICHED_INLINE_REASONING_FEW_SHOT is True
    assert "INSTRUCCI" in example
    assert "SCHEMA PYDANTIC DEL EJEMPLO:" in example
    assert "SCHEMA MODIFICADO DEL EJEMPLO" not in example
    assert "class Reasoned[T](BaseModel):" in example
    assert "class Output(BaseModel):" in example
    assert "class LiteraryWork(BaseModel):" not in example
    assert "Nullable[T] = T | null" in example
    assert "OUTPUT DEL EJEMPLO:" in example
    assert "\"reasoning\"" in example
    assert "\"value\": null" in example
    assert "fragmento verbatim" in example
    assert "literary_impact_evidence" in example
    assert "primera novela moderna" in example


def test_enriched_deep_inline_prompt_explains_recursive_reasoning():
    prompt = build_enriched_deep_inline_reasoning_prompt(_sample_task())

    assert prompt.startswith("TAREA:")
    assert "FORMATO DE RAZONAMIENTO RECURSIVO:" in prompt
    assert "cada elemento tiene reasoning propio" in prompt
    assert "tags: Reasoned[List[Reasoned[Tag]]]" in prompt
    assert "mentions: Reasoned[List[Reasoned[Mention]]]" in prompt
    assert prompt.count("class Output(BaseModel):") == 2


def test_enriched_inline_prompt_puts_rules_before_few_shot():
    prompt = build_enriched_inline_reasoning_prompt(_sample_task())

    assert prompt.startswith("TAREA:")
    assert "FORMATO DE RAZONAMIENTO:" in prompt
    assert "EJEMPLO:" in prompt
    assert "INSTRUCCIÓN:" in prompt
    assert "SCHEMA PYDANTIC:" in prompt
    assert "TEXTO FUENTE:" in prompt
    assert prompt.index("FORMATO DE RAZONAMIENTO:") < prompt.index("EJEMPLO:")
    assert prompt.index("FIN DEL EJEMPLO.") < prompt.index("INSTRUCCIÓN:")
    assert "Reasoned[T] significa" in prompt
    assert "Nullable[T] significa" in prompt
    assert prompt.count("class Output(BaseModel):") == 2
    assert "fragmento verbatim/source text/evidence" in prompt
    assert "class SampleSchema(BaseModel):" not in prompt


def test_enriched_inline_super_fsp_prompt_uses_full_synthetic_example():
    prompt = build_enriched_inline_reasoning_super_fsp_prompt(_sample_task())

    assert prompt.startswith("TAREA:")
    assert "FORMATO DE RAZONAMIENTO:" in prompt
    assert "EJEMPLO:\nINSTRUCCIÓN DEL EJEMPLO:" in prompt
    assert "Este super ejemplo" not in prompt
    assert "Subtareas seleccionadas:" not in prompt
    assert "Atlas-IE presenta avances en extracción de información" in prompt
    assert "pilot_outcome: Reasoned[PilotOutcome]" in prompt
    assert "entities: Reasoned[List[Entity]]" in prompt
    assert "registry_code: Reasoned[str]" in prompt
    assert "Lucía Ferrer" in prompt
    assert "Andrés Núñez" in prompt
    assert "SHA256" not in prompt
    assert "CEO" not in prompt
    assert "métodos clínicos" not in prompt
    assert "Complexity:" not in prompt
    assert "Don Quijote de la Mancha" not in prompt
    assert prompt.index("FORMATO DE RAZONAMIENTO:") < prompt.index("EJEMPLO:")
    assert prompt.index("FIN DEL EJEMPLO.") < prompt.index("INSTRUCCIÓN:")
    assert prompt.count("class Output(BaseModel):") == 2


def test_enriched_inline_agent_uses_wrapper_schema_and_returns_values(monkeypatch):
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

    agent = EnrichedInlineReasoningAgent()
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
    assert generation_schema["properties"]["person"]["properties"]["reasoning"]["type"] == "string"
    assert generation_schema["properties"]["person"]["properties"]["value"] == task.target_schema["properties"]["person"]
    prompt = captured["messages"][1]["content"]
    assert "class Reasoned[T](BaseModel):" in prompt
    assert "person: Reasoned[str]" in prompt


def test_enriched_inline_super_fsp_agent_only_changes_prompt(monkeypatch):
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

    agent = EnrichedInlineReasoningSuperFspAgent()
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
    assert generation_schema["properties"]["person"]["properties"]["value"] == task.target_schema["properties"]["person"]
    assert generation_schema["properties"]["mentions"]["properties"]["value"]["items"]["$ref"] == "#/$defs/Mention"
    prompt = captured["messages"][1]["content"]
    assert "Atlas-IE presenta avances en extracción de información" in prompt
    assert "Este super ejemplo" not in prompt
    assert "Don Quijote de la Mancha" not in prompt
    assert "SHA256" not in prompt
    assert "CEO" not in prompt
    assert "mentions: Reasoned[List[Mention]]" in prompt


def test_enriched_deep_inline_agent_uses_recursive_wrapper_schema_and_returns_values(monkeypatch):
    task = _sample_task()
    captured = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            message = SimpleNamespace(
                content=(
                    '{"person":{"reasoning":"The text names Ada Lovelace.","value":"Ada Lovelace"},'
                    '"year":{"reasoning":"The text states 1843.","value":1843},'
                    '"tags":{"reasoning":"The topic is computing history.","value":[{"reasoning":"Computing is science.","value":"SCIENCE"}]},'
                    '"mentions":{"reasoning":"Ada Lovelace is directly mentioned.","value":[{"reasoning":"This item is the person mention.","value":{"text":{"reasoning":"The text says Ada Lovelace.","value":"Ada Lovelace"},"label":{"reasoning":"Ada Lovelace is a person.","value":"PERSON"}}}]}}'
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

    agent = EnrichedDeepInlineReasoningAgent()
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
    mention_def = generation_schema["$defs"]["Mention"]
    assert mention_def["properties"]["text"]["properties"]["reasoning"]["type"] == "string"
    assert mention_def["properties"]["text"]["properties"]["value"]["type"] == "string"
    tag_item = generation_schema["properties"]["tags"]["properties"]["value"]["items"]
    assert tag_item["properties"]["reasoning"]["type"] == "string"
    prompt = captured["messages"][1]["content"]
    assert "FORMATO DE RAZONAMIENTO RECURSIVO:" in prompt
    assert "tags: Reasoned[List[Reasoned[Tag]]]" in prompt


def test_official_participant_registers_enriched_inline_reasoning():
    names = [p.name for p in OfficialParticipant().get_info().pipelines]

    assert "enriched-inline-reasoning" in names
    assert "enriched-inline-reasoning-super-fsp" in names
    assert "enriched-inline-reasoning-deep" in names
