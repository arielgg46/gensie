from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, Sequence

from gensie.fsp.cases import default_fsp_cases
from gensie.fsp.examples import (
    CandidateOrder,
    JudgeCandidateExample,
    JudgeExample,
    JudgeFieldExample,
    StructuredFspCase,
    canonical_json,
    ordered_candidates,
)

from gensie.fsp.projection import project_structured_fsp_case
from gensie.fsp.retrieval import FspRetrievalResult, rank_fsp_cases
from gensie.fsp.fixed import (
    CULTURAL_LITERATURE_FEW_SHOT_INPUT_TEXT,
    CULTURAL_LITERATURE_FEW_SHOT_INSTRUCTION,
)
from gensie.schemas.inspect import (
    JsonDict,
    deref,
    safe_name,
    schema_type,
    unwrap_nullable_anyof,
)

if TYPE_CHECKING:
    from gensie.aggregation.judge_scope import JudgeScope
    from gensie.aggregation.verdict_schema import (
        VerdictCandidateLayout,
        VerdictPlan,
    )
    from gensie.task import Task


class VerdictJudgeFspProvider(Protocol):
    def build(
        self,
        *,
        task: Task | None = None,
        scope: JudgeScope | None = None,
        plan: VerdictPlan | None = None,
        include_stable_fields: bool = False,
        include_support_counts: bool = True,
        candidate_layout: VerdictCandidateLayout = "array",
    ) -> str:
        pass


class NoVerdictJudgeFspProvider:
    def build(
        self,
        *,
        task: Task | None = None,
        scope: JudgeScope | None = None,
        plan: VerdictPlan | None = None,
        include_stable_fields: bool = False,
        include_support_counts: bool = True,
        candidate_layout: VerdictCandidateLayout = "array",
    ) -> str:
        del task, scope, plan, include_stable_fields, include_support_counts
        del candidate_layout
        return ""


@dataclass(frozen=True)
class RagVerdictJudgeFspProvider:
    cases: tuple[StructuredFspCase, ...] = field(default_factory=default_fsp_cases)
    top_k: int = 1
    candidate_order: CandidateOrder = CandidateOrder.RESOURCE
    max_prompt_chars: int | None = None

    def __init__(
        self,
        cases: Sequence[StructuredFspCase] | None = None,
        *,
        top_k: int = 1,
        candidate_order: CandidateOrder = CandidateOrder.RESOURCE,
        max_prompt_chars: int | None = None,
    ):
        object.__setattr__(
            self,
            "cases",
            tuple(cases) if cases is not None else default_fsp_cases(),
        )
        object.__setattr__(self, "top_k", max(1, top_k))
        object.__setattr__(self, "candidate_order", candidate_order)
        if max_prompt_chars is not None and max_prompt_chars < 1:
            max_prompt_chars = None
        object.__setattr__(self, "max_prompt_chars", max_prompt_chars)

    def build(
        self,
        *,
        task: Task | None = None,
        scope: JudgeScope | None = None,
        plan: VerdictPlan | None = None,
        include_stable_fields: bool = False,
        include_support_counts: bool = True,
        candidate_layout: VerdictCandidateLayout = "array",
    ) -> str:
        del scope
        selected = self.retrieve(task=task, plan=plan)
        blocks: list[str] = []
        for result in selected:
            case = result.case
            projection_fields = _projection_fields(result, plan)
            if projection_fields:
                case = project_structured_fsp_case(
                    case,
                    projection_fields,
                    include_stable_fields=include_stable_fields,
                )
            prompt = render_candidate_verdict_fsp_example(
                case,
                include_stable_fields=include_stable_fields,
                include_support_counts=include_support_counts,
                candidate_order=self.candidate_order,
                candidate_layout=candidate_layout,
            )
            if not prompt:
                continue
            if (
                self.max_prompt_chars is not None
                and len(prompt) > self.max_prompt_chars
            ):
                continue
            blocks.append(prompt)
            if len(blocks) >= self.top_k:
                break
        return "\n\n".join(blocks)

    def retrieve(
        self,
        *,
        task: Task | None = None,
        plan: VerdictPlan | None = None,
    ) -> tuple[FspRetrievalResult, ...]:
        cases = tuple(case for case in self.cases if case.judge is not None)
        if task is None:
            return tuple(
                FspRetrievalResult(
                    case=case,
                    score=0.0,
                    rank=index,
                    matched_tags=(),
                    matched_terms=(),
                    schema_match=False,
                    compatible_fields=(),
                )
                for index, case in enumerate(cases[: self.top_k], start=1)
            )
        task_text = " ".join(
            (
                task.id,
                task.instruction,
                str(task.target_schema.get("description") or ""),
                " ".join(plan.field_names if plan is not None else ()),
            )
        )
        return rank_fsp_cases(
            task_schema=task.target_schema,
            task_text=task_text,
            cases=cases,
            top_k=len(cases) if self.max_prompt_chars is not None else self.top_k,
        ) or self.retrieve(task=None, plan=plan)


def _projection_fields(
    result: FspRetrievalResult, plan: VerdictPlan | None
) -> tuple[str, ...]:
    if plan is None or result.case.judge is None:
        return ()
    if result.schema_match:
        return plan.field_names
    example_fields = set(result.case.judge.fields)
    return tuple(
        field_name
        for field_name in plan.field_names
        if field_name in example_fields
    )


class FixedVerdictJudgeFspProvider:
    def build(
        self,
        *,
        task: Task | None = None,
        scope: JudgeScope | None = None,
        plan: VerdictPlan | None = None,
        include_stable_fields: bool = False,
        include_support_counts: bool = True,
        candidate_layout: VerdictCandidateLayout = "array",
    ) -> str:
        del task, scope, plan, candidate_layout
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


def render_candidate_verdict_fsp_example(
    case: StructuredFspCase,
    *,
    include_stable_fields: bool = False,
    include_support_counts: bool = True,
    candidate_order: CandidateOrder = CandidateOrder.RESOURCE,
    candidate_layout: VerdictCandidateLayout = "array",
) -> str:
    if case.judge is None or not case.judge.fields:
        return ""

    field_names = tuple(case.judge.fields)
    disputed_text = ", ".join(f"`{field_name}`" for field_name in field_names)
    stable_instruction = (
        "No devuelvas campos ya consensuados; esos se reconstruyen fuera de esta llamada.\n"
        if include_stable_fields
        else ""
    )
    stable_block = (
        _render_stable_fields(case.judge.stable_fields)
        if include_stable_fields
        else ""
    )
    output_json = json.dumps(
        build_candidate_verdict_output(
            case.judge,
            candidate_order=candidate_order,
            candidate_layout=candidate_layout,
        ),
        ensure_ascii=False,
        indent=2,
    )
    return (
        "EJEMPLO:\n"
        f"Caso RAG: {case.id}\n"
        "Este ejemplo muestra cómo evaluar cada candidato por separado y devolver candidate_value literalmente.\n\n"
        "INSTRUCCIÓN ORIGINAL:\n"
        f"{case.instruction}\n\n"
        "INSTRUCCIÓN DEL JUEZ:\n"
        f"Emite veredictos solo para estos campos: {disputed_text}.\n"
        f"{stable_instruction}"
        "SCHEMA PYDANTIC DE VEREDICTOS:\n"
        f"{render_candidate_verdict_pydantic_schema(case, candidate_layout=candidate_layout)}\n"
        "TEXTO FUENTE:\n"
        f"{case.source_text}\n\n"
        f"{stable_block}"
        "VALORES CANDIDATOS POR CAMPO:\n"
        f"{render_candidate_verdict_candidate_summary(case, include_support_counts=include_support_counts, candidate_order=candidate_order)}\n\n"
        "SALIDA:\n"
        f"{output_json}\n"
        "FIN DEL EJEMPLO.\n"
    )


def render_candidate_verdict_candidate_summary(
    case: StructuredFspCase,
    *,
    include_support_counts: bool = True,
    candidate_order: CandidateOrder = CandidateOrder.RESOURCE,
) -> str:
    if case.judge is None:
        return ""

    lines = (
        [f"Trials válidos: {case.judge.total_trials}"]
        if include_support_counts
        else []
    )
    for field_name, field in case.judge.fields.items():
        lines.append("")
        if field.kind == "array":
            lines.append(f"CAMPO `{field_name}` (lista)")
            lines.append(
                f"Formato: ArrayVerdict[{_field_type_for_summary(case.schema, field_name, field)}]"
            )
            lines.append("Elementos candidatos, en este orden:")
        else:
            lines.append(f"CAMPO `{field_name}`")
            lines.append(
                f"Formato: SingleVerdict[{_field_type_for_summary(case.schema, field_name, field)}]"
            )
            lines.append("Valores candidatos, en este orden:")

        for index, candidate in enumerate(
            ordered_candidates(field.candidates, candidate_order),
            start=1,
        ):
            support = (
                f" ({candidate.support}/{case.judge.total_trials})"
                if include_support_counts
                else ""
            )
            lines.append(f"{index}.{support}: {json.dumps(candidate.value, ensure_ascii=False, sort_keys=True)}")

        if field.kind == "array":
            lines.extend(
                _array_field_observations(
                    field,
                    case.judge.total_trials,
                    include_support_counts=include_support_counts,
                )
            )
    return "\n".join(lines).rstrip()


def build_candidate_verdict_output(
    judge: JudgeExample,
    *,
    candidate_order: CandidateOrder = CandidateOrder.RESOURCE,
    candidate_layout: VerdictCandidateLayout = "array",
) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for field_name, field in judge.fields.items():
        candidates = ordered_candidates(field.candidates, candidate_order)
        if candidate_layout == "slots":
            rendered_candidates: Any = {
                str(index): _candidate_output(candidate, field)
                for index, candidate in enumerate(candidates, start=1)
            }
        else:
            rendered_candidates = [
                _candidate_output(candidate, field)
                for candidate in candidates
            ]
        verdict: dict[str, Any] = {
            "field": field.field_description or f"El campo pide `{field_name}`.",
            "candidates": rendered_candidates,
        }
        if field.kind == "single":
            verdict["value"] = copy.deepcopy(_single_field_value(field))
        output[field_name] = verdict
    return output


def render_candidate_verdict_pydantic_schema(
    case: StructuredFspCase,
    *,
    candidate_layout: VerdictCandidateLayout = "array",
) -> str:
    if case.judge is None:
        return "Nullable[T] = T | None\n\nclass Output(BaseModel):\n    pass\n"

    lines = [
        "Nullable[T] = T | None",
        "",
        "class SingleCandidate[T](BaseModel):",
        "    candidate_value: T",
        "    evidence: str",
        "",
        "class ArrayCandidate[T](BaseModel):",
        "    candidate_value: T",
        "    evidence: str",
        "    include: bool",
        "",
        "class SingleVerdict[T](BaseModel):",
        "    field: str",
        (
            "    candidates: dict[str, SingleCandidate[T]]"
            if candidate_layout == "slots"
            else "    candidates: list[SingleCandidate[T]]"
        ),
        "    value: T",
        "",
        "class ArrayVerdict[T](BaseModel):",
        "    field: str",
        (
            "    candidates: dict[str, ArrayCandidate[T]]"
            if candidate_layout == "slots"
            else "    candidates: list[ArrayCandidate[T]]"
        ),
        "",
        "class Output(BaseModel):",
    ]
    for field_name, field in case.judge.fields.items():
        wrapper = "ArrayVerdict" if field.kind == "array" else "SingleVerdict"
        lines.append(
            f"    {safe_name(field_name)}: {wrapper}[{_field_type_for_summary(case.schema, field_name, field)}]"
        )
    return "\n".join(lines).rstrip() + "\n"


def _candidate_output(
    candidate: JudgeCandidateExample, field: JudgeFieldExample
) -> dict[str, Any]:
    output = {
        "candidate_value": copy.deepcopy(candidate.value),
        "evidence": candidate.evidence,
    }
    if field.kind == "array":
        output["include"] = _array_candidate_include(candidate, field)
    return output


def _single_field_value(field: JudgeFieldExample) -> Any:
    if field.reasoned_output is not None and "value" in field.reasoned_output:
        return copy.deepcopy(field.reasoned_output["value"])
    return copy.deepcopy(field.value)


def _array_candidate_include(
    candidate: JudgeCandidateExample, field: JudgeFieldExample
) -> bool:
    if candidate.include is not None:
        return candidate.include
    if not isinstance(field.value, list):
        return False
    candidate_key = canonical_json(candidate.value)
    return any(canonical_json(item) == candidate_key for item in field.value)


def _field_type_for_summary(
    root_schema: JsonDict, field_name: str, field: JudgeFieldExample
) -> str:
    field_schema = _field_schema(root_schema, field_name)
    if field.kind == "array":
        resolved = deref(field_schema, root_schema)
        value_schema = (
            resolved.get("items")
            if isinstance(resolved.get("items"), dict)
            else {}
        )
    else:
        value_schema = field_schema
    return _type_hint(value_schema, root_schema)


def _field_schema(root_schema: JsonDict, field_name: str) -> JsonDict:
    resolved = deref(root_schema, root_schema)
    properties = (
        resolved.get("properties")
        if isinstance(resolved.get("properties"), dict)
        else {}
    )
    field_schema = properties.get(field_name)
    return field_schema if isinstance(field_schema, dict) else {}


def _type_hint(schema: JsonDict, root_schema: JsonDict) -> str:
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/$defs/"):
        return ref.rsplit("/", 1)[-1]

    unwrapped, nullable = unwrap_nullable_anyof(schema, root_schema)
    resolved = deref(unwrapped, root_schema)
    enum = resolved.get("enum")
    if isinstance(enum, list):
        base = "Literal[" + ", ".join(json.dumps(value, ensure_ascii=False) for value in enum) + "]"
    else:
        current_type = schema_type(resolved)
        if current_type == "string":
            base = "str"
        elif current_type == "integer":
            base = "int"
        elif current_type == "number":
            base = "float"
        elif current_type == "boolean":
            base = "bool"
        elif current_type == "array":
            item_schema = (
                resolved.get("items")
                if isinstance(resolved.get("items"), dict)
                else {}
            )
            base = f"list[{_type_hint(item_schema, root_schema)}]"
        elif current_type == "object":
            base = "dict[str, Any]"
        elif current_type == "null":
            base = "None"
        else:
            base = "Any"
    return f"Nullable[{base}]" if nullable else base


def _array_field_observations(
    field: JudgeFieldExample,
    total_trials: int,
    *,
    include_support_counts: bool,
) -> list[str]:
    lines: list[str] = []
    if field.empty_trial_count:
        lines.append(
            f"Observación: lista vacía en {field.empty_trial_count}/{total_trials} trials."
            if include_support_counts
            else "Observación: lista vacía."
        )
    if field.null_trial_count:
        lines.append(
            f"Observación: valor null en {field.null_trial_count}/{total_trials} trials."
            if include_support_counts
            else "Observación: valor null."
        )
    if field.invalid_value_count:
        lines.append(
            f"Observación: valor no-lista inválido en {field.invalid_value_count}/{total_trials} trials."
            if include_support_counts
            else "Observación: valor no-lista inválido."
        )
    return lines


def _render_stable_fields(stable_fields: dict[str, Any]) -> str:
    if not stable_fields:
        return "CAMPOS YA CONSENSUADOS:\n- Ningún campo consensuado.\n\n"
    lines = [
        f"- {field_name}: {json.dumps(value, ensure_ascii=False, sort_keys=True)}"
        for field_name, value in stable_fields.items()
    ]
    return "CAMPOS YA CONSENSUADOS:\n" + "\n".join(lines) + "\n\n"
