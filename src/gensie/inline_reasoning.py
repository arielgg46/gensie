import copy
import json
from typing import Any

from gensie.prompting import clean_schema_for_prompt
from gensie.task import Task


INLINE_REASONING_SYSTEM_PROMPT = (
    "Eres un motor experto de extracción de información en español.\n"
    "Devuelve solo el objeto JSON requerido por el schema.\n"
    "Usa solo evidencia del texto fuente.\n"
    "Para cada campo de primer nivel, escribe tu razonamiento antes del valor final.\n"
    "En cada reasoning, cita texto exacto cuando exista evidencia, o indica que no hay evidencia textual."
)


INLINE_REASONING_DESCRIPTION = (
    "Razonamiento sobre campo: cita texto exacto o indica "
    "que no hay evidencia, justifica inferencia/enum/normalización/null, explica la respuesta final."
    "Luego pon la respuesta final en value."
)

INLINE_PROMPT_SCHEMA_FINAL_VALUES = "final-values"
INLINE_PROMPT_SCHEMA_REASONING_WRAPPER = "reasoning-wrapper"
INLINE_PROMPT_SCHEMA_VIEW = INLINE_PROMPT_SCHEMA_REASONING_WRAPPER
INCLUDE_INLINE_REASONING_FEW_SHOT = True


CULTURAL_LITERATURE_FEW_SHOT_INPUT_TEXT = """# Don Quijote de la Mancha

## Introducción
Don Quijote de la Mancha es una novela escrita por el español Miguel de Cervantes Saavedra. Publicada su primera parte con el título de El ingenioso hidalgo don Quijote de la Mancha a comienzos de 1605, es la obra más destacada de la literatura española y una de las principales de la literatura universal. En 1615 apareció su continuación con el título de Segunda parte del ingenioso caballero don Quijote de la Mancha. El Quijote de 1605 se publicó dividido en cuatro partes; pero al aparecer el Quijote de 1615 en calidad de Segunda parte de la obra, quedó revocada de hecho la partición en cuatro secciones del volumen publicado diez años antes por Cervantes.
Es la primera obra genuinamente desmitificadora de la tradición caballeresca y cortés por su tratamiento burlesco. Representa la primera novela moderna y la primera novela polifónica; como tal, ejerció un enorme influjo en toda la narrativa europea. Por considerarse «el mejor trabajo literario jamás escrito», encabezó la lista de las mejores obras literarias de la historia, que se estableció con las votaciones de cien grandes escritores de 54 nacionalidades a petición del Club Noruego del Libro y Bokklubben World Library en 2002; así, fue la única excepción en el estricto orden alfabético que se había dispuesto."""


CULTURAL_LITERATURE_FEW_SHOT_INSTRUCTION = (
    "Extrae los metadatos bibliográficos y temas principales de la obra literaria descrita."
)


CULTURAL_LITERATURE_FEW_SHOT_SCHEMA: dict[str, Any] = {
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
            "description": "Literary genres associated with the work (e.g., 'Science Fiction', 'Romance')",
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


CULTURAL_LITERATURE_FEW_SHOT_OUTPUT: dict[str, Any] = {
    "title": {
        "reasoning": (
            "El campo pide el título oficial de la obra literaria. El texto abre con "
            "\"# Don Quijote de la Mancha\" y luego repite \"Don Quijote de la Mancha es una novela\". "
            "Aunque también aparece \"El ingenioso hidalgo don Quijote de la Mancha\", ese fragmento se presenta como "
            "\"el título\" de la primera parte publicada en 1605, no como el nombre general de la obra descrita. "
            "Por eso el valor final debe ser el título principal usado para la obra completa."
        ),
        "value": "Don Quijote de la Mancha",
    },
    "author": {
        "reasoning": (
            "El campo pide el autor principal. La evidencia textual directa es "
            "\"es una novela escrita por el español Miguel de Cervantes Saavedra\". "
            "Esa frase identifica explícitamente a Miguel de Cervantes Saavedra como quien escribió la obra, "
            "así que ese es el valor final."
        ),
        "value": "Miguel de Cervantes Saavedra",
    },
    "publication_year": {
        "reasoning": (
            "El campo pide el año de primera publicación. El texto dice "
            "\"Publicada su primera parte ... a comienzos de 1605\" y más adelante menciona "
            "\"En 1615 apareció su continuación\". Como se pide la primera publicación, la evidencia relevante es 1605; "
            "se normaliza como entero porque el schema permite integer."
        ),
        "value": 1605,
    },
    "genres": {
        "reasoning": (
            "El campo pide géneros literarios asociados con la obra. El texto da evidencia explícita en "
            "\"es una novela\", \"Representa la primera novela moderna\" y \"la primera novela polifónica\". "
            "Esos fragmentos respaldan una lista breve de etiquetas de género o tipo literario sin añadir categorías externas."
        ),
        "value": ["novela", "novela moderna", "novela polifónica"],
    },
    "key_themes": {
        "reasoning": (
            "El campo pide temas principales. La evidencia aparece en "
            "\"desmitificadora de la tradición caballeresca y cortés por su tratamiento burlesco\". "
            "De esa frase se extraen los temas apoyados directamente: tradición caballeresca, tradición cortés y tratamiento burlesco."
        ),
        "value": [
            "tradición caballeresca",
            "tradición cortés",
            "tratamiento burlesco",
        ],
    },
    "original_language": {
        "reasoning": (
            "El campo pide la lengua original de la obra. El texto dice que es una obra de la "
            "\"literatura española\" y que fue escrita por \"el español Miguel de Cervantes Saavedra\", "
            "pero no afirma explícitamente que la lengua original sea el español o castellano. "
            "Como el schema permite null y la respuesta debe estar grounded en el texto, el valor final debe ser null."
        ),
        "value": None,
    },
}


def build_inline_reasoning_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Wrap each top-level field as {reasoning, value} for constrained generation."""
    original = copy.deepcopy(schema)
    properties = original.get("properties")
    if original.get("type") != "object" or not isinstance(properties, dict):
        raise ValueError("Inline reasoning requires a root object schema with properties.")

    wrapped_properties = {}
    for field_name, field_schema in properties.items():
        wrapped_properties[field_name] = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "reasoning": {
                    "type": "string",
                    "description": INLINE_REASONING_DESCRIPTION,
                },
                "value": field_schema,
            },
            "required": ["reasoning", "value"],
        }

    reasoning_schema: dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "properties": wrapped_properties,
        "required": list(properties.keys()),
    }

    if "$defs" in original:
        reasoning_schema["$defs"] = original["$defs"]
    if "description" in original:
        reasoning_schema["description"] = (
            "Inline reasoning wrapper for: " + str(original["description"])
        )
    if "title" in original:
        reasoning_schema["title"] = str(original["title"]) + "InlineReasoning"

    return reasoning_schema


def build_inline_reasoning_prompt_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Build the prompt-visible schema with top-level reasoning/value wrappers."""
    clean_schema, _ = clean_schema_for_prompt(schema)
    properties = clean_schema.get("properties")
    if clean_schema.get("type") != "object" or not isinstance(properties, dict):
        raise ValueError("Inline reasoning prompt schema requires a root object schema.")

    wrapped_properties = {}
    for field_name, field_schema in properties.items():
        value_schema = copy.deepcopy(field_schema)
        field_description = value_schema.pop("description", None)
        wrapped_field: dict[str, Any] = {
            "type": "object",
            "properties": {
                "reasoning": {"type": "string"},
                "value": value_schema,
            },
        }
        if field_description:
            wrapped_field["description"] = field_description
        wrapped_properties[field_name] = wrapped_field

    prompt_schema: dict[str, Any] = {
        "type": "object",
        "properties": wrapped_properties,
    }
    if "$defs" in clean_schema:
        prompt_schema["$defs"] = clean_schema["$defs"]
    return prompt_schema


def build_inline_reasoning_few_shot_example() -> str:
    example_schema = build_inline_reasoning_prompt_schema(
        CULTURAL_LITERATURE_FEW_SHOT_SCHEMA
    )
    _, schema_description = clean_schema_for_prompt(CULTURAL_LITERATURE_FEW_SHOT_SCHEMA)
    schema_json = json.dumps(example_schema, ensure_ascii=False, indent=2)
    output_json = json.dumps(
        CULTURAL_LITERATURE_FEW_SHOT_OUTPUT, ensure_ascii=False, indent=2
    )
    return (
        "EJEMPLO:\n"
        "Este ejemplo muestra cómo razonar dentro de cada campo antes de escribir value.\n\n"
        "INSTRUCCIÓN DEL EJEMPLO:\n"
        f"{CULTURAL_LITERATURE_FEW_SHOT_INSTRUCTION}\n"
        f"{schema_description or 'No root schema description provided.'}\n\n"
        "SCHEMA DEL EJEMPLO:\n"
        f"{schema_json}\n\n"
        "TEXTO FUENTEDEL EJEMPLO:\n"
        f"{CULTURAL_LITERATURE_FEW_SHOT_INPUT_TEXT}\n\n"
        "OUTPUT DEL EJEMPLO:\n"
        f"{output_json}\n\n"
        "FIN DEL EJEMPLO.\n"
    )


def build_inline_reasoning_prompt(task: Task) -> str:
    clean_schema, root_description = clean_schema_for_prompt(task.target_schema)
    schema_description = root_description or "No root schema description provided."
    if INLINE_PROMPT_SCHEMA_VIEW == INLINE_PROMPT_SCHEMA_FINAL_VALUES:
        prompt_schema = clean_schema
        schema_note = "El SCHEMA describe los valores finales; la generación envuelve cada campo de primer nivel como {reasoning, value}."
    elif INLINE_PROMPT_SCHEMA_VIEW == INLINE_PROMPT_SCHEMA_REASONING_WRAPPER:
        prompt_schema = build_inline_reasoning_prompt_schema(task.target_schema)
        schema_note = "El SCHEMA muestra el formato generado: cada campo de primer nivel contiene reasoning y value."
    else:
        raise ValueError(f"Unknown inline prompt schema view: {INLINE_PROMPT_SCHEMA_VIEW}")
    schema_json = json.dumps(prompt_schema, ensure_ascii=False, indent=2)
    few_shot_example = (
        build_inline_reasoning_few_shot_example() + "\n"
        if INCLUDE_INLINE_REASONING_FEW_SHOT
        else ""
    )

    return (
        f"{few_shot_example}"
        "TAREA:\n"
        "Extrae información estructurada del TEXTO FUENTE en español.\n"
        f"{schema_note}\n\n"
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


def unwrap_inline_reasoning_output(
    raw_output: dict[str, Any], original_schema: dict[str, Any]
) -> dict[str, Any]:
    """Return the official GenSIE output by keeping only top-level wrapper values."""
    properties = original_schema.get("properties")
    if not isinstance(properties, dict):
        raise ValueError("Original schema has no root properties.")
    if not isinstance(raw_output, dict):
        raise ValueError("Inline reasoning output must be a JSON object.")

    output: dict[str, Any] = {}
    for field_name in properties:
        wrapped_field = raw_output.get(field_name)
        if not isinstance(wrapped_field, dict) or "value" not in wrapped_field:
            raise ValueError(f"Missing inline reasoning value for field: {field_name}")
        output[field_name] = wrapped_field["value"]

    return output
