import json

import pytest

from gensie.super_fsp import (
    SUPER_FSP_INPUT_TEXT,
    SUPER_FSP_INSTRUCTION,
    build_super_fsp_example_for_schema,
    build_super_fsp_example,
    build_super_fsp_instruction,
    build_super_fsp_input_text,
    build_super_fsp_reasoned_output,
    build_super_fsp_schema,
    list_super_fsp_subtasks,
    render_super_fsp_reasoned_pydantic_schema,
    resolve_super_fsp_subtasks,
    explain_super_fsp_subtask_selection,
    select_super_fsp_subtasks_for_schema,
    suggest_super_fsp_subtasks_for_schema,
)


def test_super_fsp_builds_only_selected_subtasks():
    selected = ["enum_classification", "grounded_null", "entity_array"]

    schema = build_super_fsp_schema(selected)
    code = render_super_fsp_reasoned_pydantic_schema(selected)
    output = build_super_fsp_reasoned_output(selected)
    example = build_super_fsp_example(selected)

    assert set(schema["properties"]) == {
        "pilot_outcome",
        "exact_public_release_date",
        "dataset_doi",
        "repository_url",
        "entities",
    }
    assert "$defs" in schema
    assert "PilotOutcome = Literal[\"POSITIVE\", \"NEGATIVE\", \"INCONCLUSIVE\"]" in code
    assert "class Entity(BaseModel):" in code
    assert "pilot_outcome: Reasoned[PilotOutcome]" in code
    assert "entities: Reasoned[List[Entity]]" in code
    assert output["pilot_outcome"]["value"] == "POSITIVE"
    assert output["dataset_doi"]["value"] is None
    assert output["entities"]["value"][0] == {"text": "Lucía Ferrer", "label": "PERSON"}
    assert (
        "tras la arquitectura de Atlas-IE está Lucía Ferrer, coordinadora del estudio"
        in build_super_fsp_reasoned_output(["long_verbatim_evidence"])["capability_evidence"]["value"]
    )
    assert "answer:" not in code
    assert "budget_eur" not in example
    assert "Atlas-IE presenta avances en extracción de información" in example
    assert "SHA256" not in example
    assert "CEO" not in example
    assert "métodos clínicos" not in example
    assert "Complexity" not in json.dumps(schema, ensure_ascii=False)
    assert "Complexity" not in example


def test_super_fsp_instruction_and_source_text_are_fixed():
    instruction = build_super_fsp_instruction(["verbatim_answer", "numeric_normalization"])
    input_text = build_super_fsp_input_text(["entity_array"])

    assert instruction == SUPER_FSP_INSTRUCTION
    assert input_text == SUPER_FSP_INPUT_TEXT
    assert instruction == (
        "Extrae del texto del ejemplo la información solicitada en todos los campos del schema."
    )
    assert "answer" not in instruction
    assert "Subtareas seleccionadas" not in instruction


def test_super_fsp_rejects_empty_or_unknown_selection():
    with pytest.raises(ValueError, match="At least one"):
        resolve_super_fsp_subtasks([])

    with pytest.raises(ValueError, match="Unknown super FSP subtask id"):
        resolve_super_fsp_subtasks(["missing_task"])


def test_super_fsp_lists_default_subtasks_in_stable_order():
    ids = list_super_fsp_subtasks()

    assert ids[0] == "verbatim_answer"
    assert ids[-1] == "sentinel_pattern"
    assert len(ids) == len(set(ids))


def test_suggest_super_fsp_subtasks_for_schema_covers_shape_features():
    schema = {
        "$defs": {
            "Tag": {
                "enum": ["A", "B"],
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
                "title": "Mention",
                "type": "object",
            },
            "Ingredient": {
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "amount": {
                        "anyOf": [{"type": "number"}, {"type": "null"}],
                        "default": None,
                    },
                },
                "required": ["name"],
                "title": "Ingredient",
                "type": "object",
            },
        },
        "additionalProperties": False,
        "properties": {
            "answer": {
                "description": "The verbatim fragment that answers the question.",
                "type": "string",
            },
            "summary": {
                "description": "A brief summary of the main facts.",
                "type": "string",
            },
            "event_date": {
                "anyOf": [{"type": "string"}, {"type": "null"}],
                "default": None,
                "description": "Date normalized as YYYY-MM-DD.",
            },
            "is_chronic": {
                "anyOf": [{"type": "boolean"}, {"type": "null"}],
                "default": None,
            },
            "score": {"minimum": 1, "maximum": 10, "type": "integer"},
            "tags": {"items": {"$ref": "#/$defs/Tag"}, "type": "array"},
            "mentions": {"items": {"$ref": "#/$defs/Mention"}, "type": "array"},
            "ingredients": {"items": {"$ref": "#/$defs/Ingredient"}, "type": "array"},
            "registration_code": {
                "description": "Use NONE if no explicit code appears.",
                "pattern": "^[A-Z\\-0-9]+$",
                "type": "string",
            },
        },
        "required": ["answer"],
        "type": "object",
    }

    suggested = suggest_super_fsp_subtasks_for_schema(schema)

    assert "verbatim_answer" in suggested
    assert "summary_string" in suggested
    assert "date_normalization" in suggested
    assert "numeric_normalization" in suggested
    assert "nullable_boolean" in suggested
    assert "grounded_null" in suggested
    assert "enum_array" in suggested
    assert "entity_array" in suggested
    assert "nested_numeric_object_array" in suggested
    assert "bounded_score" in suggested
    assert "sentinel_pattern" in suggested
    assert suggested == [
        subtask_id for subtask_id in list_super_fsp_subtasks() if subtask_id in suggested
    ]


def test_select_super_fsp_subtasks_explains_triggering_schema_paths():
    schema = {
        "$defs": {
            "Tag": {
                "enum": ["A", "B"],
                "title": "Tag",
                "type": "string",
            },
            "Entity": {
                "additionalProperties": False,
                "properties": {
                    "text": {"type": "string"},
                    "label": {"$ref": "#/$defs/Tag"},
                },
                "required": ["text", "label"],
                "type": "object",
            },
        },
        "additionalProperties": False,
        "properties": {
            "answer": {
                "description": "The verbatim fragment that answers the question.",
                "type": "string",
            },
            "published_at": {
                "description": "Date normalized as YYYY-MM-DD.",
                "format": "date",
                "type": "string",
            },
            "score": {
                "anyOf": [{"type": "number"}, {"type": "null"}],
                "default": None,
                "description": "Numeric score. Return null if not explicitly in the text.",
            },
            "has_success": {
                "description": "True if the text states the experiment succeeded.",
                "type": "boolean",
            },
            "tags": {"items": {"$ref": "#/$defs/Tag"}, "type": "array"},
            "entities": {"items": {"$ref": "#/$defs/Entity"}, "type": "array"},
            "registry_code": {
                "pattern": "^[A-Z\\-0-9]+$",
                "type": "string",
            },
        },
        "required": ["answer"],
        "type": "object",
    }

    selected = select_super_fsp_subtasks_for_schema(schema)
    suggested = suggest_super_fsp_subtasks_for_schema(schema)
    decisions = {
        decision.subtask_id: decision
        for decision in explain_super_fsp_subtask_selection(schema)
    }

    assert selected == suggested
    assert "verbatim_answer" in selected
    assert "date_normalization" in selected
    assert "numeric_normalization" in selected
    assert "boolean_inference" in selected
    assert "grounded_null" in selected
    assert "enum_array" in selected
    assert "entity_array" in selected
    assert "sentinel_pattern" in selected
    assert decisions["verbatim_answer"].field_paths == ("answer",)
    assert "published_at" in decisions["date_normalization"].field_paths
    assert "score" in decisions["grounded_null"].field_paths
    assert "registry_code" in decisions["sentinel_pattern"].field_paths
    assert decisions["sentinel_pattern"].reason


def test_build_super_fsp_example_for_schema_uses_selected_subset():
    schema = {
        "additionalProperties": False,
        "properties": {
            "summary": {
                "description": "A brief summary of the main facts.",
                "type": "string",
            },
            "is_relevant": {"type": "boolean"},
        },
        "required": ["summary", "is_relevant"],
        "type": "object",
    }

    example = build_super_fsp_example_for_schema(schema)

    assert "summary: Reasoned[str]" in example
    assert "has_confidentiality_protocol: Reasoned[bool]" in example
    assert "entities: Reasoned[List[Entity]]" not in example
    assert "measurements: Reasoned[List[MetricMeasurement]]" not in example
