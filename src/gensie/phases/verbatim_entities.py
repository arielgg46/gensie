from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from typing import Any, Mapping

from gensie.phases.base import PhaseResult, PipelinePhase
from gensie.pipeline.context import PipelineContext
from gensie.runtime import ChatClient, ChatMessage, ChatRequest


JsonDict = dict[str, Any]

VERBATIM_ENTITY_FIELDS: tuple[str, ...] = (
    "personas",
    "organizaciones",
    "fechas",
    "lugares",
    "otros",
)

VERBATIM_ENTITY_SYSTEM_PROMPT = (
    "Eres un extractor de entidades verbatim para textos en español. "
    "Usa solo evidencia literal del texto fuente."
)

VERBATIM_ENTITY_SCHEMA_NAME = "verbatim_entity_extraction"

_VERBATIM_ENTITY_SCHEMA: JsonDict = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "personas": {
            "type": "array",
            "description": (
                "Person names, fictional characters, or named human groups copied "
                "verbatim from the source text."
            ),
            "items": {"type": "string"},
        },
        "organizaciones": {
            "type": "array",
            "description": (
                "Organizations, institutions, companies, agencies, parties, teams, "
                "or named collectives copied verbatim from the source text."
            ),
            "items": {"type": "string"},
        },
        "fechas": {
            "type": "array",
            "description": (
                "Dates, years, and periods copied verbatim "
                "from the source text; do not normalize them."
            ),
            "items": {"type": "string"},
        },
        "lugares": {
            "type": "array",
            "description": (
                "Places, cities, countries, regions, facilities, geographic names, "
                "or location mentions copied verbatim from the source text."
            ),
            "items": {"type": "string"},
        },
        "otros": {
            "type": "array",
            "description": (
                "Other named or salient entities copied verbatim from the source "
                "text that are not persons, organizations, dates, or places."
            ),
            "items": {"type": "string"},
        },
    },
    "required": list(VERBATIM_ENTITY_FIELDS),
}


def build_verbatim_entity_schema() -> JsonDict:
    return copy.deepcopy(_VERBATIM_ENTITY_SCHEMA)


def build_verbatim_entity_prompt(input_text: str) -> str:
    return (
        "TAREA:\n"
        "Extrae entidades verbatim del TEXTO FUENTE y clasifícalas.\n\n"
        "REGLAS:\n"
        "- Copia cada entidad exactamente como aparece en el texto fuente.\n"
        "- No normalices fechas, nombres, siglas, títulos ni lugares.\n"
        "- No traduzcas, no reformules y no completes con conocimiento externo.\n"
        "- No inventes entidades implícitas.\n"
        "- Si una categoría no tiene evidencia, devuelve una lista vacía [].\n"
        "- No repitas el mismo string dentro de una categoría.\n"
        "- Usa 'otros' solo para entidades que no sean personas, organizaciones, "
        "fechas o lugares.\n\n"
        "CATEGORÍAS:\n"
        "- personas: nombres de personas o personajes.\n"
        "- organizaciones: instituciones, empresas, organismos, partidos, equipos "
        "o colectivos nombrados.\n"
        "- fechas: fechas o años concretos (NO expresiones inconcretas como 'el año pasado', SÍ '2001').\n"
        "- lugares: ciudades, países, regiones, instalaciones o ubicaciones.\n"
        "- otros: obras, productos, medicamentos, eventos, leyes, sistemas, "
        "títulos u otras entidades nombradas.\n\n"
        "TEXTO FUENTE:\n"
        f"{input_text}"
    )


def build_verbatim_entity_response_format() -> JsonDict:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": VERBATIM_ENTITY_SCHEMA_NAME,
            "schema": build_verbatim_entity_schema(),
            "strict": True,
        },
    }


def parse_verbatim_entity_response(content: str | Mapping[str, Any]) -> JsonDict:
    raw = json.loads(content) if isinstance(content, str) else dict(content)
    return normalize_verbatim_entities(raw)


def normalize_verbatim_entities(value: Mapping[str, Any]) -> JsonDict:
    normalized: JsonDict = {}
    for field_name in VERBATIM_ENTITY_FIELDS:
        items = value.get(field_name, [])
        if not isinstance(items, list):
            items = []

        seen: set[str] = set()
        cleaned: list[str] = []
        for item in items:
            if not isinstance(item, str):
                continue
            text = item.strip()
            if not text or text in seen:
                continue
            seen.add(text)
            cleaned.append(text)
        normalized[field_name] = cleaned
    return normalized


def flatten_verbatim_entities(value: Mapping[str, Any]) -> list[str]:
    normalized = normalize_verbatim_entities(value)
    seen: set[str] = set()
    flattened: list[str] = []
    for field_name in VERBATIM_ENTITY_FIELDS:
        for item in normalized[field_name]:
            if item in seen:
                continue
            seen.add(item)
            flattened.append(item)
    return flattened


@dataclass(frozen=True)
class VerbatimEntitiesPhase(PipelinePhase):
    chat_client: ChatClient
    temperature: float = 0.0
    name: str = "verbatim_entities"

    def run(
        self, context: PipelineContext, current: Mapping[str, Any] | None = None
    ) -> PhaseResult:
        request = ChatRequest(
            model=context.model,
            messages=(
                ChatMessage(role="system", content=VERBATIM_ENTITY_SYSTEM_PROMPT),
                ChatMessage(
                    role="user",
                    content=build_verbatim_entity_prompt(context.task.input_text),
                ),
            ),
            response_format=build_verbatim_entity_response_format(),
            temperature=self.temperature,
            metadata={"phase": self.name},
        )
        verbatim_entities = normalize_verbatim_entities({})
        verbatim_entity_list: list[str] = []
        metadata: dict[str, Any] = {}

        try:
            response = self.chat_client.complete(request)
            context.usage.add(response.usage)
            verbatim_entities = parse_verbatim_entity_response(response.content)
            verbatim_entity_list = flatten_verbatim_entities(verbatim_entities)
        except Exception as exc:
            metadata["error"] = str(exc) or repr(exc)

        metadata["entity_count"] = len(verbatim_entity_list)
        return PhaseResult(
            name=self.name,
            data={
                "verbatim_entities": verbatim_entities,
                "verbatim_entity_list": verbatim_entity_list,
            },
            metadata=metadata,
        )
