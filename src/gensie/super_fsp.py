from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import Any, Iterable

from gensie.schema_enrichment import FieldInfo, parse_schema_fields


JsonDict = dict[str, Any]


@dataclass(frozen=True)
class SuperFspSubtask:
    """Reusable schema/output slice of the super few-shot example."""

    id: str
    properties: JsonDict
    output: JsonDict
    reasoning: dict[str, str]
    required: tuple[str, ...] = ()
    defs: JsonDict = field(default_factory=dict)


@dataclass(frozen=True)
class SuperFspSubtaskDecision:
    """Why a super FSP subtask was selected for an input schema."""

    subtask_id: str
    field_paths: tuple[str, ...]
    reason: str


SUPER_FSP_INSTRUCTION = (
    "Extrae del texto del ejemplo la información solicitada en todos los campos del schema."
)


SUPER_FSP_INPUT_TEXT = """# Atlas-IE presenta avances en extracción de información científica

Madrid, 14 de abril de 2026. El Instituto Ibérico de IA y la Universidad de Alicante presentaron Atlas-IE, un prototipo diseñado para convertir artículos científicos en español en registros JSON verificables. La demostración se celebró durante una jornada sobre evaluación automática de sistemas de extracción de información. Aunque el trabajo fue presentado por ambas instituciones, la nota subraya que tras la arquitectura de Atlas-IE está Lucía Ferrer, coordinadora del estudio, quien resumió el alcance de la herramienta con una frase: "Atlas-IE identifica entidades, fechas, cifras y relaciones, y devuelve JSON validado contra schemas dinámicos".

El piloto analizó 12.000 artículos de acceso abierto sobre energía, clima y materiales en 8 horas. Según el informe técnico, la precisión fue del 94.1 %, la cobertura del 88.0 % y la latencia media quedó pendiente de cuantificación. El comité de seguimiento calificó el resultado como favorable y recomendó preparar una segunda fase con un presupuesto de 50.000 euros. Ese informe tiene cinco secciones y describe cuatro módulos estables: detector de entidades, normalizador de fechas, extractor de relaciones y verificador de consistencia.

Además de Ferrer, el equipo menciona a Andrés Núñez como responsable de evaluación. Las instituciones participantes son el Instituto Ibérico de IA y la Universidad de Alicante. El análisis de errores destacó dos incidencias: "citas sin fuente", señalada como el problema principal de calidad, y "duplicados leves", sin gravedad adicional indicada.

La nota de prensa añade que los datos de evaluación quedarán bajo protocolo de confidencialidad y que no se publicará un conjunto abierto durante esta fase. Tampoco identifica financiadores externos, DOI del conjunto de datos ni enlace a un repositorio público. Sobre la trazabilidad del proyecto, el dossier solo indica que la primera versión interna del prototipo data de 2021 y que no consta código de registro oficial. El comunicado no aclara si los resultados ya pasaron revisión por pares."""


DEFAULT_SUPER_FSP_SUBTASK_IDS: tuple[str, ...] = (
    "verbatim_answer",
    "direct_string",
    "summary_string",
    "long_verbatim_evidence",
    "enum_classification",
    "date_normalization",
    "numeric_normalization",
    "boolean_inference",
    "nullable_boolean",
    "grounded_null",
    "simple_array",
    "empty_array",
    "entity_array",
    "complex_object_array",
    "nested_numeric_object_array",
    "enum_array",
    "bounded_score",
    "sentinel_pattern",
)


SUPER_FSP_SUBTASKS: dict[str, SuperFspSubtask] = {}


def _register(spec: SuperFspSubtask) -> SuperFspSubtask:
    if spec.id in SUPER_FSP_SUBTASKS:
        raise ValueError(f"Duplicate super FSP subtask id: {spec.id}")
    SUPER_FSP_SUBTASKS[spec.id] = spec
    return spec


_register(
    SuperFspSubtask(
        id="verbatim_answer",
        properties={
            "answer": {
                "description": "The complete verbatim fragment from the source text that answers what Atlas-IE does.",
                "title": "Answer",
                "type": "string",
            }
        },
        required=("answer",),
        output={
            "answer": (
                "Atlas-IE identifica entidades, fechas, cifras y relaciones, y devuelve "
                "JSON validado contra schemas dinámicos"
            )
        },
        reasoning={
            "answer": (
                "Se pide el fragmento verbatim que responde qué hace Atlas-IE. "
                "Fragmentos relevantes del texto fuente: \"Atlas-IE identifica entidades, "
                "fechas, cifras y relaciones, y devuelve JSON validado contra schemas "
                "dinámicos\". Por tanto, el valor debe contener exactamente ese fragmento "
                "citado, sin resumirlo ni reducirlo solo al nombre del sistema."
            )
        },
    )
)

_register(
    SuperFspSubtask(
        id="direct_string",
        properties={
            "system_name": {
                "description": "The short name of the information extraction system.",
                "title": "System Name",
                "type": "string",
            },
            "presentation_city": {
                "description": "The city where the system was presented.",
                "title": "Presentation City",
                "type": "string",
            },
        },
        required=("system_name", "presentation_city"),
        output={"system_name": "Atlas-IE", "presentation_city": "Madrid"},
        reasoning={
            "system_name": (
                "Se pide el nombre corto del sistema de extracción. Fragmentos relevantes "
                "del texto fuente: \"presentaron Atlas-IE, un prototipo diseñado para "
                "convertir artículos científicos en español en registros JSON verificables\". "
                "Por tanto, el valor debe ser \"Atlas-IE\"."
            ),
            "presentation_city": (
                "Se pide la ciudad donde se presentó el sistema. Fragmentos relevantes "
                "del texto fuente: \"Madrid, 14 de abril de 2026\". Por tanto, el valor "
                "debe ser \"Madrid\"."
            ),
        },
    )
)

_register(
    SuperFspSubtask(
        id="summary_string",
        properties={
            "summary": {
                "description": "A concise grounded summary of the scientific news in one sentence.",
                "title": "Summary",
                "type": "string",
            }
        },
        required=("summary",),
        output={
            "summary": (
                "Atlas-IE fue presentado en Madrid como un prototipo de extracción de "
                "información científica en español, con una prueba piloto sobre 12.000 "
                "artículos, precisión del 94.1% y resultado favorable."
            )
        },
        reasoning={
            "summary": (
                "Se pide un resumen breve y grounded de la noticia científica. Fragmentos "
                "relevantes del texto fuente: \"presentaron Atlas-IE\", \"convertir "
                "artículos científicos en español en registros JSON verificables\", "
                "\"analizó 12.000 artículos\", \"precisión fue del 94.1 %\" y \"calificó "
                "el resultado como favorable\". Por tanto, el valor debe condensar esos "
                "hechos principales en una oración sin añadir información externa."
            )
        },
    )
)

_register(
    SuperFspSubtask(
        id="long_verbatim_evidence",
        properties={
            "capability_evidence": {
                "description": "The complete verbatim source-text fragment that answers who is behind Atlas-IE's architecture; do not return only the person's name.",
                "title": "Architecture Lead Evidence",
                "type": "string",
            }
        },
        required=("capability_evidence",),
        output={
            "capability_evidence": (
                "tras la arquitectura de Atlas-IE está Lucía Ferrer, coordinadora del estudio"
            )
        },
        reasoning={
            "capability_evidence": (
                "Se pide el fragmento verbatim completo que responde quién está detrás de "
                "la arquitectura de Atlas-IE; la respuesta corta sería solo la entidad "
                "\"Lucía Ferrer\", pero la description indica no devolver únicamente el "
                "nombre. Fragmentos relevantes del texto fuente: \"tras la arquitectura "
                "de Atlas-IE está Lucía Ferrer, coordinadora del estudio\". Por tanto, "
                "el valor debe contener ese fragmento completo, no solo \"Lucía Ferrer\"."
            )
        },
    )
)

_register(
    SuperFspSubtask(
        id="enum_classification",
        defs={
            "PilotOutcome": {
                "enum": ["POSITIVE", "NEGATIVE", "INCONCLUSIVE"],
                "title": "PilotOutcome",
                "type": "string",
            }
        },
        properties={
            "pilot_outcome": {
                "$ref": "#/$defs/PilotOutcome",
                "description": "Infer the semantic result of the pilot from the evidence.",
            }
        },
        required=("pilot_outcome",),
        output={"pilot_outcome": "POSITIVE"},
        reasoning={
            "pilot_outcome": (
                "Se pide inferir el resultado semántico del piloto usando uno de los "
                "literales del enum. Fragmentos relevantes del texto fuente: \"la precisión "
                "fue del 94.1 %\" y \"El comité de seguimiento calificó el resultado como "
                "favorable\". Por tanto, el valor debe ser el literal exacto \"POSITIVE\"."
            )
        },
    )
)

_register(
    SuperFspSubtask(
        id="date_normalization",
        properties={
            "presentation_date": {
                "anyOf": [{"type": "string"}, {"type": "null"}],
                "default": None,
                "description": "The presentation date normalized as YYYY-MM-DD.",
                "title": "Presentation Date",
            }
        },
        output={"presentation_date": "2026-04-14"},
        reasoning={
            "presentation_date": (
                "Se pide la fecha de presentación normalizada como YYYY-MM-DD. Fragmentos "
                "relevantes del texto fuente: \"Madrid, 14 de abril de 2026\". Por tanto, "
                "el valor debe ser \"2026-04-14\"."
            )
        },
    )
)

_register(
    SuperFspSubtask(
        id="numeric_normalization",
        properties={
            "document_count": {
                "description": "Number of documents processed in the pilot.",
                "title": "Document Count",
                "type": "integer",
            },
            "processing_hours": {
                "description": "Number of hours required by the pilot run.",
                "title": "Processing Hours",
                "type": "number",
            },
            "budget_eur": {
                "anyOf": [{"type": "number"}, {"type": "null"}],
                "default": None,
                "description": "Budget amount in euros as a numeric value without currency text.",
                "title": "Budget Eur",
            },
        },
        required=("document_count", "processing_hours"),
        output={"document_count": 12000, "processing_hours": 8.0, "budget_eur": 50000.0},
        reasoning={
            "document_count": (
                "Se pide el número de documentos o artículos procesados en el piloto. "
                "Fragmentos relevantes del texto fuente: \"El piloto analizó 12.000 "
                "artículos\". Por tanto, el valor debe ser el entero 12000, normalizando "
                "el separador de miles."
            ),
            "processing_hours": (
                "Se pide la duración del procesamiento como número de horas. Fragmentos "
                "relevantes del texto fuente: \"en 8 horas\". Por tanto, el valor debe "
                "ser 8.0, sin incluir la unidad textual."
            ),
            "budget_eur": (
                "Se pide el presupuesto en euros como valor numérico. Fragmentos relevantes "
                "del texto fuente: \"un presupuesto de 50.000 euros\". Por tanto, el "
                "valor debe ser 50000.0, sin la palabra \"euros\" y sin separador de miles."
            ),
        },
    )
)

_register(
    SuperFspSubtask(
        id="boolean_inference",
        properties={
            "has_confidentiality_protocol": {
                "description": "True if the text explicitly mentions a confidentiality protocol for evaluation data.",
                "title": "Has Confidentiality Protocol",
                "type": "boolean",
            },
            "has_open_dataset": {
                "description": "True if the text states that an open dataset will be published.",
                "title": "Has Open Dataset",
                "type": "boolean",
            },
        },
        required=("has_confidentiality_protocol", "has_open_dataset"),
        output={"has_confidentiality_protocol": True, "has_open_dataset": False},
        reasoning={
            "has_confidentiality_protocol": (
                "Se pide indicar si el texto menciona un protocolo de confidencialidad "
                "para los datos de evaluación. Fragmentos relevantes del texto fuente: "
                "\"los datos de evaluación quedarán bajo protocolo de confidencialidad\". "
                "Por tanto, el valor debe ser true."
            ),
            "has_open_dataset": (
                "Se pide indicar si el texto afirma que se publicará un conjunto abierto. "
                "Fragmentos relevantes del texto fuente: \"no se publicará un conjunto "
                "abierto durante esta fase\". Por tanto, el valor debe ser false, porque "
                "la evidencia niega explícitamente la publicación del conjunto abierto."
            ),
        },
    )
)

_register(
    SuperFspSubtask(
        id="nullable_boolean",
        properties={
            "is_peer_reviewed": {
                "anyOf": [{"type": "boolean"}, {"type": "null"}],
                "default": None,
                "description": "True if the text states that the results have already been peer reviewed.",
                "title": "Is Peer Reviewed",
            }
        },
        output={"is_peer_reviewed": None},
        reasoning={
            "is_peer_reviewed": (
                "Se pide determinar si los resultados ya pasaron revisión por pares. "
                "Fragmentos relevantes del texto fuente: \"El comunicado no aclara si "
                "los resultados ya pasaron revisión por pares\". Ese fragmento indica "
                "insuficiencia de evidencia: no permite afirmar true ni false. Por tanto, "
                "el valor debe ser null."
            )
        },
    )
)

_register(
    SuperFspSubtask(
        id="grounded_null",
        properties={
            "exact_public_release_date": {
                "anyOf": [{"type": "string"}, {"type": "null"}],
                "default": None,
                "description": "The exact public release date in DD/MM/YYYY. Return null if only a year or internal version is mentioned.",
                "title": "Exact Public Release Date",
            },
            "dataset_doi": {
                "anyOf": [{"type": "string"}, {"type": "null"}],
                "default": None,
                "description": "The DOI of the dataset. Return null if it is not explicitly in the text.",
                "title": "Dataset Doi",
            },
            "repository_url": {
                "anyOf": [{"type": "string"}, {"type": "null"}],
                "default": None,
                "description": "The public repository URL. Return null if it is not explicitly in the text.",
                "title": "Repository Url",
            },
        },
        output={
            "exact_public_release_date": None,
            "dataset_doi": None,
            "repository_url": None,
        },
        reasoning={
            "exact_public_release_date": (
                "Se pide la fecha pública exacta de lanzamiento en formato DD/MM/YYYY. "
                "Fragmentos relevantes del texto fuente: \"la primera versión interna "
                "del prototipo data de 2021\". Esa evidencia es insuficiente porque solo "
                "menciona un año y además habla de una versión interna, no de un lanzamiento "
                "público exacto. Por tanto, el valor debe ser null."
            ),
            "dataset_doi": (
                "Se pide el DOI del conjunto de datos. Fragmentos relevantes del texto "
                "fuente: \"Tampoco identifica financiadores externos, DOI del conjunto "
                "de datos ni enlace a un repositorio público\". Ese fragmento niega que "
                "el DOI aparezca en el texto. Por tanto, el valor debe ser null."
            ),
            "repository_url": (
                "Se pide la URL de un repositorio público. Fragmentos relevantes del "
                "texto fuente: \"Tampoco identifica financiadores externos, DOI del "
                "conjunto de datos ni enlace a un repositorio público\". Como el texto "
                "no proporciona ninguna URL, el valor debe ser null."
            ),
        },
    )
)

_register(
    SuperFspSubtask(
        id="simple_array",
        properties={
            "researchers": {
                "description": "Names of researchers explicitly mentioned.",
                "items": {"type": "string"},
                "title": "Researchers",
                "type": "array",
            },
            "institutions": {
                "description": "Names of participating institutions explicitly mentioned.",
                "items": {"type": "string"},
                "title": "Institutions",
                "type": "array",
            },
        },
        output={
            "researchers": ["Lucía Ferrer", "Andrés Núñez"],
            "institutions": ["Instituto Ibérico de IA", "Universidad de Alicante"],
        },
        reasoning={
            "researchers": (
                "Se pide una lista simple con los investigadores mencionados. Fragmentos "
                "relevantes del texto fuente: \"Lucía Ferrer, coordinadora del estudio\" "
                "y \"Andrés Núñez como responsable de evaluación\". Por tanto, el array "
                "debe contener exactamente esos dos nombres y no debe incluir instituciones."
            ),
            "institutions": (
                "Se pide una lista simple de instituciones participantes. Fragmentos "
                "relevantes del texto fuente: \"El Instituto Ibérico de IA y la Universidad "
                "de Alicante presentaron Atlas-IE\" y \"Las instituciones participantes "
                "son el Instituto Ibérico de IA y la Universidad de Alicante\". Por tanto, "
                "el array debe contener esas dos instituciones, sin duplicarlas."
            ),
        },
    )
)

_register(
    SuperFspSubtask(
        id="empty_array",
        properties={
            "external_funders": {
                "description": "External funders explicitly named in the news article.",
                "items": {"type": "string"},
                "title": "External Funders",
                "type": "array",
            }
        },
        output={"external_funders": []},
        reasoning={
            "external_funders": (
                "Se pide una lista de financiadores externos nombrados en la noticia. "
                "Fragmentos relevantes del texto fuente: \"Tampoco identifica financiadores "
                "externos, DOI del conjunto de datos ni enlace a un repositorio público\". "
                "Ese fragmento indica que no hay financiadores externos que extraer. Por "
                "tanto, el valor debe ser un array vacío [], no null."
            )
        },
    )
)

_register(
    SuperFspSubtask(
        id="entity_array",
        defs={
            "Entity": {
                "additionalProperties": False,
                "description": "A single named entity mention.",
                "properties": {
                    "text": {
                        "description": "The verbatim text mention from the source.",
                        "title": "Text",
                        "type": "string",
                    },
                    "label": {
                        "$ref": "#/$defs/EntityType",
                        "description": "The category of the entity.",
                    },
                },
                "required": ["text", "label"],
                "title": "Entity",
                "type": "object",
            },
            "EntityType": {
                "enum": ["PERSON", "ORGANIZATION", "LOCATION", "DATE", "EVENT", "MISCELLANEOUS"],
                "title": "EntityType",
                "type": "string",
            },
        },
        properties={
            "entities": {
                "description": "List of named entity mentions with labels.",
                "items": {"$ref": "#/$defs/Entity"},
                "title": "Entities",
                "type": "array",
            }
        },
        output={
            "entities": [
                {"text": "Lucía Ferrer", "label": "PERSON"},
                {"text": "Andrés Núñez", "label": "PERSON"},
                {"text": "Instituto Ibérico de IA", "label": "ORGANIZATION"},
                {"text": "Universidad de Alicante", "label": "ORGANIZATION"},
                {"text": "Madrid", "label": "LOCATION"},
                {"text": "14 de abril de 2026", "label": "DATE"},
            ]
        },
        reasoning={
            "entities": (
                "Se pide una lista de entidades con mención verbatim y etiqueta. Fragmentos "
                "relevantes del texto fuente: \"Madrid, 14 de abril de 2026\", \"El "
                "Instituto Ibérico de IA y la Universidad de Alicante presentaron Atlas-IE\", "
                "\"Lucía Ferrer\" y \"Andrés Núñez\". Por tanto, el array debe contener "
                "las personas Lucía Ferrer y Andrés Núñez con label PERSON, las instituciones "
                "Instituto Ibérico de IA y Universidad de Alicante con label ORGANIZATION, "
                "Madrid con label LOCATION y 14 de abril de 2026 con label DATE."
            )
        },
    )
)

_register(
    SuperFspSubtask(
        id="complex_object_array",
        defs={
            "Finding": {
                "additionalProperties": False,
                "properties": {
                    "name": {
                        "description": "Verbatim name of the evaluated finding.",
                        "title": "Name",
                        "type": "string",
                    },
                    "severity_level": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "default": None,
                        "description": "Severity if explicitly mentioned.",
                        "title": "Severity Level",
                    },
                    "is_primary": {
                        "description": "True if the finding is presented as the main quality problem.",
                        "title": "Is Primary",
                        "type": "boolean",
                    },
                },
                "required": ["name", "is_primary"],
                "title": "Finding",
                "type": "object",
            }
        },
        properties={
            "findings": {
                "description": "Structured list of evaluated quality findings.",
                "items": {"$ref": "#/$defs/Finding"},
                "title": "Findings",
                "type": "array",
            }
        },
        output={
            "findings": [
                {"name": "citas sin fuente", "severity_level": None, "is_primary": True},
                {"name": "duplicados leves", "severity_level": "leve", "is_primary": False},
            ]
        },
        reasoning={
            "findings": (
                "Se pide una lista de hallazgos de calidad, cada uno con nombre, severidad "
                "si aparece e indicador de si es principal. Fragmentos relevantes del texto "
                "fuente: \"citas sin fuente\", \"señalada como el problema principal de "
                "calidad\" y \"duplicados leves, sin gravedad adicional indicada\". Por "
                "tanto, el primer objeto debe tener name \"citas sin fuente\", severity_level "
                "null porque no se da una severidad, e is_primary true porque se marca como "
                "problema principal. El segundo objeto debe tener name \"duplicados leves\", "
                "severity_level \"leve\" por el adjetivo \"leves\", e is_primary false "
                "porque no es el problema principal."
            )
        },
    )
)

_register(
    SuperFspSubtask(
        id="nested_numeric_object_array",
        defs={
            "MetricUnit": {
                "enum": ["documentos", "horas", "porcentaje", "euros", "otro"],
                "title": "MetricUnit",
                "type": "string",
            },
            "MetricMeasurement": {
                "additionalProperties": False,
                "properties": {
                    "name": {
                        "description": "Name of the reported metric.",
                        "title": "Name",
                        "type": "string",
                    },
                    "value": {
                        "anyOf": [{"type": "number"}, {"type": "null"}],
                        "default": None,
                        "description": "Numeric value without unit text.",
                        "title": "Value",
                    },
                    "unit": {
                        "anyOf": [{"$ref": "#/$defs/MetricUnit"}, {"type": "null"}],
                        "default": None,
                        "description": "Normalized unit for the metric.",
                        "title": "Unit",
                    },
                },
                "required": ["name"],
                "title": "MetricMeasurement",
                "type": "object",
            },
        },
        properties={
            "measurements": {
                "description": "Structured list of reported measurements.",
                "items": {"$ref": "#/$defs/MetricMeasurement"},
                "title": "Measurements",
                "type": "array",
            }
        },
        output={
            "measurements": [
                {"name": "documentos procesados", "value": 12000.0, "unit": "documentos"},
                {"name": "tiempo de procesamiento", "value": 8.0, "unit": "horas"},
                {"name": "precisión", "value": 94.1, "unit": "porcentaje"},
                {"name": "cobertura", "value": 88.0, "unit": "porcentaje"},
                {"name": "latencia media", "value": None, "unit": None},
            ]
        },
        reasoning={
            "measurements": (
                "Se pide una lista estructurada de mediciones, con nombre, valor numérico "
                "y unidad normalizada cuando existan. Fragmentos relevantes del texto "
                "fuente: \"analizó 12.000 artículos\", \"en 8 horas\", \"la precisión fue "
                "del 94.1 %\", \"la cobertura del 88.0 %\" y \"la latencia media quedó "
                "pendiente de cuantificación\". Por tanto, el array debe incluir documentos "
                "procesados con value 12000.0 y unit documentos, tiempo de procesamiento "
                "con value 8.0 y unit horas, precisión con value 94.1 y unit porcentaje, "
                "cobertura con value 88.0 y unit porcentaje, y latencia media con value "
                "null y unit null porque se menciona sin valor numérico publicado."
            )
        },
    )
)

_register(
    SuperFspSubtask(
        id="enum_array",
        defs={
            "Capability": {
                "enum": [
                    "ENTITY_DETECTION",
                    "DATE_NORMALIZATION",
                    "RELATION_EXTRACTION",
                    "CONSISTENCY_CHECKING",
                ],
                "title": "Capability",
                "type": "string",
            }
        },
        properties={
            "capabilities": {
                "description": "Capabilities supported by the system, mapped to exact enum literals.",
                "items": {"$ref": "#/$defs/Capability"},
                "title": "Capabilities",
                "type": "array",
            }
        },
        output={
            "capabilities": [
                "ENTITY_DETECTION",
                "DATE_NORMALIZATION",
                "RELATION_EXTRACTION",
                "CONSISTENCY_CHECKING",
            ]
        },
        reasoning={
            "capabilities": (
                "Se pide mapear capacidades del sistema a literales exactos del enum. "
                "Fragmentos relevantes del texto fuente: \"identifica entidades, fechas, "
                "cifras y relaciones\" y \"detector de entidades, normalizador de fechas, "
                "extractor de relaciones y verificador de consistencia\". Por tanto, el "
                "array debe contener ENTITY_DETECTION, DATE_NORMALIZATION, RELATION_EXTRACTION "
                "y CONSISTENCY_CHECKING, usando exactamente esos literales."
            )
        },
    )
)

_register(
    SuperFspSubtask(
        id="bounded_score",
        properties={
            "maturity_score": {
                "description": "Inferred maturity from 1 (early idea) to 10 (production-ready) based on the article.",
                "maximum": 10,
                "minimum": 1,
                "title": "Maturity Score",
                "type": "integer",
            }
        },
        required=("maturity_score",),
        output={"maturity_score": 7},
        reasoning={
            "maturity_score": (
                "Se pide inferir una puntuación de madurez entre 1 y 10. Fragmentos "
                "relevantes del texto fuente: \"prototipo diseñado\", \"El piloto analizó "
                "12.000 artículos\", \"calificó el resultado como favorable\" y \"preparar "
                "una segunda fase\". Por tanto, el valor debe reflejar una madurez "
                "intermedia-alta: no es solo una idea inicial, pero tampoco producción "
                "definitiva. El valor 7 respeta el rango del schema."
            )
        },
    )
)

_register(
    SuperFspSubtask(
        id="sentinel_pattern",
        properties={
            "registry_code": {
                "description": "Official registry code matching the pattern. Use NONE if no explicit code appears.",
                "pattern": "^[A-Z\\-0-9]+$",
                "title": "Registry Code",
                "type": "string",
            }
        },
        required=("registry_code",),
        output={"registry_code": "NONE"},
        reasoning={
            "registry_code": (
                "Se pide un código oficial de registro que cumpla el patrón, usando NONE "
                "si no aparece un código explícito. Fragmentos relevantes del texto fuente: "
                "\"no consta código de registro oficial\". Por tanto, como el campo no "
                "permite null y la description define el sentinel, el valor debe ser "
                "\"NONE\"."
            )
        },
    )
)


def list_super_fsp_subtasks() -> list[str]:
    """Return available subtask ids in stable default order."""

    return list(DEFAULT_SUPER_FSP_SUBTASK_IDS)


def resolve_super_fsp_subtasks(
    subtask_ids: Iterable[str] | None = None,
) -> list[SuperFspSubtask]:
    """Resolve selected subtask ids, preserving caller order."""

    selected_ids = (
        DEFAULT_SUPER_FSP_SUBTASK_IDS if subtask_ids is None else tuple(subtask_ids)
    )
    if not selected_ids:
        raise ValueError("At least one super FSP subtask must be selected.")

    specs: list[SuperFspSubtask] = []
    for subtask_id in selected_ids:
        try:
            specs.append(SUPER_FSP_SUBTASKS[subtask_id])
        except KeyError as exc:
            available = ", ".join(list_super_fsp_subtasks())
            raise ValueError(
                f"Unknown super FSP subtask id: {subtask_id}. Available: {available}"
            ) from exc
    return specs


def build_super_fsp_instruction(subtask_ids: Iterable[str] | None = None) -> str:
    """Return the fixed instruction used by the example."""

    _ = subtask_ids
    return SUPER_FSP_INSTRUCTION


def build_super_fsp_input_text(subtask_ids: Iterable[str] | None = None) -> str:
    """Return the fixed source text used by the example."""

    _ = subtask_ids
    return SUPER_FSP_INPUT_TEXT


def build_super_fsp_schema(subtask_ids: Iterable[str] | None = None) -> JsonDict:
    """Build the final-values JSON Schema for the selected subtasks."""

    props: JsonDict = {}
    defs: JsonDict = {}
    required: list[str] = []

    for spec in resolve_super_fsp_subtasks(subtask_ids):
        for def_name, def_schema in spec.defs.items():
            if def_name in defs and defs[def_name] != def_schema:
                raise ValueError(f"Conflicting $defs entry in super FSP: {def_name}")
            defs[def_name] = copy.deepcopy(def_schema)

        for field_name, field_schema in spec.properties.items():
            if field_name in props:
                raise ValueError(f"Conflicting field in super FSP: {field_name}")
            props[field_name] = copy.deepcopy(field_schema)

        for field_name in spec.required:
            if field_name not in required:
                required.append(field_name)

    schema: JsonDict = {
        "additionalProperties": False,
        "properties": props,
        "required": required,
        "title": "SuperFspExample",
        "type": "object",
    }
    if defs:
        schema["$defs"] = defs
    return schema


def build_super_fsp_reasoned_output(
    subtask_ids: Iterable[str] | None = None,
) -> JsonDict:
    """Build the top-level Reasoned[T] output for the selected subtasks."""

    output: JsonDict = {}
    for spec in resolve_super_fsp_subtasks(subtask_ids):
        for field_name, value in spec.output.items():
            if field_name in output:
                raise ValueError(f"Duplicate output field in super FSP: {field_name}")
            output[field_name] = {
                "reasoning": spec.reasoning[field_name],
                "value": copy.deepcopy(value),
            }
    return output


def render_super_fsp_reasoned_pydantic_schema(
    subtask_ids: Iterable[str] | None = None,
) -> str:
    """Render the dynamically selected example as compact Reasoned[T] Pydantic."""

    from gensie.enriched_inline_reasoning import render_reasoned_pydantic_schema

    return render_reasoned_pydantic_schema(build_super_fsp_schema(subtask_ids))


def build_super_fsp_example(subtask_ids: Iterable[str] | None = None) -> str:
    """Build the few-shot prompt block for selected extraction subtasks."""

    schema_code = render_super_fsp_reasoned_pydantic_schema(subtask_ids)
    output_json = json.dumps(
        build_super_fsp_reasoned_output(subtask_ids),
        ensure_ascii=False,
        indent=2,
    )
    return (
        "EJEMPLO:\n"
        "INSTRUCCIÓN DEL EJEMPLO:\n"
        f"{SUPER_FSP_INSTRUCTION}\n\n"
        "SCHEMA PYDANTIC DEL EJEMPLO:\n"
        f"{schema_code}\n"
        "TEXTO FUENTE DEL EJEMPLO:\n"
        f"{SUPER_FSP_INPUT_TEXT}\n\n"
        "OUTPUT DEL EJEMPLO:\n"
        f"{output_json}\n\n"
        "FIN DEL EJEMPLO.\n"
    )


def build_super_fsp_example_for_schema(
    schema: JsonDict,
    *,
    include_empty_array_hint: bool = True,
) -> str:
    """Build a super FSP example using subtasks selected from an input schema."""

    return build_super_fsp_example(
        select_super_fsp_subtasks_for_schema(
            schema,
            include_empty_array_hint=include_empty_array_hint,
        )
    )


def select_super_fsp_subtasks_for_schema(
    schema: JsonDict,
    *,
    include_empty_array_hint: bool = True,
) -> list[str]:
    """Return selected super FSP subtask ids for an input schema."""

    decisions = explain_super_fsp_subtask_selection(
        schema,
        include_empty_array_hint=include_empty_array_hint,
    )
    return [decision.subtask_id for decision in decisions]


def suggest_super_fsp_subtasks_for_schema(
    schema: JsonDict,
    *,
    include_empty_array_hint: bool = True,
) -> list[str]:
    """Backward-compatible alias for select_super_fsp_subtasks_for_schema."""

    return select_super_fsp_subtasks_for_schema(
        schema,
        include_empty_array_hint=include_empty_array_hint,
    )


def explain_super_fsp_subtask_selection(
    schema: JsonDict,
    *,
    include_empty_array_hint: bool = True,
) -> list[SuperFspSubtaskDecision]:
    """
    Heuristically select useful super FSP subtasks and explain triggering fields.

    The selector is intentionally conservative and stable. Callers can append or
    remove ids afterwards when doing ablations.
    """

    selected: dict[str, set[str]] = {}
    raw_metadata_by_path = _collect_raw_field_metadata(schema)

    def add(subtask_id: str, field_info: FieldInfo, reason: str = "") -> None:
        _ = reason
        selected.setdefault(subtask_id, set()).add(field_info.path)

    fields = parse_schema_fields(schema)
    for field_info in _walk_fields(fields):
        raw_metadata = raw_metadata_by_path.get(field_info.path, {})
        text = _field_search_text(field_info, raw_metadata)
        in_array_item = "[]" in field_info.path
        is_date_like = _mentions_date(text, raw_metadata)
        is_summary_like = _mentions_summary(text)
        is_evidence_like = _mentions_verbatim_evidence(text)
        is_hallucination_trap = _mentions_hallucination_trap(text)
        is_sentinel_like = _mentions_sentinel(text, raw_metadata)

        if field_info.enum is not None:
            add("enum_classification", field_info)

        if field_info.json_type in {"integer", "number"}:
            add("numeric_normalization", field_info)

        if field_info.json_type == "boolean":
            add(
                "nullable_boolean" if field_info.nullable else "boolean_inference",
                field_info,
            )

        if field_info.nullable:
            add("grounded_null", field_info)

        if field_info.minimum is not None or field_info.maximum is not None:
            add("bounded_score", field_info)

        if is_date_like:
            add("date_normalization", field_info)

        if is_summary_like:
            add("summary_string", field_info)

        if field_info.json_type == "string":
            if field_info.name == "answer":
                add("verbatim_answer", field_info)
            elif is_evidence_like and not in_array_item:
                add("long_verbatim_evidence", field_info)
            elif (
                not field_info.nullable
                and not in_array_item
                and field_info.enum is None
                and not is_date_like
                and not is_summary_like
                and not is_hallucination_trap
                and not is_sentinel_like
            ):
                add("direct_string", field_info)

        if is_hallucination_trap:
            add("grounded_null", field_info)

        if is_sentinel_like:
            add("sentinel_pattern", field_info)

        if field_info.json_type == "array":
            if include_empty_array_hint:
                add("empty_array", field_info)
            if field_info.items is None:
                add("simple_array", field_info)
            elif field_info.items.enum is not None:
                add("enum_array", field_info)
            elif field_info.items.json_type == "object":
                if _looks_like_entity_item(field_info.items):
                    add("entity_array", field_info)
                elif _has_numeric_child(field_info.items):
                    add("nested_numeric_object_array", field_info)
                else:
                    add("complex_object_array", field_info)
            else:
                add("simple_array", field_info)

    if not selected and fields:
        selected["direct_string"] = {fields[0].path}

    return [
        SuperFspSubtaskDecision(
            subtask_id=subtask_id,
            field_paths=tuple(sorted(selected[subtask_id])),
            reason=_selection_reason(subtask_id),
        )
        for subtask_id in DEFAULT_SUPER_FSP_SUBTASK_IDS
        if subtask_id in selected
    ]


def _walk_fields(fields: Iterable[FieldInfo]) -> Iterable[FieldInfo]:
    for field_info in fields:
        yield field_info
        if field_info.properties:
            yield from _walk_fields(field_info.properties)
        if field_info.items is not None:
            yield from _walk_fields([field_info.items])


def _collect_raw_field_metadata(schema: JsonDict) -> dict[str, JsonDict]:
    root_schema = schema
    out: dict[str, JsonDict] = {}
    root = _deref_raw_schema(schema, root_schema)
    props = root.get("properties")
    if not isinstance(props, dict):
        return out

    for name, prop_schema in props.items():
        if isinstance(prop_schema, dict):
            _collect_raw_field_metadata_for_node(
                prop_schema,
                root_schema,
                name,
                out,
            )
    return out


def _collect_raw_field_metadata_for_node(
    schema: JsonDict,
    root_schema: JsonDict,
    path: str,
    out: dict[str, JsonDict],
) -> None:
    schema = _deref_raw_schema(schema, root_schema)
    schema, _ = _unwrap_raw_nullable_anyof(schema, root_schema)
    out[path] = schema

    schema_type = schema.get("type")
    if schema_type == "array" and isinstance(schema.get("items"), dict):
        _collect_raw_field_metadata_for_node(
            schema["items"],
            root_schema,
            f"{path}[]",
            out,
        )
    elif schema_type == "object" and isinstance(schema.get("properties"), dict):
        for name, prop_schema in schema["properties"].items():
            if isinstance(prop_schema, dict):
                _collect_raw_field_metadata_for_node(
                    prop_schema,
                    root_schema,
                    f"{path}.{name}",
                    out,
                )


def _deref_raw_schema(schema: JsonDict, root_schema: JsonDict) -> JsonDict:
    ref = schema.get("$ref")
    if not isinstance(ref, str) or not ref.startswith("#/"):
        return schema

    current: Any = root_schema
    for part in ref[2:].split("/"):
        if not isinstance(current, dict):
            return schema
        current = current.get(part)
        if current is None:
            return schema

    if not isinstance(current, dict):
        return schema
    merged = dict(current)
    merged.update({key: value for key, value in schema.items() if key != "$ref"})
    return merged


def _unwrap_raw_nullable_anyof(
    schema: JsonDict,
    root_schema: JsonDict,
) -> tuple[JsonDict, bool]:
    schema = _deref_raw_schema(schema, root_schema)
    any_of = schema.get("anyOf")
    if not isinstance(any_of, list):
        return schema, False

    non_null: list[JsonDict] = []
    has_null = False
    for alt in any_of:
        if not isinstance(alt, dict):
            return schema, False
        alt = _deref_raw_schema(alt, root_schema)
        if alt.get("type") == "null":
            has_null = True
        else:
            non_null.append(alt)

    if has_null and len(non_null) == 1:
        inner = dict(non_null[0])
        for key in ("description", "title", "default", "format", "pattern"):
            if key in schema and key not in inner:
                inner[key] = schema[key]
        return inner, True
    return schema, False


def _field_search_text(field_info: FieldInfo, raw_metadata: JsonDict) -> str:
    parts = [
        field_info.name,
        field_info.path,
        field_info.description or "",
        str(raw_metadata.get("title") or ""),
        str(raw_metadata.get("description") or ""),
        str(raw_metadata.get("format") or ""),
        str(raw_metadata.get("pattern") or ""),
        str(raw_metadata.get("default") or ""),
    ]
    return " ".join(parts).lower()


def _mentions_date(text: str, raw_metadata: JsonDict) -> bool:
    fmt = str(raw_metadata.get("format") or "").lower()
    if fmt in {"date", "date-time"}:
        return True
    return any(
        marker in text
        for marker in (
            "date",
            "fecha",
            "yyyy-mm-dd",
            "dd/mm/yyyy",
            "release",
            "published",
            "publication",
        )
    )


def _mentions_summary(text: str) -> bool:
    return any(
        marker in text
        for marker in (
            "summary",
            "resumen",
            "brief summary",
            "concise",
            "verdict",
            "síntesis",
            "sintesis",
        )
    )


def _mentions_verbatim_evidence(text: str) -> bool:
    if "verbatim" in text and ("fragment" in text or "complete" in text):
        return True
    return any(
        marker in text
        for marker in (
            "source text",
            "evidence",
            "fragment",
            "fragmento",
            "texto fuente",
            "literal",
        )
    )


def _mentions_hallucination_trap(text: str) -> bool:
    return any(
        marker in text
        for marker in (
            "return null",
            "not explicitly",
            "not in text",
            "if only",
            "exact",
            "current",
            "doi",
            "repository",
            "repositorio",
            "checksum",
            "sha256",
            "ceo",
            "discoverer",
            "storage",
        )
    )


def _mentions_sentinel(text: str, raw_metadata: JsonDict) -> bool:
    return bool(raw_metadata.get("pattern")) or any(
        marker in text
        for marker in (
            "none",
            "sentinel",
            "pattern",
            "use none",
            "return none",
            "no explicit code",
            "sin código",
            "sin codigo",
        )
    )


def _looks_like_entity_item(field_info: FieldInfo) -> bool:
    if not field_info.properties:
        return False
    names = {child.name for child in field_info.properties}
    return {"text", "label"}.issubset(names)


def _has_numeric_child(field_info: FieldInfo) -> bool:
    if not field_info.properties:
        return False
    return any(child.json_type in {"integer", "number"} for child in field_info.properties)


def _selection_reason(subtask_id: str) -> str:
    reasons = {
        "verbatim_answer": "Schema contains an answer-style field that should copy a complete source fragment.",
        "direct_string": "Schema contains scalar string fields that need short direct extraction.",
        "summary_string": "Schema contains summary/verdict-style free-text fields.",
        "long_verbatim_evidence": "Schema contains fields asking for verbatim evidence or source fragments.",
        "enum_classification": "Schema contains enum fields that require exact literal classification.",
        "date_normalization": "Schema contains date-like fields or date formats.",
        "numeric_normalization": "Schema contains integer/number fields that may need numeric normalization.",
        "boolean_inference": "Schema contains non-nullable booleans requiring grounded inference.",
        "nullable_boolean": "Schema contains nullable booleans where lack of evidence should remain null.",
        "grounded_null": "Schema contains nullable fields or hallucination-trap descriptions.",
        "simple_array": "Schema contains arrays of simple values.",
        "empty_array": "Schema contains arrays, so the FSP should demonstrate [] for no elements.",
        "entity_array": "Schema contains arrays of entity-like objects with text and label.",
        "complex_object_array": "Schema contains arrays of heterogeneous objects.",
        "nested_numeric_object_array": "Schema contains arrays of objects with numeric subfields.",
        "enum_array": "Schema contains arrays whose items are enum literals.",
        "bounded_score": "Schema contains numeric min/max constraints.",
        "sentinel_pattern": "Schema contains patterns or sentinel-style descriptions.",
    }
    return reasons.get(subtask_id, "Selected from schema shape.")
