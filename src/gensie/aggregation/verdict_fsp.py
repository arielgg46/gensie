from __future__ import annotations

from typing import Protocol

from gensie.fsp.fixed import (
    CULTURAL_LITERATURE_FEW_SHOT_INPUT_TEXT,
    CULTURAL_LITERATURE_FEW_SHOT_INSTRUCTION,
)


class VerdictJudgeFspProvider(Protocol):
    def build(
        self,
        *,
        include_stable_fields: bool = False,
        include_support_counts: bool = True,
    ) -> str:
        pass


class NoVerdictJudgeFspProvider:
    def build(
        self,
        *,
        include_stable_fields: bool = False,
        include_support_counts: bool = True,
    ) -> str:
        del include_stable_fields, include_support_counts
        return ""


class FixedVerdictJudgeFspProvider:
    def build(
        self,
        *,
        include_stable_fields: bool = False,
        include_support_counts: bool = True,
    ) -> str:
        stable_instruction = (
            "No devuelvas campos ya consensuados; esos se reconstruyen fuera de esta llamada.\n"
            if include_stable_fields
            else ""
        )
        stable_block = (
            "CAMPOS YA CONSENSUADOS:\n"
            "- author: \"Miguel de Cervantes Saavedra\"\n\n"
            if include_stable_fields
            else ""
        )
        trial_count_line = "Trials válidos: 4\n\n" if include_support_counts else ""

        return f"""EJEMPLO:
Este ejemplo muestra cómo evaluar cada candidato por separado y devolver candidate_value literalmente.

INSTRUCCIÓN ORIGINAL:
{CULTURAL_LITERATURE_FEW_SHOT_INSTRUCTION}

INSTRUCCIÓN DEL JUEZ:
Emite veredictos solo para estos campos: `title`, `publication_year`, `genres`, `key_themes`, `original_language`, `literary_impact_evidence`.
{stable_instruction}
SCHEMA PYDANTIC DE VEREDICTOS:
Nullable[T] = T | None

class SingleCandidate[T](BaseModel):
    candidate_value: T
    evidence: str

class ArrayCandidate[T](BaseModel):
    candidate_value: T
    evidence: str
    include: bool

class SingleVerdict[T](BaseModel):
    field: str
    candidates: list[SingleCandidate[T]]
    value: T

class ArrayVerdict[T](BaseModel):
    field: str
    candidates: list[ArrayCandidate[T]]

class Output(BaseModel):
    title: SingleVerdict[str]
    publication_year: SingleVerdict[Nullable[int]]
    genres: ArrayVerdict[str]
    key_themes: ArrayVerdict[str]
    original_language: SingleVerdict[Nullable[str]]
    literary_impact_evidence: SingleVerdict[str]

TEXTO FUENTE:
{CULTURAL_LITERATURE_FEW_SHOT_INPUT_TEXT}

{stable_block}VALORES CANDIDATOS POR CAMPO:
{trial_count_line}CAMPO `title`
Formato: SingleVerdict[str]
Valores candidatos, en este orden:
{_candidate_line('"Don Quijote de la Mancha"', "3/4", include_support_counts)}
{_candidate_line('"El ingenioso hidalgo don Quijote de la Mancha"', "1/4", include_support_counts)}

CAMPO `publication_year`
Formato: SingleVerdict[Nullable[int]]
Valores candidatos, en este orden:
{_candidate_line("1605", "2/4", include_support_counts)}
{_candidate_line("1615", "1/4", include_support_counts)}
{_candidate_line("null", "1/4", include_support_counts)}

CAMPO `genres` (lista)
Formato: ArrayVerdict[str]
Elementos candidatos, en este orden:
{_candidate_line('"novela"', "4/4", include_support_counts)}
{_candidate_line('"novela moderna"', "3/4", include_support_counts)}
{_candidate_line('"novela polifónica"', "2/4", include_support_counts)}
{_candidate_line('"tradición caballeresca"', "1/4", include_support_counts)}

CAMPO `key_themes` (lista)
Formato: ArrayVerdict[str]
Elementos candidatos, en este orden:
{_candidate_line('"tratamiento burlesco"', "4/4", include_support_counts)}
{_candidate_line('"tradición caballeresca"', "3/4", include_support_counts)}
{_candidate_line('"tradición cortés"', "2/4", include_support_counts)}
{_candidate_line('"narrativa europea"', "1/4", include_support_counts)}

CAMPO `original_language`
Formato: SingleVerdict[Nullable[str]]
Valores candidatos, en este orden:
{_candidate_line("null", "2/4", include_support_counts)}
{_candidate_line('"español"', "1/4", include_support_counts)}
{_candidate_line('"castellano"', "1/4", include_support_counts)}

CAMPO `literary_impact_evidence`
Formato: SingleVerdict[str]
Valores candidatos, en este orden:
{_candidate_line('"Representa la primera novela moderna y la primera novela polifónica; como tal, ejerció un enorme influjo en toda la narrativa europea."', "2/4", include_support_counts)}
{_candidate_line('"primera novela moderna y la primera novela polifónica"', "1/4", include_support_counts)}
{_candidate_line('"El Quijote influyó mucho en la narrativa europea."', "1/4", include_support_counts)}

SALIDA:
{{
  "title": {{
    "field": "El campo pide el título principal de la obra literaria descrita.",
    "candidates": [
      {{
        "candidate_value": "Don Quijote de la Mancha",
        "evidence": "Fragmentos: \\"# Don Quijote de la Mancha\\" y \\"Don Quijote de la Mancha es una novela de Miguel de Cervantes [...] publicada en dos partes\\". El encabezado y la oración principal presentan este literal como título y sujeto de la obra completa; por eso este candidato debe ser el valor final."
      }},
      {{
        "candidate_value": "El ingenioso hidalgo don Quijote de la Mancha",
        "evidence": "Fragmento: \\"la primera parte se publicó con el título El ingenioso hidalgo don Quijote de la Mancha [...] la segunda parte apareció como El ingenioso caballero don Quijote de la Mancha\\". El fragmento ubica este literal como título de la primera parte, no como título general de la obra completa; por eso no debe elegirse como valor final."
      }}
    ],
    "value": "Don Quijote de la Mancha"
  }},
  "publication_year": {{
    "field": "El campo pide el año de primera publicación de la obra.",
    "candidates": [
      {{
        "candidate_value": 1605,
        "evidence": "Fragmento: \\"Publicada su primera parte [...] a comienzos de 1605\\". El campo pide la primera publicación; 1605 aparece asociado a la primera parte publicada y debe ser el valor final."
      }},
      {{
        "candidate_value": 1615,
        "evidence": "Fragmento: \\"En 1615 apareció su continuación con el título de Segunda parte [...]\\". La cita sitúa 1615 como año de la continuación, no de la primera publicación de la obra; por eso este candidato no debe elegirse."
      }},
      {{
        "candidate_value": null,
        "evidence": "Fragmento: \\"Publicada su primera parte [...] a comienzos de 1605\\". Sí hay evidencia explícita para el año de primera publicación, así que null sería demasiado conservador y debe rechazarse."
      }}
    ],
    "value": 1605
  }},
  "genres": {{
    "field": "El campo pide los géneros literarios asociados explícitamente con la obra.",
    "candidates": [
      {{
        "candidate_value": "novela",
        "evidence": "Fragmento: \\"Don Quijote de la Mancha es una novela de Miguel de Cervantes\\". La palabra \\"novela\\" aparece en una oración definitoria sobre la obra, por lo que funciona como género o forma literaria y debe incluirse.",
        "include": true
      }},
      {{
        "candidate_value": "novela moderna",
        "evidence": "Fragmento: \\"Representa la primera novela moderna y la primera novela polifónica\\". El texto clasifica explícitamente la obra como novela moderna, así que este candidato pertenece al array final.",
        "include": true
      }},
      {{
        "candidate_value": "novela polifónica",
        "evidence": "Fragmento: \\"Representa la primera novela moderna y la primera novela polifónica\\". La expresión aparece como clasificación literaria de la obra; por eso debe incluirse.",
        "include": true
      }},
      {{
        "candidate_value": "tradición caballeresca",
        "evidence": "Fragmento: \\"desmitificadora de la tradición caballeresca y cortés por su tratamiento burlesco\\". El contexto presenta la tradición caballeresca como tradición desmitificada, no como género formal de la obra; por eso no debe incluirse en géneros.",
        "include": false
      }}
    ]
  }},
  "key_themes": {{
    "field": "El campo pide los temas principales explorados o tratados por la obra.",
    "candidates": [
      {{
        "candidate_value": "tratamiento burlesco",
        "evidence": "Fragmento: \\"desmitificadora de la tradición caballeresca y cortés por su tratamiento burlesco\\". El texto identifica el tratamiento burlesco como modo central con que la obra aborda esas tradiciones, así que debe incluirse como tema.",
        "include": true
      }},
      {{
        "candidate_value": "tradición caballeresca",
        "evidence": "Fragmento: \\"desmitificadora de la tradición caballeresca y cortés [...]\\". La tradición caballeresca es uno de los objetos temáticos que la obra desmitifica, por lo que debe incluirse.",
        "include": true
      }},
      {{
        "candidate_value": "tradición cortés",
        "evidence": "Fragmento: \\"desmitificadora de la tradición caballeresca y cortés por su tratamiento burlesco\\". La tradición cortés aparece junto a la caballeresca como objeto del tratamiento burlesco, así que también debe incluirse.",
        "include": true
      }},
      {{
        "candidate_value": "narrativa europea",
        "evidence": "Fragmento: \\"ejerció un enorme influjo en toda la narrativa europea\\". La narrativa europea aparece como ámbito de impacto posterior, no como tema explorado por la obra; por eso no debe incluirse.",
        "include": false
      }}
    ]
  }},
  "original_language": {{
    "field": "El campo pide la lengua original de la obra si el texto la afirma explícitamente.",
    "candidates": [
      {{
        "candidate_value": null,
        "evidence": "Fragmento revisado: \\"Don Quijote de la Mancha es una novela de Miguel de Cervantes [...] una de las obras más destacadas de la literatura española y universal\\". El fragmento da contexto autoral y literario, pero no afirma de forma explícita la lengua original; como el campo exige evidencia textual directa, null es el valor más seguro."
      }},
      {{
        "candidate_value": "español",
        "evidence": "Fragmento revisado: \\"Don Quijote de la Mancha es una novela de Miguel de Cervantes [...] una de las obras más destacadas de la literatura española y universal\\". La frase permite inferir contexto cultural, pero no dice \\"lengua original: español\\" ni equivalente; elegir \\"español\\" requeriría conocimiento externo o una inferencia no solicitada, así que este candidato debe rechazarse."
      }},
      {{
        "candidate_value": "castellano",
        "evidence": "Fragmento revisado: \\"novela escrita por el español Miguel de Cervantes Saavedra [...] literatura española y universal\\". El texto permite reconocer contexto español, pero no afirma que la lengua original sea castellano; este candidato requiere conocimiento externo y debe rechazarse."
      }}
    ],
    "value": null
  }},
  "literary_impact_evidence": {{
    "field": "El campo pide un fragmento verbatim completo que evidencie la importancia o impacto literario de la obra.",
    "candidates": [
      {{
        "candidate_value": "Representa la primera novela moderna y la primera novela polifónica; como tal, ejerció un enorme influjo en toda la narrativa europea.",
        "evidence": "Fragmento: \\"Representa la primera novela moderna y la primera novela polifónica; como tal, ejerció un enorme influjo en toda la narrativa europea\\". La cita es verbatim y cubre tanto la innovación formal como el influjo literario, por lo que debe ser el valor final."
      }},
      {{
        "candidate_value": "primera novela moderna y la primera novela polifónica",
        "evidence": "Fragmento: \\"Representa la primera novela moderna y la primera novela polifónica; como tal, ejerció un enorme influjo en toda la narrativa europea\\". Este candidato copia solo una parte del fragmento y pierde la consecuencia sobre el influjo europeo; por eso no satisface el campo completo."
      }},
      {{
        "candidate_value": "El Quijote influyó mucho en la narrativa europea.",
        "evidence": "Fragmento fuente: \\"ejerció un enorme influjo en toda la narrativa europea\\". El candidato es una paráfrasis, no una copia verbatim del texto, y además omite la parte sobre novela moderna y polifónica; debe rechazarse."
      }}
    ],
    "value": "Representa la primera novela moderna y la primera novela polifónica; como tal, ejerció un enorme influjo en toda la narrativa europea."
  }}
}}
FIN DEL EJEMPLO.
"""


def _candidate_line(value: str, support: str, include_support_counts: bool) -> str:
    if include_support_counts:
        return f"- ({support}): {value}"
    return value
