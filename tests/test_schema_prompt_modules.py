import copy

import pytest

from gensie.fsp import (
    FSPExample,
    FieldExample,
    FieldReasoning,
    RagExtractionFspProvider,
    ReasoningSectionLabels,
    StaticFSPProvider,
    StructuredFspCase,
)
from gensie.pipeline import (
    ExtractionSpec,
    FewShotMode,
    PipelineContext,
    ReasoningMode,
    SchemaPromptMode,
)
from gensie.prompts import ExtractionPromptBuilder, render_schema_view
from gensie.prompts.extraction import ENRICHED_RAG_FIELD_DESCRIPTIONS_ENV
from gensie.prompts.system import STRICT_ANCHORING_RULE
from gensie.schemas import (
    build_deep_inline_reasoning_schema,
    build_inline_reasoning_prompt_schema,
    build_inline_reasoning_schema,
    build_selective_inline_reasoning_schema,
    clean_schema_for_prompt,
    parse_schema_fields,
    render_deep_reasoned_pydantic_schema,
    render_field_cards,
    render_pydantic_code,
    render_reasoned_pydantic_schema,
    render_selective_reasoned_pydantic_schema,
    transform_schema_for_reasoning,
    unwrap_deep_inline_reasoning_output,
    unwrap_inline_reasoning_output,
    unwrap_selective_inline_reasoning_output,
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


def _selective_schema():
    return {
        "$defs": {
            "Entity": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "label": {"type": "string"},
                },
                "required": ["text", "label"],
            },
            "Tag": {"type": "string", "enum": ["SCIENCE", "OTHER"]},
        },
        "type": "object",
        "properties": {
            "answer": {"type": "string", "description": "Answer span"},
            "status": {
                "type": "string",
                "enum": ["confirmed", "unclear"],
                "description": "Classification status",
            },
            "entities": {
                "type": "array",
                "items": {"$ref": "#/$defs/Entity"},
                "description": "Named entities mentioned in the text",
            },
            "observations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"value": {"type": "number"}},
                },
            },
            "tags": {"type": "array", "items": {"$ref": "#/$defs/Tag"}},
        },
        "required": ["answer", "status", "entities", "observations", "tags"],
    }


def _same_schema_case(
    case_id: str,
    source_text: str,
    *,
    enriched_field_descriptions: dict[str, str] | None = None,
) -> StructuredFspCase:
    values = {
        "person": "Ada Lovelace",
        "year": 1843,
        "tags": ["SCIENCE"],
        "mentions": [{"text": "Ada Lovelace", "label": "PERSON"}],
    }
    return StructuredFspCase(
        id=case_id,
        domain="technical_entities",
        language="es",
        source_text=source_text,
        instruction="Extract the person, year, and labels.",
        schema=_schema(),
        field_examples={
            field_name: FieldExample(
                value=value,
                reasoning=FieldReasoning(
                    field_asks=f"el valor del campo `{field_name}`.",
                    relevant_fragments=(
                        f"El texto del ejemplo aporta evidencia para `{field_name}`."
                    ),
                    final_value=f"se usa el valor respaldado para `{field_name}`.",
                ),
            )
            for field_name, value in values.items()
        },
        enriched_field_descriptions=enriched_field_descriptions or {},
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
    assert "person :: string (requerido)" in cards
    assert "year :: nullable[integer] (opcional)" in cards
    assert "mentions[].label :: string (requerido)" in cards


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


def test_selective_reasoning_schema_wraps_only_beneficial_root_fields():
    schema = _selective_schema()
    wrapped = build_selective_inline_reasoning_schema(schema)

    assert "reasoning" in wrapped["properties"]["answer"]["properties"]
    assert "reasoning" in wrapped["properties"]["tags"]["properties"]
    assert wrapped["properties"]["status"] == schema["properties"]["status"]
    assert wrapped["properties"]["entities"] == schema["properties"]["entities"]
    assert wrapped["properties"]["observations"] == schema["properties"]["observations"]

    code = render_selective_reasoned_pydantic_schema(schema)
    assert "answer: Reasoned[str]" in code
    assert "tags: Reasoned[List[Tag]]" in code
    assert "status: Literal[\"confirmed\", \"unclear\"]" in code
    assert "entities: List[Entity]" in code
    assert "entities: Reasoned" not in code


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

    raw_selective = {
        "answer": {"reasoning": "answer evidence", "value": "Ada Lovelace"},
        "status": "confirmed",
        "entities": [{"text": "Ada Lovelace", "label": "PERSON"}],
        "observations": [{"value": 1.0}],
        "tags": {"reasoning": "tag evidence", "value": ["SCIENCE"]},
    }
    assert unwrap_selective_inline_reasoning_output(
        raw_selective, _selective_schema()
    ) == {
        "answer": "Ada Lovelace",
        "status": "confirmed",
        "entities": [{"text": "Ada Lovelace", "label": "PERSON"}],
        "observations": [{"value": 1.0}],
        "tags": ["SCIENCE"],
    }


def test_transform_schema_for_reasoning_dispatches_by_mode():
    assert transform_schema_for_reasoning(_schema(), ReasoningMode.NONE) == _schema()
    assert "reasoning" in transform_schema_for_reasoning(
        _schema(), ReasoningMode.TOP_LEVEL
    )["properties"]["person"]["properties"]
    assert "reasoning" in transform_schema_for_reasoning(
        _schema(), ReasoningMode.DEEP
    )["$defs"]["Mention"]["properties"]["text"]["properties"]
    selective = transform_schema_for_reasoning(
        _selective_schema(), ReasoningMode.SELECTIVE_TOP_LEVEL
    )
    assert "reasoning" in selective["properties"]["answer"]["properties"]
    assert "reasoning" not in selective["properties"]["entities"].get("properties", {})


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
    assert STRICT_ANCHORING_RULE in bundle.system
    assert "EJEMPLOS FEW-SHOT:" in bundle.user
    assert "Ejemplo 1: mini" in bundle.user
    assert STRICT_ANCHORING_RULE in bundle.user
    assert "SCHEMA PYDANTIC:" in bundle.user
    assert "person: Reasoned[str]" in bundle.user
    assert "TEXTO FUENTE:" in bundle.user
    assert "Ada Lovelace published notes" in bundle.user
    assert bundle.metadata["reasoning"] == "top_level"


def test_same_schema_rag_prompt_moves_common_contract_to_system_and_instruction_to_user():
    builder = ExtractionPromptBuilder(
        fsp_provider=RagExtractionFspProvider(
            cases=[
                _same_schema_case(
                    "same_schema_one",
                    "Ada Lovelace published notes in 1843.",
                ),
                _same_schema_case(
                    "same_schema_two",
                    "Grace Hopper documented a compiler note.",
                ),
            ],
            top_k=2,
        )
    )
    context = PipelineContext(task=_task(), model="demo", usage=UsageTracker())
    extraction = ExtractionSpec(
        name="enriched-inline-reasoning-rag",
        reasoning=ReasoningMode.TOP_LEVEL,
        schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
        few_shot=FewShotMode.RAG,
    )

    bundle = builder.build(context, extraction)
    combined = f"{bundle.system}\n{bundle.user}"

    assert bundle.metadata["layout"] == "same_schema_rag_compact"
    assert bundle.metadata["prompt_layout"] == "same_schema_rag_compact"
    assert combined.count(STRICT_ANCHORING_RULE) == 1
    assert "INSTRUCCI" not in bundle.system
    assert "Extract the person, year, and labels." not in bundle.system
    assert "SCHEMA PYDANTIC:" in bundle.system
    assert "person: Reasoned[str]" in bundle.system
    assert "EJEMPLOS FEW-SHOT:" in bundle.user
    assert "INSTRUCCIÓN DEL EJEMPLO:" in bundle.user
    assert "TEXTO FUENTE DEL EJEMPLO:" in bundle.user
    assert "SALIDA DEL EJEMPLO:" in bundle.user
    assert "SCHEMA PYDANTIC:" not in bundle.user
    assert "SCHEMA PYDANTIC DEL EJEMPLO:" not in bundle.user
    assert "TAREA NUEVA:\n\nINSTRUCCIÓN:" in bundle.user
    assert "INSTRUCCIÓN:\nExtract the person, year, and labels." in bundle.user
    assert "TEXTO FUENTE:\nAda Lovelace published notes" in bundle.user
    assert len(bundle.metadata["fsp_examples"]) == 2
    assert all(
        item["retrieval"]["schema_match"] is True
        for item in bundle.metadata["fsp_examples"]
    )
    assert "No cites fragmentos irrelevantes" in bundle.system
    assert "estilo de reasoning" in bundle.system
    assert "Todo `reasoning` debe usar exactamente tres secciones" in bundle.system
    assert "`EL CAMPO PIDE: ...`" in bundle.system
    assert "`FRAGMENTOS RELEVANTES: ...`" in bundle.system
    assert "`VALOR FINAL: ...`" in bundle.system


def test_same_schema_rag_reasoning_format_rule_uses_provider_labels():
    labels = ReasoningSectionLabels(
        field_asks="CAMPO",
        relevant_fragments="EVIDENCIA",
        final_value="RESPUESTA",
    )
    builder = ExtractionPromptBuilder(
        fsp_provider=RagExtractionFspProvider(
            cases=[
                _same_schema_case(
                    "same_schema_one",
                    "Ada Lovelace published notes in 1843.",
                ),
                _same_schema_case(
                    "same_schema_two",
                    "Grace Hopper documented a compiler note.",
                ),
            ],
            labels=labels,
            top_k=2,
        )
    )
    context = PipelineContext(task=_task(), model="demo", usage=UsageTracker())
    extraction = ExtractionSpec(
        name="enriched-inline-reasoning-rag",
        reasoning=ReasoningMode.TOP_LEVEL,
        schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
        few_shot=FewShotMode.RAG,
    )

    bundle = builder.build(context, extraction)

    assert "`CAMPO: ...`" in bundle.system
    assert "`EVIDENCIA: ...`" in bundle.system
    assert "`RESPUESTA: ...`" in bundle.system
    assert "`EL CAMPO PIDE: ...`" not in bundle.system
    assert '"reasoning": "CAMPO:' in bundle.user


def test_same_schema_plain_pydantic_rag_prompt_uses_compact_layout_without_reasoning_rules():
    builder = ExtractionPromptBuilder(
        fsp_provider=RagExtractionFspProvider(
            cases=[
                _same_schema_case(
                    "same_schema_one",
                    "Ada Lovelace published notes in 1843.",
                ),
                _same_schema_case(
                    "same_schema_two",
                    "Grace Hopper documented a compiler note.",
                ),
            ],
            top_k=2,
        )
    )
    context = PipelineContext(task=_task(), model="demo", usage=UsageTracker())
    extraction = ExtractionSpec(
        name="enriched-schema-rag",
        reasoning=ReasoningMode.NONE,
        schema_prompt=SchemaPromptMode.PYDANTIC,
        few_shot=FewShotMode.RAG,
    )

    bundle = builder.build(context, extraction)
    combined = f"{bundle.system}\n{bundle.user}"

    assert bundle.metadata["layout"] == "same_schema_rag_compact"
    assert bundle.metadata["prompt_layout"] == "same_schema_rag_compact"
    assert combined.count(STRICT_ANCHORING_RULE) == 1
    assert "SCHEMA PYDANTIC:" in bundle.system
    assert "person: str" in bundle.system
    assert "Reasoned[" not in combined
    assert '"reasoning":' not in combined
    assert "El `reasoning` debe" not in combined
    assert "No cites fragmentos irrelevantes" not in combined
    assert "formato de salida" in bundle.system
    assert "estilo de reasoning" not in combined
    assert "EJEMPLOS FEW-SHOT:" in bundle.user
    assert "INSTRUCCIÓN DEL EJEMPLO:" in bundle.user
    assert "TAREA NUEVA:\n\nINSTRUCCIÓN:" in bundle.user
    assert "INSTRUCCIÓN:\nExtract the person, year, and labels." in bundle.user
    assert "Extract the person, year, and labels." not in bundle.system
    assert '"person": "Ada Lovelace"' in bundle.user
    assert "SCHEMA PYDANTIC:" not in bundle.user
    assert "SCHEMA PYDANTIC DEL EJEMPLO:" not in bundle.user
    assert len(bundle.metadata["fsp_examples"]) == 2


def test_same_schema_rag_prompt_can_use_enriched_field_descriptions(monkeypatch):
    monkeypatch.setenv(ENRICHED_RAG_FIELD_DESCRIPTIONS_ENV, "1")
    builder = ExtractionPromptBuilder(
        fsp_provider=RagExtractionFspProvider(
            cases=[
                _same_schema_case(
                    "same_schema_one",
                    "Ada Lovelace published notes in 1843.",
                    enriched_field_descriptions={
                        "person": "Nombre de persona verbatim con guía enriquecida.",
                        "mentions[].label": (
                            "Etiqueta enriquecida para la mención, sin inferir."
                        ),
                    },
                ),
                _same_schema_case(
                    "same_schema_two",
                    "Grace Hopper documented a compiler note.",
                ),
            ],
            top_k=2,
        )
    )
    context = PipelineContext(task=_task(), model="demo", usage=UsageTracker())
    extraction = ExtractionSpec(
        name="enriched-schema-rag",
        reasoning=ReasoningMode.NONE,
        schema_prompt=SchemaPromptMode.PYDANTIC,
        few_shot=FewShotMode.RAG,
    )

    bundle = builder.build(context, extraction)

    assert bundle.metadata["layout"] == "same_schema_rag_compact"
    assert (
        'person: str = Field(..., description="Nombre de persona verbatim '
        'con guía enriquecida.")'
        in bundle.system
    )
    assert (
        'label: str = Field(..., description="Etiqueta enriquecida para la '
        'mención, sin inferir.")'
        in bundle.system
    )
    assert "Verbatim person name" not in bundle.system
    assert bundle.metadata["schema_view"]["field_description_overrides"] == [
        "mentions[].label",
        "person",
    ]


def test_rag_prompt_keeps_default_layout_when_any_selected_case_differs():
    other_schema = {
        "type": "object",
        "properties": {"year": {"type": "string"}},
    }
    builder = ExtractionPromptBuilder(
        fsp_provider=RagExtractionFspProvider(
            cases=[
                _same_schema_case(
                    "same_schema_one",
                    "Ada Lovelace published notes in 1843.",
                ),
                StructuredFspCase(
                    id="other_schema",
                    domain="technical_entities",
                    language="es",
                    source_text="Otra fuente.",
                    instruction="Extrae otro campo.",
                    schema=other_schema,
                    field_examples={
                        "year": FieldExample(
                            value="valor",
                            reasoning=FieldReasoning(
                                field_asks="el valor de `year`.",
                                relevant_fragments='"Otra fuente".',
                                final_value="el valor es valor.",
                            ),
                        )
                    },
                ),
            ],
            top_k=2,
        )
    )
    context = PipelineContext(task=_task(), model="demo", usage=UsageTracker())
    extraction = ExtractionSpec(
        name="enriched-inline-reasoning-rag",
        reasoning=ReasoningMode.TOP_LEVEL,
        schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
        few_shot=FewShotMode.RAG,
    )

    bundle = builder.build(context, extraction)

    assert bundle.metadata["layout"] == "default"
    assert "SCHEMA PYDANTIC DEL EJEMPLO:" in bundle.user
    assert "SCHEMA PYDANTIC:" in bundle.user
    assert STRICT_ANCHORING_RULE in bundle.user
