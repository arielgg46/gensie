from __future__ import annotations

from typing import Protocol

from gensie.aggregation.judge_scope import JudgeScope
from gensie.fsp.fixed import (
    CULTURAL_LITERATURE_FEW_SHOT_INPUT_TEXT,
    CULTURAL_LITERATURE_FEW_SHOT_INSTRUCTION,
)


class JudgeFspProvider(Protocol):
    def build(
        self,
        scope: JudgeScope,
        *,
        include_stable_fields: bool = False,
        include_support_counts: bool = True,
    ) -> str:
        pass


class NoJudgeFspProvider:
    def build(
        self,
        scope: JudgeScope,
        *,
        include_stable_fields: bool = False,
        include_support_counts: bool = True,
    ) -> str:
        del scope, include_stable_fields, include_support_counts
        return ""


class FixedJudgeFspProvider:
    def build(
        self,
        scope: JudgeScope,
        *,
        include_stable_fields: bool = False,
        include_support_counts: bool = True,
    ) -> str:
        del scope
        instruction = (
            f"{CULTURAL_LITERATURE_FEW_SHOT_INSTRUCTION} "
            "Incluye también el fragmento verbatim completo que evidencia su importancia literaria."
        )
        no_stable_instruction = (
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

        title_main = _candidate_ref(
            "`Don Quijote de la Mancha`", "3/4", include_support_counts
        )
        title_part = _candidate_ref(
            "`El ingenioso hidalgo don Quijote de la Mancha`",
            "1/4",
            include_support_counts,
        )
        year_1605 = _candidate_ref("1605", "2/4", include_support_counts)
        year_1615 = _candidate_ref("1615", "1/4", include_support_counts)
        year_null = _candidate_ref("null", "1/4", include_support_counts)
        genre_novel = _candidate_ref("`novela`", "4/4", include_support_counts)
        genre_modern = _candidate_ref(
            "`novela moderna`", "3/4", include_support_counts
        )
        genre_polyphonic = _candidate_ref(
            "`novela polifónica`", "2/4", include_support_counts
        )
        genre_chivalric = _candidate_ref(
            "`tradición caballeresca`", "1/4", include_support_counts
        )
        theme_burlesque = _candidate_ref(
            "`tratamiento burlesco`", "4/4", include_support_counts
        )
        theme_chivalric = _candidate_ref(
            "`tradición caballeresca`", "3/4", include_support_counts
        )
        theme_courtly = _candidate_ref(
            "`tradición cortés`", "2/4", include_support_counts
        )
        theme_european = _candidate_ref(
            "`narrativa europea`", "1/4", include_support_counts
        )
        language_null = _candidate_ref("null", "2/4", include_support_counts)
        language_spanish = _candidate_ref("`español`", "1/4", include_support_counts)
        language_castilian = _candidate_ref(
            "`castellano`", "1/4", include_support_counts
        )
        evidence_full = _candidate_ref(
            "de frase completa", "2/4", include_support_counts
        )
        evidence_partial = _candidate_ref(
            "`primera novela moderna y la primera novela polifónica`",
            "1/4",
            include_support_counts,
        )
        evidence_paraphrase = _candidate_ref(
            "`El Quijote influyó mucho en la narrativa europea`",
            "1/4",
            include_support_counts,
        )

        return f"""EJEMPLO:
Este ejemplo muestra cómo citar evidencia, razonar antes de escribir value y copiar fragmentos verbatim largos cuando un campo lo pide."

INSTRUCCIÓN ORIGINAL:
{instruction}

INSTRUCCIÓN DEL JUEZ:
Razona y da un veredicto solo sobre estos campos: `title`, `publication_year`, `genres`, `key_themes`, `original_language`, `literary_impact_evidence`.
{no_stable_instruction}
SCHEMA PYDANTIC:
class LiteraryWorkJudge(BaseModel):
    title: Reasoned[str]
    publication_year: Reasoned[Nullable[int]]
    genres: Reasoned[list[str]]
    key_themes: Reasoned[list[str]]
    original_language: Reasoned[Nullable[str]]
    literary_impact_evidence: Reasoned[str]

TEXTO FUENTE:
{CULTURAL_LITERATURE_FEW_SHOT_INPUT_TEXT}

{stable_block}VALORES CANDIDATOS POR CAMPO:
{trial_count_line}CAMPO `title`
Valores candidatos:
{_candidate_line('"Don Quijote de la Mancha"', "3/4", include_support_counts)}
{_candidate_line('"El ingenioso hidalgo don Quijote de la Mancha"', "1/4", include_support_counts)}

CAMPO `publication_year`
Valores candidatos:
{_candidate_line("1605", "2/4", include_support_counts)}
{_candidate_line("1615", "1/4", include_support_counts)}
{_candidate_line("null", "1/4", include_support_counts)}

CAMPO `genres` (lista)
Elementos candidatos:
{_candidate_line('"novela"', "4/4", include_support_counts)}
{_candidate_line('"novela moderna"', "3/4", include_support_counts)}
{_candidate_line('"novela polifónica"', "2/4", include_support_counts)}
{_candidate_line('"tradición caballeresca"', "1/4", include_support_counts)}

CAMPO `key_themes` (lista)
Elementos candidatos:
{_candidate_line('"tratamiento burlesco"', "4/4", include_support_counts)}
{_candidate_line('"tradición caballeresca"', "3/4", include_support_counts)}
{_candidate_line('"tradición cortés"', "2/4", include_support_counts)}
{_candidate_line('"narrativa europea"', "1/4", include_support_counts)}

CAMPO `original_language`
Valores candidatos:
{_candidate_line("null", "2/4", include_support_counts)}
{_candidate_line('"español"', "1/4", include_support_counts)}
{_candidate_line('"castellano"', "1/4", include_support_counts)}

CAMPO `literary_impact_evidence`
Valores candidatos:
{_candidate_line('"Representa la primera novela moderna y la primera novela polifónica; como tal, ejerció un enorme influjo en toda la narrativa europea."', "2/4", include_support_counts)}
{_candidate_line('"primera novela moderna y la primera novela polifónica"', "1/4", include_support_counts)}
{_candidate_line('"El Quijote influyó mucho en la narrativa europea."', "1/4", include_support_counts)}

SALIDA:
{{
  "title": {{
    "reasoning": "{title_main}: está respaldado por el encabezado `# Don Quijote de la Mancha` y por la frase `Don Quijote de la Mancha es una novela`. {title_part}: aparece solo como título de la primera parte publicada en 1605, no como título principal de la obra completa. Por tanto el valor final es el título principal.",
    "value": "Don Quijote de la Mancha"
  }},
  "publication_year": {{
    "reasoning": "{year_1605}: el texto dice que la primera parte se publicó `a comienzos de 1605`, que responde al año de primera publicación. {year_1615}: corresponde a la continuación, no a la primera publicación. {year_null}: es demasiado conservador porque sí hay evidencia explícita para 1605. Por tanto el valor final es 1605.",
    "value": 1605
  }},
  "genres": {{
    "reasoning": "{genre_novel}: está explícito en `es una novela`. {genre_modern}: está explícito en `la primera novela moderna`. {genre_polyphonic}: está explícito en `la primera novela polifónica`. {genre_chivalric}: el texto la presenta como tema o tradición desmitificada, no como género. Por tanto se incluyen solo los tres géneros respaldados como novela.",
    "value": ["novela", "novela moderna", "novela polifónica"]
  }},
  "key_themes": {{
    "reasoning": "{theme_burlesque}: está explícito y describe el tratamiento temático. {theme_chivalric}: aparece en el fragmento `tradición caballeresca y cortés`. {theme_courtly}: aparece en el mismo fragmento y también es tema. {theme_european}: se refiere al influjo de la obra, no a un tema explorado. Por tanto se incluyen los tres temas explícitos.",
    "value": ["tradición caballeresca", "tradición cortés", "tratamiento burlesco"]
  }},
  "original_language": {{
    "reasoning": "{language_null}: aunque el texto habla de literatura española y de un autor español, no afirma explícitamente la lengua original. {language_spanish}: es una inferencia plausible, pero no está dicho como idioma original. {language_castilian}: también sería conocimiento externo o inferencia. Como el schema permite null y falta evidencia textual directa, el valor final debe ser null.",
    "value": null
  }},
  "literary_impact_evidence": {{
    "reasoning": "{evidence_full}: copia verbatim el fragmento que evidencia que es primera novela moderna y polifónica y su influjo narrativo. {evidence_partial}: es parcial y pierde la parte del influjo. {evidence_paraphrase}: es una paráfrasis, no un fragmento verbatim. Como el campo pide el fragmento completo y verbatim, se elige la frase completa.",
    "value": "Representa la primera novela moderna y la primera novela polifónica; como tal, ejerció un enorme influjo en toda la narrativa europea."
  }}
}}
FIN DEL EJEMPLO.
"""


def _candidate_line(value: str, support: str, include_support_counts: bool) -> str:
    if include_support_counts:
        return f"- {support}: {value}"
    return f"- {value}"


def _candidate_ref(label: str, support: str, include_support_counts: bool) -> str:
    if include_support_counts:
        return f"Candidato {label} ({support})"
    return f"Candidato {label}"
