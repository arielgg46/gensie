from gensie.fsp.cases import quijote_cultural_literature_case
from gensie.fsp.examples import (
    CandidateOrder,
    FieldExample,
    ReasoningSectionLabels,
    StructuredFspCase,
)
from gensie.fsp.fixed import build_inline_reasoning_few_shot_example
from gensie.fsp.projection import project_structured_fsp_case
from gensie.fsp.rag import RagExtractionFspProvider
from gensie.fsp.render_extraction import (
    build_extraction_output,
    render_extraction_fsp_example,
)
from gensie.fsp.render_judge import render_judge_candidate_summary
from gensie.pipeline import (
    ExtractionSpec,
    FewShotMode,
    PipelineContext,
    ReasoningMode,
    SchemaPromptMode,
)
from gensie.task import Task
from gensie.usage import UsageTracker
from gensie.schemas.projection import build_reduced_schema


def _context() -> PipelineContext:
    return _context_for_schema(
        {
            "type": "object",
            "properties": {"person": {"type": "string"}},
            "required": ["person"],
        }
    )


def _context_for_schema(
    schema: dict,
    *,
    instruction: str = "Extrae persona y año.",
) -> PipelineContext:
    return PipelineContext(
        task=Task(
            id="sample",
            input_text="Ada Lovelace publicó notas en 1843.",
            instruction=instruction,
            target_schema=schema,
        ),
        model="demo",
        usage=UsageTracker(),
    )


def _minimal_case(
    case_id: str,
    schema: dict,
    *,
    tags: tuple[str, ...] = (),
    field_tags: tuple[str, ...] = (),
    source_text: str | None = None,
) -> StructuredFspCase:
    return StructuredFspCase(
        id=case_id,
        domain="test",
        language="es",
        source_text=source_text or f"Texto fuente del caso {case_id}.",
        instruction="Extrae los campos solicitados.",
        schema=schema,
        field_examples={
            field_name: FieldExample(
                value=_example_value(field_schema),
                tags=field_tags,
            )
            for field_name, field_schema in schema.get("properties", {}).items()
            if isinstance(field_name, str) and isinstance(field_schema, dict)
        },
        tags=tags,
    )


def _example_value(schema: dict):
    if schema.get("type") == "array":
        return []
    if schema.get("type") in {"integer", "number"}:
        return 1
    if schema.get("type") == "boolean":
        return True
    if "anyOf" in schema:
        return None
    return "valor"


def test_quijote_cultural_case_renders_current_fixed_inline_fsp_exactly():
    case = quijote_cultural_literature_case()
    extraction = ExtractionSpec(
        name="inline-reasoning-rag-fsp",
        reasoning=ReasoningMode.TOP_LEVEL,
        schema_prompt=SchemaPromptMode.INLINE_REASONING_WRAPPER,
        few_shot=FewShotMode.RAG,
    )

    rendered = render_extraction_fsp_example(case, extraction)

    assert rendered == build_inline_reasoning_few_shot_example()


def test_quijote_cultural_case_does_not_include_enriched_extra_field():
    case = quijote_cultural_literature_case()

    assert "literary_impact_evidence" not in case.schema["properties"]
    assert "literary_impact_evidence" not in case.field_examples


def test_structured_case_renders_none_and_top_level_outputs_from_same_base():
    case = quijote_cultural_literature_case()

    direct = build_extraction_output(case, ReasoningMode.NONE)
    reasoned = build_extraction_output(case, ReasoningMode.TOP_LEVEL)

    assert direct["title"] == "Don Quijote de la Mancha"
    assert direct["publication_year"] == 1605
    assert reasoned["title"]["value"] == direct["title"]
    assert reasoned["title"]["reasoning"].startswith("EL CAMPO PIDE:")
    assert "FRAGMENTOS RELEVANTES:" in reasoned["title"]["reasoning"]
    assert "VALOR FINAL:" in reasoned["title"]["reasoning"]


def test_reasoning_section_labels_are_renderer_configuration():
    case = quijote_cultural_literature_case()
    labels = ReasoningSectionLabels(
        field_asks="CAMPO",
        relevant_fragments="EVIDENCIA",
        final_value="RESPUESTA",
    )

    reasoned = build_extraction_output(
        case,
        ReasoningMode.TOP_LEVEL,
        labels=labels,
    )

    assert reasoned["title"]["reasoning"].startswith("CAMPO:")
    assert "EVIDENCIA:" in reasoned["title"]["reasoning"]
    assert "RESPUESTA:" in reasoned["title"]["reasoning"]
    assert "EL CAMPO PIDE:" not in reasoned["title"]["reasoning"]


def test_rag_extraction_provider_supports_none_and_top_level_but_not_deep():
    provider = RagExtractionFspProvider(cases=[quijote_cultural_literature_case()])

    none_examples = provider.examples(
        _context(),
        ExtractionSpec(
            name="baseline-rag-fsp",
            reasoning=ReasoningMode.NONE,
            schema_prompt=SchemaPromptMode.JSON_SCHEMA,
            few_shot=FewShotMode.RAG,
        ),
    )
    top_examples = provider.examples(
        _context(),
        ExtractionSpec(
            name="enriched-inline-reasoning-rag-fsp",
            reasoning=ReasoningMode.TOP_LEVEL,
            schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
            few_shot=FewShotMode.RAG,
        ),
    )
    deep_examples = provider.examples(
        _context(),
        ExtractionSpec(
            name="deep-rag-fsp",
            reasoning=ReasoningMode.DEEP,
            schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
            few_shot=FewShotMode.RAG,
        ),
    )

    assert none_examples[0].name == "cultural_literature_quijote"
    assert '"title": "Don Quijote de la Mancha"' in none_examples[0].prompt
    assert '"reasoning": "EL CAMPO PIDE:' in top_examples[0].prompt
    assert deep_examples == ()


def test_rag_extraction_provider_prefers_same_schema_over_resource_order():
    target_schema = {
        "type": "object",
        "properties": {
            "mass_kg": {
                "anyOf": [{"type": "number"}, {"type": "null"}],
                "description": "Mass in kilograms",
            }
        },
    }
    unrelated_schema = {
        "type": "object",
        "properties": {"title": {"type": "string", "description": "Title"}},
    }
    provider = RagExtractionFspProvider(
        cases=[
            _minimal_case("first_but_unrelated", unrelated_schema),
            _minimal_case("same_schema", target_schema),
        ]
    )

    examples = provider.examples(
        _context_for_schema(target_schema, instruction="Extrae la masa."),
        ExtractionSpec(
            name="baseline-rag-fsp",
            reasoning=ReasoningMode.NONE,
            schema_prompt=SchemaPromptMode.JSON_SCHEMA,
            few_shot=FewShotMode.RAG,
        ),
    )

    assert examples[0].name == "same_schema"
    assert examples[0].metadata["retrieval"]["schema_match"] is True
    assert examples[0].metadata["retrieval"]["score"] > 100


def test_rag_extraction_provider_uses_schema_tags_when_schema_differs():
    target_schema = {
        "type": "object",
        "properties": {
            "observations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"value": {"type": "number"}},
                },
                "description": "Measured observations",
            },
            "event_date": {
                "anyOf": [{"type": "string"}, {"type": "null"}],
                "description": "Date of the event",
            },
        },
    }
    plain_string_schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
    }
    similar_shape_schema = {
        "type": "object",
        "properties": {
            "samples": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"amount": {"type": "number"}},
                },
            },
            "reported_date": {
                "anyOf": [{"type": "string"}, {"type": "null"}],
            },
        },
    }
    provider = RagExtractionFspProvider(
        cases=[
            _minimal_case("plain_string", plain_string_schema),
            _minimal_case("similar_tags", similar_shape_schema),
        ]
    )

    examples = provider.examples(
        _context_for_schema(target_schema, instruction="Extrae mediciones y fecha."),
        ExtractionSpec(
            name="baseline-rag-fsp",
            reasoning=ReasoningMode.NONE,
            schema_prompt=SchemaPromptMode.JSON_SCHEMA,
            few_shot=FewShotMode.RAG,
        ),
    )
    matched_tags = set(examples[0].metadata["retrieval"]["matched_tags"])

    assert examples[0].name == "similar_tags"
    assert {"complex_object_array", "nested_numeric_object_array", "grounded_null"} <= matched_tags


def test_rag_extraction_provider_skips_examples_over_prompt_budget():
    provider = RagExtractionFspProvider(
        cases=[quijote_cultural_literature_case()],
        max_prompt_chars=10,
    )

    examples = provider.examples(
        _context(),
        ExtractionSpec(
            name="baseline-rag-fsp",
            reasoning=ReasoningMode.NONE,
            schema_prompt=SchemaPromptMode.JSON_SCHEMA,
            few_shot=FewShotMode.RAG,
        ),
    )

    assert examples == ()


def test_rag_extraction_provider_falls_back_when_top_candidate_exceeds_budget():
    target_schema = {
        "type": "object",
        "properties": {"person": {"type": "string"}},
    }
    similar_schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
    }
    provider = RagExtractionFspProvider(
        cases=[
            _minimal_case(
                "same_schema_but_too_long",
                target_schema,
                source_text="Texto. " * 1000,
            ),
            _minimal_case("similar_short", similar_schema),
        ],
        max_prompt_chars=1000,
    )

    examples = provider.examples(
        _context_for_schema(target_schema),
        ExtractionSpec(
            name="baseline-rag-fsp",
            reasoning=ReasoningMode.NONE,
            schema_prompt=SchemaPromptMode.JSON_SCHEMA,
            few_shot=FewShotMode.RAG,
        ),
    )

    assert examples[0].name == "similar_short"


def test_judge_candidate_summary_renders_empty_array_trials_and_ordering():
    judge = quijote_cultural_literature_case().judge
    assert judge is not None

    summary = render_judge_candidate_summary(
        judge,
        field_names=("genres",),
        include_support_counts=True,
        candidate_order=CandidateOrder.SUPPORT_ASC,
    )
    hidden_counts = render_judge_candidate_summary(
        judge,
        field_names=("genres",),
        include_support_counts=False,
    )

    assert "Trials válidos: 4" in summary
    assert "- 1/4: \"tradición caballeresca\"" in summary
    assert "- Lista vacía en 1/4 trials." in summary
    assert "- Lista vacía." in hidden_counts
    assert "1/4" not in hidden_counts


def test_array_candidate_evidence_uses_contextual_verbatim_fragments():
    judge = quijote_cultural_literature_case().judge
    assert judge is not None
    genres = judge.fields["genres"]

    evidences = {
        candidate.value: candidate.evidence for candidate in genres.candidates
    }

    assert all('"' in text for text in evidences.values())
    assert all(
        "El texto respalda explícitamente" not in text
        for text in evidences.values()
    )
    assert (
        "Don Quijote de la Mancha es una novela escrita por el español "
        "Miguel de Cervantes Saavedra"
        in evidences["novela"]
    )
    assert (
        "Representa la primera novela moderna y la primera novela polifónica"
        in evidences["novela moderna"]
    )
    assert (
        "Representa la primera novela moderna y la primera novela polifónica"
        in evidences["novela polifónica"]
    )
    assert (
        "desmitificadora de la tradición caballeresca y cortés por su "
        "tratamiento burlesco"
        in evidences["tradición caballeresca"]
    )


def test_reduced_schema_projects_top_level_properties_and_required_fields():
    case = quijote_cultural_literature_case()

    reduced = build_reduced_schema(
        case.schema,
        ("genres", "title", "missing", "genres"),
    )

    assert list(reduced["properties"]) == ["title", "genres"]
    assert reduced["required"] == ["title"]
    assert "$defs" not in reduced or reduced["$defs"] == case.schema.get("$defs")


def test_structured_fsp_case_projection_filters_schema_outputs_and_judge_fields():
    case = quijote_cultural_literature_case()

    projected = project_structured_fsp_case(
        case,
        ("genres", "title"),
        include_stable_fields=False,
    )
    direct = build_extraction_output(projected, ReasoningMode.NONE)
    reasoned = build_extraction_output(projected, ReasoningMode.TOP_LEVEL)
    assert projected.judge is not None

    assert list(projected.schema["properties"]) == ["title", "genres"]
    assert set(projected.field_examples) == {"title", "genres"}
    assert set(direct) == {"title", "genres"}
    assert set(reasoned) == {"title", "genres"}
    assert set(projected.judge.fields) == {"title", "genres"}
    assert projected.judge.total_trials == 4
    assert projected.judge.stable_fields == {}
    assert projected.judge.fields["genres"].empty_trial_count == 1


def test_structured_fsp_case_projection_can_keep_judge_stable_fields():
    case = quijote_cultural_literature_case()

    projected = project_structured_fsp_case(
        case,
        ("title",),
        include_stable_fields=True,
    )

    assert projected.judge is not None
    assert projected.judge.stable_fields == {"author": "Miguel de Cervantes Saavedra"}
    assert set(projected.judge.fields) == {"title"}
