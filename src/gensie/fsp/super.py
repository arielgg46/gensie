from __future__ import annotations

import copy
import json
from typing import Any

from gensie.fsp.base import FSPProvider
from gensie.fsp.providers import TextFSPProvider
from gensie.schemas.inspect import JsonDict
from gensie.schemas.pydantic_render import render_reasoned_pydantic_schema

SUPER_FSP_INSTRUCTION = (
    "Extrae del texto del ejemplo la información solicitada en todos los campos del schema."
)

SUPER_FSP_INPUT_TEXT = """# Atlas-IE presenta avances en extracción de información científica

Madrid, 14 de abril de 2026. El Instituto Ibérico de IA y la Universidad de Alicante presentaron Atlas-IE, un prototipo diseñado para convertir artículos científicos en español en registros JSON verificables. La demostración se celebró durante una jornada sobre evaluación automática de sistemas de extracción de información. Aunque el trabajo fue presentado por ambas instituciones, la nota subraya que tras la arquitectura de Atlas-IE está Lucía Ferrer, coordinadora del estudio, quien resumió el alcance de la herramienta con una frase: "Atlas-IE identifica entidades, fechas, cifras y relaciones, y devuelve JSON validado contra schemas dinámicos".

El piloto analizó 12.000 artículos de acceso abierto sobre energía, clima y materiales en 8 horas. Según el informe técnico, la precisión fue del 94.1 %, la cobertura del 88.0 % y la latencia media quedó pendiente de cuantificación. El comité de seguimiento calificó el resultado como favorable y recomendó preparar una segunda fase con un presupuesto de 50.000 euros. Ese informe tiene cinco secciones y describe cuatro módulos estables: detector de entidades, normalizador de fechas, extractor de relaciones y verificador de consistencia.

Además de Ferrer, el equipo menciona a Andrés Núñez como responsable de evaluación. Las instituciones participantes son el Instituto Ibérico de IA y la Universidad de Alicante. El análisis de errores destacó dos incidencias: "citas sin fuente", señalada como el problema principal de calidad, y "duplicados leves", sin gravedad adicional indicada.

La nota de prensa añade que los datos de evaluación quedarán bajo protocolo de confidencialidad y que no se publicará un conjunto abierto durante esta fase. Tampoco identifica financiadores externos, DOI del conjunto de datos ni enlace a un repositorio público. Sobre la trazabilidad del proyecto, el dossier solo indica que la primera versión interna del prototipo data de 2021 y que no consta código de registro oficial. El comunicado no aclara si los resultados ya pasaron revisión por pares."""

SUPER_FSP_SCHEMA: JsonDict = {
    "$defs": {
        "PilotOutcome": {
            "enum": ["POSITIVE", "NEGATIVE", "INCONCLUSIVE"],
            "title": "PilotOutcome",
            "type": "string",
        },
        "Entity": {
            "additionalProperties": False,
            "properties": {
                "name": {"description": "Verbatim entity name.", "type": "string"},
                "role": {"description": "Grounded role in the project.", "type": "string"},
            },
            "required": ["name", "role"],
            "title": "Entity",
            "type": "object",
        },
        "Issue": {
            "additionalProperties": False,
            "properties": {
                "name": {"description": "Verbatim issue label.", "type": "string"},
                "severity": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "description": "Severity or importance if stated.",
                },
            },
            "required": ["name", "severity"],
            "title": "Issue",
            "type": "object",
        },
    },
    "additionalProperties": False,
    "properties": {
        "answer": {
            "description": "The complete verbatim fragment from the source text that answers what Atlas-IE does.",
            "type": "string",
        },
        "system_name": {
            "description": "The short name of the information extraction system.",
            "type": "string",
        },
        "presentation_city": {
            "description": "The city where the system was presented.",
            "type": "string",
        },
        "summary": {
            "description": "A concise grounded summary of the scientific news in one sentence.",
            "type": "string",
        },
        "capability_evidence": {
            "description": "The complete verbatim source-text fragment that answers who is behind Atlas-IE's architecture; do not return only the person's name.",
            "type": "string",
        },
        "pilot_outcome": {
            "$ref": "#/$defs/PilotOutcome",
            "description": "Infer the semantic result of the pilot from the evidence.",
        },
        "presentation_date": {
            "anyOf": [{"type": "string"}, {"type": "null"}],
            "description": "The presentation date normalized as YYYY-MM-DD.",
        },
        "document_count": {
            "description": "Number of articles analyzed by the pilot.",
            "type": "integer",
        },
        "precision_percent": {
            "description": "Precision percentage reported by the technical report.",
            "type": "number",
        },
        "average_latency": {
            "anyOf": [{"type": "number"}, {"type": "null"}],
            "description": "Average latency if quantified.",
        },
        "is_open_dataset": {
            "description": "Whether an open dataset will be published during this phase.",
            "type": "boolean",
        },
        "external_funders": {
            "description": "External funders identified in the source text.",
            "items": {"type": "string"},
            "type": "array",
        },
        "entities": {
            "description": "People and institutions explicitly named in the project.",
            "items": {"$ref": "#/$defs/Entity"},
            "type": "array",
        },
        "stable_modules": {
            "description": "Stable modules described by the report.",
            "items": {"type": "string"},
            "type": "array",
        },
        "issues": {
            "description": "Issues mentioned in the error analysis.",
            "items": {"$ref": "#/$defs/Issue"},
            "type": "array",
        },
        "registry_code": {
            "description": "Official registration code if stated; return null when absent.",
            "anyOf": [{"type": "string"}, {"type": "null"}],
        },
    },
    "required": [
        "answer",
        "system_name",
        "presentation_city",
        "summary",
        "capability_evidence",
        "pilot_outcome",
        "presentation_date",
        "document_count",
        "precision_percent",
        "average_latency",
        "is_open_dataset",
        "external_funders",
        "entities",
        "stable_modules",
        "issues",
        "registry_code",
    ],
    "title": "SuperFspExample",
    "type": "object",
}

SUPER_FSP_OUTPUT: JsonDict = {
    "answer": (
        "Atlas-IE identifica entidades, fechas, cifras y relaciones, y devuelve "
        "JSON validado contra schemas dinámicos"
    ),
    "system_name": "Atlas-IE",
    "presentation_city": "Madrid",
    "summary": (
        "Atlas-IE fue presentado en Madrid como un prototipo de extracción de "
        "información científica en español, con una prueba piloto sobre 12.000 "
        "artículos, precisión del 94.1% y resultado favorable."
    ),
    "capability_evidence": (
        "tras la arquitectura de Atlas-IE está Lucía Ferrer, coordinadora del estudio"
    ),
    "pilot_outcome": "POSITIVE",
    "presentation_date": "2026-04-14",
    "document_count": 12000,
    "precision_percent": 94.1,
    "average_latency": None,
    "is_open_dataset": False,
    "external_funders": [],
    "entities": [
        {"name": "Lucía Ferrer", "role": "coordinadora del estudio"},
        {"name": "Andrés Núñez", "role": "responsable de evaluación"},
        {"name": "Instituto Ibérico de IA", "role": "institución participante"},
        {"name": "Universidad de Alicante", "role": "institución participante"},
    ],
    "stable_modules": [
        "detector de entidades",
        "normalizador de fechas",
        "extractor de relaciones",
        "verificador de consistencia",
    ],
    "issues": [
        {"name": "citas sin fuente", "severity": "problema principal de calidad"},
        {"name": "duplicados leves", "severity": None},
    ],
    "registry_code": None,
}

SUPER_FSP_REASONING: dict[str, str] = {
    "answer": (
        "Se pide el fragmento verbatim que responde qué hace Atlas-IE. "
        "El texto cita directamente: \"Atlas-IE identifica entidades, fechas, cifras y relaciones, "
        "y devuelve JSON validado contra schemas dinámicos\"."
    ),
    "system_name": "El nombre corto aparece explícitamente como Atlas-IE.",
    "presentation_city": "El texto empieza con \"Madrid, 14 de abril de 2026\".",
    "summary": (
        "El resumen se apoya en la presentación de Atlas-IE, el piloto de 12.000 artículos, "
        "la precisión del 94.1 % y la evaluación favorable."
    ),
    "capability_evidence": (
        "El campo pide evidencia verbatim completa; la frase relevante es "
        "\"tras la arquitectura de Atlas-IE está Lucía Ferrer, coordinadora del estudio\"."
    ),
    "pilot_outcome": (
        "El comité calificó el resultado como favorable, por lo que el literal del enum es POSITIVE."
    ),
    "presentation_date": "La fecha \"14 de abril de 2026\" se normaliza como 2026-04-14.",
    "document_count": "El piloto analizó 12.000 artículos; se normaliza a 12000.",
    "precision_percent": "El informe técnico reporta precisión del 94.1 %.",
    "average_latency": "La latencia media quedó pendiente de cuantificación, así que no hay número.",
    "is_open_dataset": "El texto dice que no se publicará un conjunto abierto durante esta fase.",
    "external_funders": "El texto no identifica financiadores externos, así que la lista queda vacía.",
    "entities": "El texto nombra personas e instituciones con roles explícitos.",
    "stable_modules": "El informe describe cuatro módulos estables enumerados en el texto.",
    "issues": "El análisis de errores menciona dos incidencias y solo una gravedad explícita.",
    "registry_code": "El dossier indica que no consta código de registro oficial.",
}


def super_static_provider() -> FSPProvider:
    return TextFSPProvider("super-fsp-atlas-ie", build_super_fsp_example())


def build_super_fsp_schema() -> JsonDict:
    return copy.deepcopy(SUPER_FSP_SCHEMA)


def build_super_fsp_reasoned_output() -> JsonDict:
    return {
        field_name: {
            "reasoning": SUPER_FSP_REASONING[field_name],
            "value": copy.deepcopy(value),
        }
        for field_name, value in SUPER_FSP_OUTPUT.items()
    }


def build_super_fsp_example() -> str:
    schema_code = render_reasoned_pydantic_schema(build_super_fsp_schema())
    output_json = json.dumps(build_super_fsp_reasoned_output(), ensure_ascii=False, indent=2)
    return (
        "EJEMPLO:\n"
        "INSTRUCCIÓN DEL EJEMPLO:\n"
        f"{SUPER_FSP_INSTRUCTION}\n\n"
        "SCHEMA PYDANTIC DEL EJEMPLO:\n"
        f"{schema_code}\n"
        "TEXTO FUENTE DEL EJEMPLO:\n"
        f"{SUPER_FSP_INPUT_TEXT}\n\n"
        "SALIDA DEL EJEMPLO:\n"
        f"{output_json}\n\n"
        "FIN DEL EJEMPLO.\n"
    )
