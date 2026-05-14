from __future__ import annotations

import json
from dataclasses import dataclass

from gensie.fsp.fixed import (
    build_enriched_deep_inline_reasoning_few_shot_example,
    build_enriched_inline_reasoning_few_shot_example,
    build_inline_reasoning_few_shot_example,
)
from gensie.fsp.super import build_super_fsp_example
from gensie.pipeline.context import PipelineContext
from gensie.pipeline.specs import ExtractionSpec, PhaseKind, ReasoningMode
from gensie.prompts.base import PromptBundle, PromptBuilder
from gensie.prompts.system import (
    BASE_EXTRACTION_SYSTEM_PROMPT,
    DEEP_INLINE_REASONING_SYSTEM_PROMPT,
    ENRICHED_SCHEMA_SYSTEM_PROMPT,
    ENRICHED_INLINE_REASONING_SYSTEM_PROMPT,
    INLINE_REASONING_SYSTEM_PROMPT,
)
from gensie.schemas.clean import clean_schema_for_prompt
from gensie.schemas.pydantic_render import (
    render_deep_reasoned_pydantic_schema,
    render_plain_pydantic_schema,
    render_reasoned_pydantic_schema,
)
from gensie.schemas.reasoning import build_inline_reasoning_prompt_schema
from gensie.task import Task


@dataclass(frozen=True)
class ReferenceExtractionPromptBuilder(PromptBuilder):
    def build(
        self, context: PipelineContext, extraction: ExtractionSpec
    ) -> PromptBundle:
        task = context.task
        if extraction.name == "enriched-schema":
            return PromptBundle(
                system=ENRICHED_SCHEMA_SYSTEM_PROMPT,
                user=build_enriched_schema_prompt(task),
                metadata={"prompt_style": "enriched-schema"},
            )

        if extraction.reasoning is ReasoningMode.NONE:
            return PromptBundle(
                system=BASE_EXTRACTION_SYSTEM_PROMPT,
                user=task.get_input_prompt(),
                metadata={"prompt_style": "baseline"},
            )

        if extraction.reasoning is ReasoningMode.DEEP:
            return PromptBundle(
                system=DEEP_INLINE_REASONING_SYSTEM_PROMPT,
                user=build_enriched_deep_inline_reasoning_prompt(task),
                metadata={"prompt_style": "enriched-inline-reasoning-deep"},
            )

        if extraction.name == "inline-reasoning":
            return PromptBundle(
                system=INLINE_REASONING_SYSTEM_PROMPT,
                user=build_inline_reasoning_prompt(task),
                metadata={"prompt_style": "inline-reasoning"},
            )

        if extraction.name == "enriched-inline-reasoning-super-fsp":
            return PromptBundle(
                system=ENRICHED_INLINE_REASONING_SYSTEM_PROMPT,
                user=build_enriched_inline_reasoning_super_fsp_prompt(task),
                metadata={"prompt_style": "enriched-inline-reasoning-super-fsp"},
            )

        verbatim_entity_list = _verbatim_entity_list_from_context(context, extraction)
        prompt_style = (
            "verbatim-entities-enriched-inline-reasoning"
            if PhaseKind.VERBATIM_ENTITIES in extraction.phases
            else "enriched-inline-reasoning"
        )
        return PromptBundle(
            system=ENRICHED_INLINE_REASONING_SYSTEM_PROMPT,
            user=build_enriched_inline_reasoning_prompt(
                task, verbatim_entity_list=verbatim_entity_list
            ),
            metadata={"prompt_style": prompt_style},
        )


def build_inline_reasoning_prompt(task: Task) -> str:
    _, root_description = clean_schema_for_prompt(task.target_schema)
    schema_description = root_description or "No root schema description provided."
    prompt_schema = build_inline_reasoning_prompt_schema(task.target_schema)
    schema_json = json.dumps(prompt_schema, ensure_ascii=False, indent=2)
    few_shot_example = build_inline_reasoning_few_shot_example() + "\n"

    return (
        f"{few_shot_example}"
        "TAREA:\n"
        "Extrae información estructurada del TEXTO FUENTE en español.\n"
        "El SCHEMA muestra el formato generado: cada campo de primer nivel contiene reasoning y value.\n\n"
        "INSTRUCCIÓN:\n"
        f"{task.instruction}\n"
        f"{schema_description}\n\n"
        "FORMATO DE RAZONAMIENTO:\n"
        "- En cada campo, completa primero reasoning y después value.\n"
        "- reasoning debe citar evidencia textual exacta o indicar que no existe, y justificar inferencias, enums, normalizaciones o nulls.\n"
        "- value contiene solo la respuesta final, sin explicaciones.\n"
        "- En objetos, arrays de objetos y arrays de simples, haz un único reasoning para todo el campo y luego rellena value completo. No repitas elementos.\n"
        "- Si un string pide verbatim, usa el span relevante completo cuando sea posible.\n\n"
        "SCHEMA:\n"
        f"{schema_json}\n\n"
        "TEXTO FUENTE:\n"
        f"{task.input_text}"
    )


def build_enriched_inline_reasoning_prompt(
    task: Task,
    *,
    verbatim_entity_list: list[str] | None = None,
) -> str:
    return _build_enriched_inline_reasoning_prompt(
        task,
        few_shot_example=build_enriched_inline_reasoning_few_shot_example() + "\n",
        verbatim_entity_list=verbatim_entity_list,
    )


def build_enriched_schema_prompt(task: Task) -> str:
    _, root_description = clean_schema_for_prompt(task.target_schema)
    schema_description = root_description or "No root schema description provided."
    schema_code = render_plain_pydantic_schema(task.target_schema)

    return (
        "TAREA:\n"
        "Eres un extractor de información estructurada. Debes usar solo evidencia del TEXTO FUENTE.\n"
        "La salida debe seguir el schema de generación: devuelve directamente los valores finales, sin reasoning.\n\n"
        "REGLAS DE EXTRACCIÓN:\n"
        "- Completa todos los campos del schema.\n"
        "- No incluyas campos `reasoning`, `value` ni explicaciones dentro del JSON.\n"
        "- Si no hay evidencia suficiente y el campo permite null, usa null.\n"
        "- Si un array no tiene elementos apoyados por el texto, usa [].\n"
        "- Si un campo pide fragmento verbatim/source text/evidence, copia el fragmento mínimo completo del texto que responde la pregunta; no devuelvas solo la entidad o respuesta normalizada.\n"
        "- En enums, el valor debe coincidir exactamente con una opción del schema.\n"
        "- No uses conocimiento externo.\n\n"
        "INSTRUCCIÓN:\n"
        f"{task.instruction}\n"
        f"{schema_description}\n\n"
        "SCHEMA PYDANTIC:\n"
        f"{schema_code}\n"
        "TEXTO FUENTE:\n"
        f"{task.input_text}"
    )


def build_enriched_inline_reasoning_super_fsp_prompt(task: Task) -> str:
    return _build_enriched_inline_reasoning_prompt(
        task,
        few_shot_example=build_super_fsp_example() + "\n",
        verbatim_entity_list=None,
    )


def build_enriched_deep_inline_reasoning_prompt(task: Task) -> str:
    _, root_description = clean_schema_for_prompt(task.target_schema)
    schema_description = root_description or "No root schema description provided."
    schema_code = render_deep_reasoned_pydantic_schema(task.target_schema)
    few_shot_example = build_enriched_deep_inline_reasoning_few_shot_example() + "\n"

    return (
        "TAREA:\n"
        "Eres un extractor de información estructurada. Debes usar solo evidencia del TEXTO FUENTE.\n"
        "La salida debe seguir el schema de generación: cada campo, subcampo y elemento de array contiene reasoning y value.\n\n"
        "FORMATO DE RAZONAMIENTO RECURSIVO:\n"
        "- Completa todos los campos del schema.\n"
        "- En cada campo y subcampo, escribe primero reasoning y después value.\n"
        "- En arrays, value contiene una lista de Reasoned[item]; cada elemento tiene reasoning propio.\n"
        "- Si un elemento de array es un objeto, su value contiene un objeto cuyos campos también son Reasoned[T].\n"
        "- reasoning debe citar texto exacto del TEXTO FUENTE cuando exista evidencia.\n"
        "- Si no hay evidencia suficiente y value permite null, usa null y explica por qué.\n"
        "- value contiene solo la respuesta final de ese campo, subcampo o elemento, sin explicaciones.\n"
        "- Si un campo pide fragmento verbatim/source text/evidence, copia el fragmento mínimo completo del texto que responde la pregunta; no devuelvas solo la entidad o respuesta normalizada.\n"
        "- Reasoned[T] significa que ese nodo se genera como {\"reasoning\": str, \"value\": T}.\n"
        "- La description de un campo Reasoned[T] describe su value.\n"
        "- Nullable[T] significa que value puede ser null, pero el campo Reasoned[T] no se puede omitir.\n\n"
        f"{few_shot_example}"
        "INSTRUCCIÓN:\n"
        f"{task.instruction}\n"
        f"{schema_description}\n\n"
        "SCHEMA PYDANTIC:\n"
        f"{schema_code}\n"
        "TEXTO FUENTE:\n"
        f"{task.input_text}"
    )


def _build_enriched_inline_reasoning_prompt(
    task: Task,
    *,
    few_shot_example: str,
    verbatim_entity_list: list[str] | None,
) -> str:
    _, root_description = clean_schema_for_prompt(task.target_schema)
    schema_description = root_description or "No root schema description provided."
    schema_code = render_reasoned_pydantic_schema(task.target_schema)
    verbatim_entity_block = _build_verbatim_entity_list_prompt_block(verbatim_entity_list)

    return (
        "TAREA:\n"
        "Eres un extractor de información estructurada. Debes usar solo evidencia del TEXTO FUENTE.\n"
        "La salida debe seguir el schema de generación: cada campo de primer nivel contiene reasoning y value.\n\n"
        "FORMATO DE RAZONAMIENTO:\n"
        "- Completa todos los campos del schema.\n"
        "- En cada campo, escribe primero reasoning y después value.\n"
        "- reasoning debe citar texto exacto del TEXTO FUENTE cuando exista evidencia.\n"
        "- Si no hay evidencia suficiente y value permite null, usa null y explica por qué.\n"
        "- value contiene solo la respuesta final, sin explicaciones.\n"
        "- Si un campo pide fragmento verbatim/source text/evidence, copia el fragmento mínimo completo del texto que responde la pregunta; no devuelvas solo la entidad o respuesta normalizada.\n"
        "- Reasoned[T] significa que el campo se genera como {\"reasoning\": str, \"value\": T}.\n"
        "- La description de un campo Reasoned[T] describe su value.\n"
        "- Nullable[T] significa que value puede ser null, pero el campo no se puede omitir.\n"
        "- En objetos, arrays de objetos y arrays de simples, haz un único reasoning para todo el campo y luego rellena value completo. Razona sobre cada campo de cada elemento. No repitas elementos.\n"
        "- En enums razona explícitamente sobre la pertenencia a cada una de las categorías.\n\n"
        f"{few_shot_example}"
        "INSTRUCCIÓN:\n"
        f"{task.instruction}\n"
        f"{schema_description}\n\n"
        "SCHEMA PYDANTIC:\n"
        f"{schema_code}\n"
        "TEXTO FUENTE:\n"
        f"{task.input_text}\n"
        f"{verbatim_entity_block}"
    )


def _build_verbatim_entity_list_prompt_block(
    verbatim_entity_list: list[str] | None,
) -> str:
    if verbatim_entity_list is None:
        return ""

    entities = _dedupe_prompt_entities(verbatim_entity_list)
    entity_json = json.dumps(entities, ensure_ascii=False, indent=2)
    return (
        "\nENTIDADES PREEXTRAIDAS:\n"
        "Se listan algunas de las entidades verbatim del TEXTO FUENTE. Úsala como ayuda de grounding, pero decide la respuesta final con el TEXTO FUENTE completo y el schema, no es infalible:\n"
        f"{entity_json}"
    )


def _dedupe_prompt_entities(verbatim_entity_list: list[str]) -> list[str]:
    seen: set[str] = set()
    entities: list[str] = []
    for item in verbatim_entity_list:
        if not isinstance(item, str):
            continue
        entity = item.strip()
        if not entity or entity in seen:
            continue
        seen.add(entity)
        entities.append(entity)
    return entities


def _verbatim_entity_list_from_context(
    context: PipelineContext, extraction: ExtractionSpec
) -> list[str] | None:
    if PhaseKind.VERBATIM_ENTITIES not in extraction.phases:
        return None

    raw_entities = context.metadata.get("verbatim_entity_list")
    if not isinstance(raw_entities, list):
        return []
    return [item for item in raw_entities if isinstance(item, str)]
