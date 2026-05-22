from gensie.aggregation.verdict_fsp import RagVerdictJudgeFspProvider
from gensie.aggregation import build_judge_scope
from gensie.aggregation.verdict_schema import build_verdict_plan
from gensie.fsp.cases import (
    default_extraction_fsp_cases,
    default_fsp_cases,
    quijote_cultural_literature_case,
)
from gensie.fsp.examples import (
    CandidateOrder,
    FieldExample,
    FieldReasoning,
    ReasoningSectionLabels,
    StructuredFspCase,
)
from gensie.fsp.fixed import build_inline_reasoning_few_shot_example
from gensie.fsp.projection import project_structured_fsp_case
from gensie.fsp.rag import RagExtractionFspProvider
from gensie.fsp.render_extraction import (
    build_extraction_output,
    render_extraction_fsp_example,
    render_same_schema_extraction_fsp_example,
)
from gensie.fsp.resources import load_fsp_case_resource
from gensie.fsp.render_judge import render_judge_candidate_summary
from gensie.pipeline import (
    ExtractionResult,
    ExtractionSpec,
    FewShotMode,
    PipelineContext,
    ReasoningMode,
    SchemaPromptMode,
    TrialRecord,
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
                reasoning=FieldReasoning(
                    field_asks=f"el valor del campo `{field_name}`.",
                    relevant_fragments=(
                        f"Texto fuente del caso {case_id} contiene el valor de `{field_name}`."
                    ),
                    final_value=f"el valor final de `{field_name}` queda respaldado por el texto.",
                ),
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


def test_default_fsp_cases_keep_quijote_for_judge_rag():
    cases = default_fsp_cases()
    case_ids = {case.id for case in cases}

    assert "cultural_literature_quijote" in case_ids


def test_default_extraction_fsp_cases_load_resources_without_quijote_fixed_case():
    cases = default_extraction_fsp_cases()
    case_ids = {case.id for case in cases}

    assert len(cases) > 1
    assert "cultural_literature_quijote" not in case_ids
    assert "technical_software_lince_editor" in case_ids
    assert "stem_astronomy_detailed_marte" in case_ids


def test_fsp_case_resource_can_load_enriched_field_descriptions():
    case = load_fsp_case_resource("medical_extraction_lactosa_comprimido.json")

    assert case.enriched_field_descriptions == {
        "answer": (
            "Fragmento único y verbatim que responde exactamente la pregunta. "
            "Copia la oración o sintagma completo del texto fuente, conservando "
            "unidades, tildes y puntuación; no resumas, no normalices cantidades "
            "y no añadas contexto externo."
        )
    }


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


def test_rag_extraction_provider_exposes_structured_selection():
    target_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "year": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
        },
    }
    provider = RagExtractionFspProvider(
        cases=[
            _minimal_case("same_schema_one", target_schema),
            _minimal_case("same_schema_two", target_schema),
        ],
        top_k=2,
    )

    selection = provider.select(
        _context_for_schema(target_schema, instruction="Extrae nombre y año."),
        ExtractionSpec(
            name="enriched-inline-reasoning-rag-fsp",
            reasoning=ReasoningMode.TOP_LEVEL,
            schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
            few_shot=FewShotMode.RAG,
        ),
    )

    assert [case.name for case in selection.cases] == [
        "same_schema_one",
        "same_schema_two",
    ]
    assert selection.all_schema_match is True
    assert selection.metadata()[0]["retrieval"]["schema_match"] is True
    assert selection.metadata()[0]["prompt_chars"] > 0


def test_same_schema_extraction_fsp_renderer_omits_repeated_schema_contract():
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
    }
    case = _minimal_case("same_schema", schema)
    extraction = ExtractionSpec(
        name="enriched-inline-reasoning-rag-fsp",
        reasoning=ReasoningMode.TOP_LEVEL,
        schema_prompt=SchemaPromptMode.REASONED_PYDANTIC,
        few_shot=FewShotMode.RAG,
    )

    rendered = render_same_schema_extraction_fsp_example(case, extraction)

    assert "INSTRUCCIÓN DEL EJEMPLO:" in rendered
    assert "Extrae los campos solicitados." in rendered
    assert "TEXTO FUENTE DEL EJEMPLO:" in rendered
    assert "SALIDA DEL EJEMPLO:" in rendered
    assert '"reasoning": "EL CAMPO PIDE:' in rendered
    assert "SCHEMA" not in rendered


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


def test_rag_verdict_judge_provider_renders_candidate_verdict_example():
    provider = RagVerdictJudgeFspProvider(cases=[quijote_cultural_literature_case()])

    prompt = provider.build(include_stable_fields=True, include_support_counts=True)

    assert "Caso RAG: cultural_literature_quijote" in prompt
    assert "SCHEMA PYDANTIC DE VEREDICTOS:" in prompt
    assert "title: SingleVerdict[str]" in prompt
    assert "genres: ArrayVerdict[str]" in prompt
    assert "CAMPOS YA CONSENSUADOS:" in prompt
    assert "- author: \"Miguel de Cervantes Saavedra\"" in prompt
    assert "1. (3/4): \"Don Quijote de la Mancha\"" in prompt
    assert "1. (4/4): \"novela\"" in prompt
    assert "Observación: lista vacía en 1/4 trials." in prompt
    assert '"candidate_value": "Don Quijote de la Mancha"' in prompt
    assert '"candidate_value": "tradición caballeresca"' in prompt
    assert '"include": false' in prompt
    assert '"value": "Don Quijote de la Mancha"' in prompt


def test_rag_verdict_judge_provider_projects_overlapping_disputed_fields():
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "genres": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["genres"],
    }
    task = Task(
        id="sample",
        input_text="Texto sobre una novela.",
        instruction="Extrae los géneros literarios.",
        target_schema=schema,
    )
    records = [
        TrialRecord(
            index=0,
            group_name="a",
            extraction=ExtractionSpec(name="a"),
            result=ExtractionResult(output={"genres": ["novela"]}),
        ),
        TrialRecord(
            index=1,
            group_name="b",
            extraction=ExtractionSpec(name="b"),
            result=ExtractionResult(output={"genres": ["realismo"]}),
        ),
    ]
    scope = build_judge_scope(records, schema)
    plan = build_verdict_plan(task, records, scope)
    provider = RagVerdictJudgeFspProvider(cases=[quijote_cultural_literature_case()])

    prompt = provider.build(task=task, plan=plan)

    assert "genres: ArrayVerdict[str]" in prompt
    assert "CAMPO `genres`" in prompt
    assert "title: SingleVerdict[str]" not in prompt
    assert "CAMPO `title`" not in prompt


def test_rag_verdict_judge_provider_can_hide_support_counts():
    provider = RagVerdictJudgeFspProvider(cases=[quijote_cultural_literature_case()])

    prompt = provider.build(include_support_counts=False)

    assert "Trials válidos:" not in prompt
    assert "(3/4)" not in prompt
    assert "1.: \"Don Quijote de la Mancha\"" in prompt
    assert "Observación: lista vacía." in prompt


def test_rag_verdict_judge_provider_can_render_candidate_slots():
    provider = RagVerdictJudgeFspProvider(cases=[quijote_cultural_literature_case()])

    prompt = provider.build(candidate_layout="slots")

    assert "candidates: dict[str, ArrayCandidate[T]]" in prompt
    assert '"candidates": {' in prompt
    assert '"1": {' in prompt
    assert '"candidate_value": "novela"' in prompt
