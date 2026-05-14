import copy

import pytest

from gensie.fsp import FSPExample, StaticFSPProvider
from gensie.pipeline import (
    ExtractionSpec,
    FewShotMode,
    PipelineContext,
    ReasoningMode,
    SchemaPromptMode,
)
from gensie.prompts import ExtractionPromptBuilder, render_schema_view
from gensie.schemas import (
    build_deep_inline_reasoning_schema,
    build_inline_reasoning_prompt_schema,
    build_inline_reasoning_schema,
    clean_schema_for_prompt,
    parse_schema_fields,
    render_deep_reasoned_pydantic_schema,
    render_field_cards,
    render_pydantic_code,
    render_reasoned_pydantic_schema,
    transform_schema_for_reasoning,
    unwrap_deep_inline_reasoning_output,
    unwrap_inline_reasoning_output,
)
from gensie.task import Task
from gensie.usage import UsageTracker


def _schema():
    return {
        "$defs": {
            "Tag": {"enum": ["SCIENCE", "OTHER"], "title": "Tag", "type": "string"},
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
            "tags": {"items": {"$ref": "#/$defs/Tag"}, "type": "array"},
            "mentions": {"items": {"$ref": "#/$defs/Mention"}, "type": "array"},
        },
        "required": ["person"],
        "title": "SampleSchema",
        "type": "object",
    }


def _task() -> Task:
    return Task(
        id="sample",
        input_text="Ada Lovelace published notes about the Analytical Engine in 1843.",
        instruction="Extract the person, year, and labels.",
        target_schema=_schema(),
    )


def test_clean_schema_for_prompt_keeps_root_description_separate():
    clean_schema, root_description = clean_schema_for_prompt(_schema())

    assert root_description == "Extracts historical computing facts."
    assert "description" not in clean_schema
    assert "additionalProperties" not in clean_schema
    assert "required" not in clean_schema
    assert "title" not in clean_schema["properties"]["person"]
    assert clean_schema["properties"]["person"]["description"] == "Verbatim person name"


def test_field_parser_and_cards_walk_nested_refs_and_nullable_fields():
    fields = parse_schema_fields(_schema())
    by_name = {field.name: field for field in fields}

    assert by_name["year"].nullable is True
    assert by_name["tags"].items.enum == ["SCIENCE", "OTHER"]
    assert by_name["mentions"].items.properties[0].path == "mentions[].text"

    cards = render_field_cards(_schema())
    assert "person :: string (required)" in cards
    assert "year :: nullable[integer] (optional)" in cards
    assert "mentions[].label :: string (required)" in cards


def test_pydantic_renderers_cover_final_top_level_and_deep_reasoning():
    final_code = render_pydantic_code(_schema())
    assert "class SampleSchema(BaseModel):" in final_code
    assert "person: str = Field(..., description=\"Verbatim person name\")" in final_code
    assert "year: Optional[int] = Field(None, description=\"Year mentioned in the text\")" in final_code

    top_level_code = render_reasoned_pydantic_schema(_schema())
    assert top_level_code.startswith("Nullable[T] = T | null")
    assert "class Output(BaseModel):" in top_level_code
    assert "person: Reasoned[str] = Field(description=\"Verbatim person name\")" in top_level_code
    assert "year: Reasoned[Nullable[int]]" in top_level_code
    assert "mentions: Reasoned[List[Mention]]" in top_level_code
    assert "text: str" in top_level_code

    deep_code = render_deep_reasoned_pydantic_schema(_schema())
    assert "text: Reasoned[str]" in deep_code
    assert "tags: Reasoned[List[Reasoned[Tag]]]" in deep_code
    assert "mentions: Reasoned[List[Reasoned[Mention]]]" in deep_code


def test_top_level_reasoning_schema_wraps_only_root_fields():
    schema = _schema()
    original = copy.deepcopy(schema)

    wrapped = build_inline_reasoning_schema(schema)

    assert schema == original
    assert wrapped["required"] == ["person", "year", "tags", "mentions"]
    assert wrapped["$defs"] == schema["$defs"]
    assert wrapped["properties"]["person"]["properties"]["value"] == schema["properties"]["person"]
    assert wrapped["properties"]["mentions"]["properties"]["value"]["items"] == {
        "$ref": "#/$defs/Mention"
    }


def test_prompt_reasoning_schema_uses_clean_wrapper_schema():
    prompt_schema = build_inline_reasoning_prompt_schema(_schema())

    person = prompt_schema["properties"]["person"]
    assert person["description"] == "Verbatim person name"
    assert person["properties"]["reasoning"] == {"type": "string"}
    assert person["properties"]["value"] == {"type": "string"}
    assert "required" not in prompt_schema
    assert "additionalProperties" not in prompt_schema


def test_deep_reasoning_schema_wraps_defs_nested_fields_and_array_items():
    wrapped = build_deep_inline_reasoning_schema(_schema())

    tag_item = wrapped["properties"]["tags"]["properties"]["value"]["items"]
    assert tag_item["properties"]["value"]["$ref"] == "#/$defs/Tag"

    mention_def = wrapped["$defs"]["Mention"]
    assert mention_def["properties"]["text"]["properties"]["reasoning"]["type"] == "string"
    assert mention_def["properties"]["text"]["properties"]["value"]["type"] == "string"


def test_reasoning_unwraps_return_final_values():
    raw_top_level = {
        "person": {"reasoning": "named", "value": "Ada Lovelace"},
        "year": {"reasoning": "year", "value": 1843},
        "tags": {"reasoning": "tag", "value": ["SCIENCE"]},
        "mentions": {
            "reasoning": "mention",
            "value": [{"text": "Ada Lovelace", "label": "PERSON"}],
        },
    }
    assert unwrap_inline_reasoning_output(raw_top_level, _schema()) == {
        "person": "Ada Lovelace",
        "year": 1843,
        "tags": ["SCIENCE"],
        "mentions": [{"text": "Ada Lovelace", "label": "PERSON"}],
    }

    raw_deep = {
        "person": {"reasoning": "named", "value": "Ada Lovelace"},
        "year": {"reasoning": "year", "value": 1843},
        "tags": {
            "reasoning": "tag",
            "value": [{"reasoning": "science", "value": "SCIENCE"}],
        },
        "mentions": {
            "reasoning": "mention",
            "value": [
                {
                    "reasoning": "item",
                    "value": {
                        "text": {"reasoning": "text", "value": "Ada Lovelace"},
                        "label": {"reasoning": "label", "value": "PERSON"},
                    },
                }
            ],
        },
    }
    assert unwrap_deep_inline_reasoning_output(raw_deep, _schema()) == {
        "person": "Ada Lovelace",
        "year": 1843,
        "tags": ["SCIENCE"],
        "mentions": [{"text": "Ada Lovelace", "label": "PERSON"}],
    }


def test_transform_schema_for_reasoning_dispatches_by_mode():
    assert transform_schema_for_reasoning(_schema(), ReasoningMode.NONE) == _schema()
    assert "reasoning" in transform_schema_for_reasoning(
        _schema(), ReasoningMode.TOP_LEVEL
    )["properties"]["person"]["properties"]
    assert "reasoning" in transform_schema_for_reasoning(
        _schema(), ReasoningMode.DEEP
    )["$defs"]["Mention"]["properties"]["text"]["properties"]


def test_schema_views_render_raw_clean_pydantic_and_reasoned_variants():
    raw = render_schema_view(_schema(), SchemaPromptMode.JSON_SCHEMA)
    assert raw.heading == "SCHEMA"
    assert '"additionalProperties": false' in raw.content

    clean = render_schema_view(_schema(), SchemaPromptMode.CLEAN_JSON_SCHEMA)
    assert '"additionalProperties"' not in clean.content
    assert clean.root_description == "Extracts historical computing facts."

    pydantic = render_schema_view(_schema(), SchemaPromptMode.PYDANTIC)
    assert pydantic.heading == "SCHEMA PYDANTIC"
    assert "class SampleSchema(BaseModel):" in pydantic.content

    reasoned = render_schema_view(
        _schema(),
        SchemaPromptMode.REASONED_PYDANTIC,
        reasoning=ReasoningMode.DEEP,
    )
    assert "tags: Reasoned[List[Reasoned[Tag]]]" in reasoned.content

    with pytest.raises(ValueError, match="requires inline reasoning"):
        render_schema_view(_schema(), SchemaPromptMode.REASONED_PYDANTIC)


def test_extraction_prompt_builder_keeps_fsp_separate_from_schema_view():
    builder = ExtractionPromptBuilder(
        fsp_provider=StaticFSPProvider(
            [
                FSPExample(
                    name="mini",
                    prompt="INPUT: Ada wrote notes.\nOUTPUT should include Ada.",
                    output={"person": "Ada Lovelace"},
                )
            ]
        )
    )
    context = PipelineContext(task=_task(), model="demo", usage=UsageTracker())
    extraction = ExtractionSpec(
        name="reasoned",
        reasoning=ReasoningMode.TOP_LEVEL,
        schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
        few_shot=FewShotMode.FIXED,
    )

    bundle = builder.build(context, extraction)

    assert "Eres un motor experto de extracción de información en español" in bundle.system
    assert "razonamiento antes del valor final" in bundle.system
    assert "FEW-SHOT EXAMPLES:" in bundle.user
    assert "Example 1: mini" in bundle.user
    assert "SCHEMA PYDANTIC:" in bundle.user
    assert "person: Reasoned[str]" in bundle.user
    assert "SOURCE TEXT:" in bundle.user
    assert "Ada Lovelace published notes" in bundle.user
    assert bundle.metadata["reasoning"] == "top_level"
