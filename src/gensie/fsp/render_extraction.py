from __future__ import annotations

import copy
import json
from typing import Any, Mapping

from gensie.fsp.examples import (
    DEFAULT_REASONING_SECTION_LABELS,
    ReasoningSectionLabels,
    StructuredFspCase,
)
from gensie.pipeline.specs import ExtractionSpec, ReasoningMode, SchemaPromptMode
from gensie.schemas.clean import clean_schema_for_prompt
from gensie.schemas.pydantic_render import (
    render_plain_pydantic_schema,
    render_reasoned_pydantic_schema,
)
from gensie.schemas.reasoning import build_inline_reasoning_prompt_schema


def build_extraction_output(
    case: StructuredFspCase,
    reasoning: ReasoningMode | str,
    *,
    labels: ReasoningSectionLabels = DEFAULT_REASONING_SECTION_LABELS,
) -> dict[str, Any]:
    mode = ReasoningMode(reasoning)
    if mode is ReasoningMode.NONE:
        return {
            field_name: copy.deepcopy(field.value)
            for field_name, field in case.field_examples.items()
        }
    if mode is ReasoningMode.TOP_LEVEL:
        output: dict[str, Any] = {}
        for field_name, field in case.field_examples.items():
            if field.reasoning is None:
                continue
            output[field_name] = {
                "reasoning": field.reasoning.render(labels),
                "value": copy.deepcopy(field.value),
            }
        return output
    raise ValueError("FSP RAG examples initially support only none and top_level reasoning")


def render_extraction_fsp_example(
    case: StructuredFspCase,
    extraction: ExtractionSpec,
    *,
    labels: ReasoningSectionLabels = DEFAULT_REASONING_SECTION_LABELS,
) -> str:
    return render_full_extraction_fsp_example(case, extraction, labels=labels)


def render_full_extraction_fsp_example(
    case: StructuredFspCase,
    extraction: ExtractionSpec,
    *,
    labels: ReasoningSectionLabels = DEFAULT_REASONING_SECTION_LABELS,
) -> str:
    schema_heading, schema_content = _render_example_schema(case, extraction)
    output = build_extraction_output(case, extraction.reasoning, labels=labels)
    output_json = json.dumps(output, ensure_ascii=False, indent=2)
    _, schema_description = clean_schema_for_prompt(case.schema)
    description = schema_description or "El schema no proporciona descripción raíz."
    intro = _example_intro(extraction)
    return (
        "EJEMPLO:\n"
        f"{intro}\n\n"
        "INSTRUCCIÓN DEL EJEMPLO:\n"
        f"{case.instruction}\n"
        f"{description}\n\n"
        f"{schema_heading}:\n"
        f"{schema_content.rstrip()}\n\n"
        "TEXTO FUENTE DEL EJEMPLO:\n"
        f"{case.source_text}\n\n"
        "SALIDA DEL EJEMPLO:\n"
        f"{output_json}\n\n"
        "FIN DEL EJEMPLO.\n"
    )


def render_same_schema_extraction_fsp_example(
    case: StructuredFspCase,
    extraction: ExtractionSpec,
    *,
    labels: ReasoningSectionLabels = DEFAULT_REASONING_SECTION_LABELS,
) -> str:
    output = build_extraction_output(case, extraction.reasoning, labels=labels)
    output_json = json.dumps(output, ensure_ascii=False, indent=2)
    return (
        "INSTRUCCIÓN DEL EJEMPLO:\n"
        f"{case.instruction}\n\n"
        "TEXTO FUENTE DEL EJEMPLO:\n"
        f"{case.source_text}\n\n"
        "SALIDA DEL EJEMPLO:\n"
        f"{output_json}\n\n"
        "FIN DEL EJEMPLO.\n"
    )


def _example_intro(extraction: ExtractionSpec) -> str:
    if (
        extraction.reasoning is ReasoningMode.TOP_LEVEL
        and extraction.schema_prompt is SchemaPromptMode.INLINE_REASONING_WRAPPER
    ):
        return "Este ejemplo muestra cómo razonar dentro de cada campo antes de escribir value."
    if extraction.reasoning is ReasoningMode.TOP_LEVEL:
        return (
            "Este ejemplo muestra cómo razonar antes de escribir value: determinar "
            "precisamente qué se requiere (EL CAMPO PIDE), citar TODA la evidencia "
            "textual relacionada (FRAGMENTOS RELEVANTES) y luego razonar sobre el "
            "value (VALOR FINAL)."
        )
    return (
        "Este ejemplo muestra cómo extraer directamente los valores finales del "
        "schema usando solo evidencia del texto fuente."
    )


def _render_example_schema(
    case: StructuredFspCase, extraction: ExtractionSpec
) -> tuple[str, str]:
    mode = extraction.schema_prompt
    if mode is SchemaPromptMode.REASONED_PYDANTIC:
        return "SCHEMA PYDANTIC DEL EJEMPLO", render_reasoned_pydantic_schema(case.schema)
    if mode is SchemaPromptMode.PYDANTIC:
        return "SCHEMA PYDANTIC DEL EJEMPLO", render_plain_pydantic_schema(case.schema)
    if mode is SchemaPromptMode.INLINE_REASONING_WRAPPER:
        return (
            "SCHEMA DEL EJEMPLO",
            json.dumps(
                build_inline_reasoning_prompt_schema(case.schema),
                ensure_ascii=False,
                indent=2,
            ),
        )
    if mode is SchemaPromptMode.CLEAN_JSON_SCHEMA:
        clean_schema, _ = clean_schema_for_prompt(case.schema)
        return "SCHEMA DEL EJEMPLO", json.dumps(clean_schema, ensure_ascii=False, indent=2)
    return "SCHEMA DEL EJEMPLO", json.dumps(case.schema, ensure_ascii=False, indent=2)
