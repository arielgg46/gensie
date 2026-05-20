from __future__ import annotations

import copy
import json
from typing import Any

from gensie.fsp.base import FSPProvider
from gensie.fsp.providers import TextFSPProvider
from gensie.pipeline.specs import ReasoningMode
from gensie.schemas.clean import clean_schema_for_prompt
from gensie.schemas.inspect import JsonDict, deref, schema_type, unwrap_nullable_anyof
from gensie.schemas.pydantic_render import (
    render_deep_reasoned_pydantic_schema,
    render_reasoned_pydantic_schema,
)
from gensie.schemas.reasoning import build_inline_reasoning_prompt_schema

CULTURAL_LITERATURE_FEW_SHOT_INPUT_TEXT = """# Don Quijote de la Mancha

## Introducción
Don Quijote de la Mancha es una novela escrita por el español Miguel de Cervantes Saavedra. Publicada su primera parte con el título de El ingenioso hidalgo don Quijote de la Mancha a comienzos de 1605, es la obra más destacada de la literatura española y una de las principales de la literatura universal. En 1615 apareció su continuación con el título de Segunda parte del ingenioso caballero don Quijote de la Mancha. El Quijote de 1605 se publicó dividido en cuatro partes; pero al aparecer el Quijote de 1615 en calidad de Segunda parte de la obra, quedó revocada de hecho la partición en cuatro secciones del volumen publicado diez años antes por Cervantes.
Es la primera obra genuinamente desmitificadora de la tradición caballeresca y cortés por su tratamiento burlesco. Representa la primera novela moderna y la primera novela polifónica; como tal, ejerció un enorme influjo en toda la narrativa europea. Por considerarse "el mejor trabajo literario jamás escrito", encabezó la lista de las mejores obras literarias de la historia, que se estableció con las votaciones de cien grandes escritores de 54 nacionalidades a petición del Club Noruego del Libro y Bokklubben World Library en 2002; así, fue la única excepción en el estricto orden alfabético que se había dispuesto."""

CULTURAL_LITERATURE_FEW_SHOT_INSTRUCTION = (
    "Extrae los metadatos bibliográficos y temas principales de la obra literaria descrita."
)

CULTURAL_LITERATURE_FEW_SHOT_SCHEMA: JsonDict = {
    "additionalProperties": False,
    "description": "Extracts basic bibliographic metadata and key themes from a book description or encyclopedia entry.\nComplexity: L2 (Explicit Information Retrieval).",
    "properties": {
        "title": {
            "description": "The official title of the literary work",
            "title": "Title",
            "type": "string",
        },
        "author": {
            "description": "The primary author or creator of the work",
            "title": "Author",
            "type": "string",
        },
        "publication_year": {
            "anyOf": [{"type": "integer"}, {"type": "null"}],
            "default": None,
            "description": "The year the work was first published",
            "title": "Publication Year",
        },
        "genres": {
            "description": "Literary genres associated with the work",
            "items": {"type": "string"},
            "title": "Genres",
            "type": "array",
        },
        "key_themes": {
            "description": "Main topics or themes explored in the work",
            "items": {"type": "string"},
            "title": "Key Themes",
            "type": "array",
        },
        "original_language": {
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "default": None,
            "description": "The language in which the work was originally written",
            "title": "Original Language",
        },
    },
    "required": ["title", "author"],
    "title": "LiteraryWork",
    "type": "object",
}

CULTURAL_LITERATURE_FEW_SHOT_OUTPUT: JsonDict = {
    "title": {
        "reasoning": (
            "EL CAMPO PIDE: el título oficial de la obra literaria.\n"
            
            "FRAGMENTOS RELEVANTES: el texto abre con \"# Don Quijote de la Mancha\" y luego repite \"Don Quijote de la Mancha es una novela\". Luego dice \"Publicada su primera parte con el título de El ingenioso hidalgo don Quijote de la Mancha\" y \"En 1615 apareció su continuación con el título de Segunda parte del ingenioso caballero don Quijote de la Mancha\".\n"
            
            "VALOR FINAL: los dos últimos fragmentos mencionan títulos de partes independientes, pero como se pide el título oficial este debe ser el principal usado para la obra completa: Don Quijote de la Mancha."
        ),
        "value": "Don Quijote de la Mancha",
    },
    "author": {
        "reasoning": (
            "EL CAMPO PIDE: el autor principal de la obra.\n"
            
            "FRAGMENTOS RELEVANTES: \"Don Quijote de la Mancha es una novela escrita por el español Miguel de Cervantes Saavedra\".\n"
            
            "VALOR FINAL: es el nombre completo del autor: Miguel de Cervantes Saavedra."
        ),
        "value": "Miguel de Cervantes Saavedra",
    },
    "publication_year": {
        "reasoning": (
            "EL CAMPO PIDE: el año de la primera publicación de la obra (null si no hay suficiente evidencia en el texto).\n"
            
            "FRAGMENTOS RELEVANTES: \"Publicada su primera parte [...] a comienzos de 1605\" y \"En 1615 apareció su continuación\"\n"
            
            "VALOR FINAL: es el año de publicación de la primera parte: 1605."
        ),
        "value": 1605,
    },
    "genres": {
        "reasoning": (
            "EL CAMPO PIDE: géneros literarios asociados con la obra.\n"
            
            "FRAGMENTOS RELEVANTES: \"Don Quijote de la Mancha es una novela\", \"Representa la primera novela moderna y la primera novela polifónica\".\n"
            
            "VALOR FINAL: lista con los géneros mencionados: novela, novela moderna, novela polifónica"
        ),
        "value": ["novela", "novela moderna", "novela polifónica"],
    },
    "key_themes": {
        "reasoning": (
            "EL CAMPO PIDE: tópicos o temas principales explorados en la obra.\n"
            
            "FRAGMENTOS RELEVANTES: \"Es la primera obra genuinamente desmitificadora de la tradición caballeresca y cortés por su tratamiento burlesco\".\n"

            "VALOR FINAL: lista con los elementos mencionados: tradición caballeresca y cortés, tratamiento burlesco."
        ),
        "value": ["tradición caballeresca y cortés", "tratamiento burlesco"],
    },
    "original_language": {
        "reasoning": (
            "EL CAMPO PIDE: el lenguaje en que la obra fue escrita originalmente (null si no hay suficiente evidencia en el texto).\n"
            
            "FRAGMENTOS RELEVANTES: \"escrita por el español Miguel de Cervantes\" y \"es la obra más destacada de la literatura española\".\n"
            
            "VALOR FINAL: se menciona la nacionalidad del autor y se asocia la obra a la literatura española, pero no se afirma explícitamente que su lenguaje original sea el español, por tanto debe ser: null."
        ),
        "value": None,
    },
}


def fixed_reasoning_provider(reasoning: ReasoningMode) -> FSPProvider:
    if reasoning is ReasoningMode.DEEP:
        return TextFSPProvider("deep-cultural-literature", build_enriched_deep_inline_reasoning_few_shot_example())
    if reasoning is ReasoningMode.TOP_LEVEL:
        return TextFSPProvider("enriched-cultural-literature", build_enriched_inline_reasoning_few_shot_example())
    return TextFSPProvider("none", "")


def build_inline_reasoning_few_shot_example() -> str:
    example_schema = build_inline_reasoning_prompt_schema(CULTURAL_LITERATURE_FEW_SHOT_SCHEMA)
    _, schema_description = clean_schema_for_prompt(CULTURAL_LITERATURE_FEW_SHOT_SCHEMA)
    schema_json = json.dumps(example_schema, ensure_ascii=False, indent=2)
    output_json = json.dumps(CULTURAL_LITERATURE_FEW_SHOT_OUTPUT, ensure_ascii=False, indent=2)
    return (
        "EJEMPLO:\n"
        "Este ejemplo muestra cómo razonar dentro de cada campo antes de escribir value.\n\n"
        "INSTRUCCIÓN DEL EJEMPLO:\n"
        f"{CULTURAL_LITERATURE_FEW_SHOT_INSTRUCTION}\n"
        f"{schema_description or 'El schema no proporciona descripción raíz.'}\n\n"
        "SCHEMA DEL EJEMPLO:\n"
        f"{schema_json}\n\n"
        "TEXTO FUENTE DEL EJEMPLO:\n"
        f"{CULTURAL_LITERATURE_FEW_SHOT_INPUT_TEXT}\n\n"
        "SALIDA DEL EJEMPLO:\n"
        f"{output_json}\n\n"
        "FIN DEL EJEMPLO.\n"
    )


def build_enriched_inline_reasoning_few_shot_example() -> str:
    schema = _build_enriched_cultural_few_shot_schema()
    output = _build_enriched_cultural_few_shot_output()
    _, schema_description = clean_schema_for_prompt(schema)
    schema_code = render_reasoned_pydantic_schema(schema)
    output_json = json.dumps(output, ensure_ascii=False, indent=2)
    return (
        "EJEMPLO:\n"
        "Este ejemplo muestra cómo razonar antes de escribir value: determinar precisamente qué se requiere (EL CAMPO PIDE), citar TODA la evidencia textual relacionada (FRAGMENTOS RELEVANTES) y luego razonar sobre el value (VALOR FINAL).\n\n"
        "INSTRUCCIÓN DEL EJEMPLO:\n"
        f"{CULTURAL_LITERATURE_FEW_SHOT_INSTRUCTION} Incluye también el fragmento verbatim completo que evidencia su importancia literaria.\n"
        f"{schema_description or 'El schema no proporciona descripción raíz.'}\n\n"
        "SCHEMA PYDANTIC DEL EJEMPLO:\n"
        f"{schema_code}\n"
        "TEXTO FUENTE DEL EJEMPLO:\n"
        f"{CULTURAL_LITERATURE_FEW_SHOT_INPUT_TEXT}\n\n"
        "SALIDA DEL EJEMPLO:\n"
        f"{output_json}\n\n"
        "FIN DEL EJEMPLO.\n"
    )


def build_enriched_deep_inline_reasoning_few_shot_example() -> str:
    schema = _build_enriched_cultural_few_shot_schema()
    output = _build_deep_cultural_few_shot_output()
    _, schema_description = clean_schema_for_prompt(schema)
    schema_code = render_deep_reasoned_pydantic_schema(schema)
    output_json = json.dumps(output, ensure_ascii=False, indent=2)
    return (
        "EJEMPLO:\n"
        "Este ejemplo muestra razonamiento recursivo: campos, subcampos y "
        "elementos de arrays usan reasoning y value.\n\n"
        "INSTRUCCIÓN DEL EJEMPLO:\n"
        f"{CULTURAL_LITERATURE_FEW_SHOT_INSTRUCTION} Incluye también el fragmento verbatim completo que evidencia su importancia literaria.\n"
        f"{schema_description or 'El schema no proporciona descripción raíz.'}\n\n"
        "SCHEMA PYDANTIC DEL EJEMPLO:\n"
        f"{schema_code}\n"
        "TEXTO FUENTE DEL EJEMPLO:\n"
        f"{CULTURAL_LITERATURE_FEW_SHOT_INPUT_TEXT}\n\n"
        "SALIDA DEL EJEMPLO:\n"
        f"{output_json}\n\n"
        "FIN DEL EJEMPLO.\n"
    )


def _build_enriched_cultural_few_shot_schema() -> JsonDict:
    schema = copy.deepcopy(CULTURAL_LITERATURE_FEW_SHOT_SCHEMA)
    properties = schema.setdefault("properties", {})
    properties["literary_impact_evidence"] = {
        "description": (
            "The complete verbatim source-text fragment that supports the work "
            "being the first modern and polyphonic novel."
        ),
        "title": "Literary Impact Evidence",
        "type": "string",
    }
    required = schema.setdefault("required", [])
    if "literary_impact_evidence" not in required:
        required.append("literary_impact_evidence")
    return schema


def _build_enriched_cultural_few_shot_output() -> JsonDict:
    output = copy.deepcopy(CULTURAL_LITERATURE_FEW_SHOT_OUTPUT)
    output["literary_impact_evidence"] = {
        "reasoning": (
            "El campo pide un fragmento verbatim completo de evidencia, no una etiqueta resumida. "
            "La frase que responde es: \"Representa la primera novela moderna y la primera novela "
            "polifónica; como tal, ejerció un enorme influjo en toda la narrativa europea\"."
        ),
        "value": (
            "Representa la primera novela moderna y la primera novela polifónica; "
            "como tal, ejerció un enorme influjo en toda la narrativa europea."
        ),
    }
    return output


def _build_deep_cultural_few_shot_output() -> JsonDict:
    schema = _build_enriched_cultural_few_shot_schema()
    output = _build_enriched_cultural_few_shot_output()
    properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    deep_output: JsonDict = {}
    for field_name, wrapped_field in output.items():
        field_schema = properties.get(field_name) if isinstance(properties.get(field_name), dict) else {}
        if not isinstance(wrapped_field, dict) or "value" not in wrapped_field:
            continue
        deep_output[field_name] = {
            "reasoning": wrapped_field.get("reasoning", ""),
            "value": _deep_reasoned_example_value(
                wrapped_field["value"],
                field_schema,
                schema,
                path=field_name,
            ),
        }
    return deep_output


def _deep_reasoned_example_value(
    value: Any,
    schema: JsonDict,
    root_schema: JsonDict,
    *,
    path: str,
) -> Any:
    schema, nullable = unwrap_nullable_anyof(schema, root_schema)
    schema = deref(schema, root_schema)
    if value is None:
        return None if nullable else None

    current_type = schema_type(schema)
    if current_type == "array":
        item_schema = schema.get("items") if isinstance(schema.get("items"), dict) else {}
        if not isinstance(value, list):
            return value
        return [
            {
                "reasoning": f"Este item de {path} se incluye porque está apoyado por la evidencia citada en el reasoning del campo.",
                "value": _deep_reasoned_example_value(
                    item, item_schema, root_schema, path=f"{path}[]"
                ),
            }
            for item in value
        ]

    if current_type == "object":
        properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
        if not isinstance(value, dict):
            return value
        return {
            property_name: {
                "reasoning": f"El subcampo {property_name} de {path} se extrae del mismo item y se respalda con el texto fuente.",
                "value": _deep_reasoned_example_value(
                    value[property_name],
                    property_schema,
                    root_schema,
                    path=f"{path}.{property_name}",
                ),
            }
            for property_name, property_schema in properties.items()
            if property_name in value and isinstance(property_schema, dict)
        }

    return value
