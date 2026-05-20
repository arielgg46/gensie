from __future__ import annotations

import json
from typing import Any

from gensie.aggregation.judge_scope import JudgeScope
from gensie.aggregation.schema_utils import JsonDict
from gensie.aggregation.verdict_fsp import (
    NoVerdictJudgeFspProvider,
    VerdictJudgeFspProvider,
)
from gensie.aggregation.verdict_schema import (
    VERDICT_EVIDENCE_MAX_LENGTH,
    VerdictCandidateLayout,
    VerdictField,
    VerdictPlan,
    json_value,
    normalize_candidate_layout,
)
from gensie.schemas.inspect import deref, pascal_case, safe_name, unwrap_nullable_anyof
from gensie.task import Task


VERDICT_JUDGE_SYSTEM_PROMPT = (
    "Eres un juez experto de extracción de información en español.\n"
    "Recibes varios intentos de extracción, campos disputados y candidatos observados.\n"
    "Devuelve veredictos estructurados por candidato usando solo el texto fuente.\n"
    "No inventes candidatos, no omitas candidatos y no uses conocimiento externo.\n"
    "Cada candidate_value debe copiar exactamente el literal indicado en el prompt, "
    "en el mismo orden en que aparece para su campo.\n"
    "Escribe caracteres Unicode reales en español (á, é, í, ó, ú, ñ) directamente; "
    "no uses secuencias escapadas \\uXXXX."
)


def build_verdict_judge_prompt(
    task: Task,
    scope: JudgeScope,
    plan: VerdictPlan,
    *,
    fsp_provider: VerdictJudgeFspProvider | None = None,
    include_stable_fields: bool = False,
    include_support_counts: bool = True,
    candidate_layout: VerdictCandidateLayout = "array",
) -> str:
    candidate_layout = normalize_candidate_layout(candidate_layout)
    fsp = (fsp_provider or NoVerdictJudgeFspProvider()).build(
        task=task,
        scope=scope,
        plan=plan,
        include_stable_fields=include_stable_fields,
        include_support_counts=include_support_counts,
        candidate_layout=candidate_layout,
    )
    stable_section = _render_stable_fields_section(scope) if include_stable_fields else ""
    disputed_text = ", ".join(f"`{field}`" for field in plan.field_names)
    count_rule = (
        "Los conteos indican estabilidad entre trials, pero no reemplazan al grounding textual.\n"
        if include_support_counts
        else ""
    )
    stable_instruction = (
        "No devuelvas campos ya consensuados; esos se reconstruyen fuera de esta llamada.\n"
        if include_stable_fields
        else ""
    )
    candidates_instruction = (
        'En cada `candidates`, devuelve un objeto con claves requeridas "1", "2", ...; '
        "cada clave corresponde al candidato de esa posición y no debes añadir otras claves.\n"
        if candidate_layout == "slots"
        else "En cada `candidates`, devuelve un array con exactamente un objeto por candidato listado, en el mismo orden.\n"
    )

    return (
        "TAREA DEL JUEZ:\n"
        "Evalúa los candidatos observados para cada campo disputado y emite un veredicto estructurado.\n"
        f"{count_rule}"
        "En `field`, explica qué pide el campo; no decidas el valor ahí.\n"
        f"{candidates_instruction}"
        "En cada `candidate_value`, copia exactamente el valor candidato correspondiente.\n"
        f"En cada `evidence`, usa una frase breve de máximo {VERDICT_EVIDENCE_MAX_LENGTH} caracteres "
        "sobre la evidencia o ausencia de evidencia de ese candidato. "
        "Cita fragmentos verbatim con contexto y razona ahí mismo si el candidato debe ser el valor final, "
        "en campos simples, o si debe incluirse en el array final, en campos array.\n"
        "Para campos simples, después de `candidates` decide `value` con el valor final.\n"
        "Para campos array, decide `include=true` si el item debe entrar en el array final, o `false` si debe descartarse.\n"
        "El schema de generación solo valida la forma; la lista de candidatos válida está en este prompt y será validada después de la llamada.\n"
        "Si la mayoría contradice el texto fuente o inventa información, corrige hacia el texto o usa null cuando el schema lo permita.\n\n"
        f"{fsp}\n"
        "INSTRUCCIÓN ORIGINAL:\n"
        f"{task.instruction}\n\n"
        "INSTRUCCIÓN DEL JUEZ:\n"
        f"Emite veredictos solo para estos campos: {disputed_text}.\n"
        f"{stable_instruction}\n"
        "SCHEMA PYDANTIC DE VEREDICTOS:\n"
        f"{render_verdict_pydantic_schema(task.target_schema, plan, candidate_layout=candidate_layout)}\n"
        "TEXTO FUENTE:\n"
        f"{task.input_text}\n\n"
        f"{stable_section}"
        "VALORES CANDIDATOS POR CAMPO:\n"
        f"{render_verdict_candidate_summary(plan, include_support_counts=include_support_counts)}"
    )


def render_verdict_candidate_summary(
    plan: VerdictPlan, *, include_support_counts: bool = True
) -> str:
    lines = [f"Trials válidos: {plan.total_trials}"] if include_support_counts else []
    for field in plan.fields:
        lines.append("")
        if field.kind == "array":
            lines.append(f"CAMPO `{field.name}` (lista)")
            lines.append(f"Formato: ArrayVerdict[{_field_type_for_summary(field)}]")
            lines.append("Elementos candidatos, en este orden:")
        else:
            lines.append(f"CAMPO `{field.name}`")
            lines.append(f"Formato: SingleVerdict[{_field_type_for_summary(field)}]")
            lines.append("Valores candidatos, en este orden:")
        if not field.candidates:
            lines.append("Ningún candidato observado.")
            continue
        for index, candidate in enumerate(field.candidates, start=1):
            support = (
                f" ({candidate.count}/{plan.total_trials})"
                if include_support_counts
                else ""
            )
            lines.append(f"{index}.{support}: {json_value(candidate.value)}")
    return "\n".join(lines).rstrip()


def render_verdict_pydantic_schema(
    root_schema: JsonDict,
    plan: VerdictPlan,
    *,
    candidate_layout: VerdictCandidateLayout = "array",
) -> str:
    candidate_layout = normalize_candidate_layout(candidate_layout)
    lines = [
        "Nullable[T] = T | None",
        "",
    ]
    lines.extend(_render_reachable_defs(root_schema, plan))
    if lines[-1] != "":
        lines.append("")
    lines.extend(
        [
            (
                '# candidates es un objeto con claves fijas "1", "2", ...'
                if candidate_layout == "slots"
                else "# candidates es una lista ordenada."
            ),
            (
                "# Debe tener exactamente una clave por candidato listado en VALORES CANDIDATOS POR CAMPO."
                if candidate_layout == "slots"
                else "# Debe tener exactamente un item por candidato listado en VALORES CANDIDATOS POR CAMPO."
            ),
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
    )
    if not plan.fields:
        lines.append("    pass")
        return "\n".join(lines).rstrip() + "\n"

    for field in plan.fields:
        wrapper = "ArrayVerdict" if field.kind == "array" else "SingleVerdict"
        type_hint = _type_hint(field.value_schema, root_schema)
        default = _field_default(field.name, field.field_schema, root_schema)
        lines.append(f"    {safe_name(field.name)}: {wrapper}[{type_hint}]{default}")
    return "\n".join(lines).rstrip() + "\n"


def _render_reachable_defs(root_schema: JsonDict, plan: VerdictPlan) -> list[str]:
    defs = root_schema.get("$defs") if isinstance(root_schema.get("$defs"), dict) else {}
    if not defs:
        return []

    ref_names = sorted(
        {
            ref.rsplit("/", 1)[-1]
            for field in plan.fields
            for ref in _collect_refs(field.value_schema)
        }
    )
    lines: list[str] = []
    for ref_name in ref_names:
        def_schema = defs.get(ref_name)
        if not isinstance(def_schema, dict):
            continue
        alias = _def_alias(ref_name, def_schema)
        resolved = deref(def_schema, root_schema)
        enum = resolved.get("enum")
        if isinstance(enum, list):
            values = ", ".join(json.dumps(value, ensure_ascii=False) for value in enum)
            lines.append(f"{alias} = Literal[{values}]")
            lines.append("")
        elif resolved.get("type") == "object":
            lines.extend(_render_object_def(alias, resolved, root_schema))
            lines.append("")
    return lines


def _render_object_def(name: str, schema: JsonDict, root_schema: JsonDict) -> list[str]:
    properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    required = set(schema.get("required") or [])
    lines = [f"class {name}(BaseModel):"]
    if not properties:
        lines.append("    pass")
        return lines
    for prop_name, prop_schema in properties.items():
        if not isinstance(prop_schema, dict):
            continue
        hint = _type_hint(prop_schema, root_schema)
        default = "..." if prop_name in required else "None"
        desc = prop_schema.get("description")
        args = [default]
        if isinstance(desc, str) and desc.strip():
            args.append(f"description={json.dumps(desc, ensure_ascii=False)}")
        if safe_name(prop_name) != prop_name:
            args.append(f"alias={json.dumps(prop_name, ensure_ascii=False)}")
        lines.append(f"    {safe_name(prop_name)}: {hint} = Field({', '.join(args)})")
    return lines


def _type_hint(schema: JsonDict, root_schema: JsonDict) -> str:
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/$defs/"):
        def_name = ref.rsplit("/", 1)[-1]
        defs = root_schema.get("$defs") if isinstance(root_schema.get("$defs"), dict) else {}
        def_schema = defs.get(def_name) if isinstance(defs.get(def_name), dict) else {}
        return _def_alias(def_name, def_schema)

    unwrapped, nullable = unwrap_nullable_anyof(schema, root_schema)
    resolved = deref(unwrapped, root_schema)
    enum = resolved.get("enum")
    if isinstance(enum, list):
        base = "Literal[" + ", ".join(json.dumps(value, ensure_ascii=False) for value in enum) + "]"
    else:
        current_type = resolved.get("type")
        if current_type == "string":
            base = "str"
        elif current_type == "integer":
            base = "int"
        elif current_type == "number":
            base = "float"
        elif current_type == "boolean":
            base = "bool"
        elif current_type == "array":
            item_schema = resolved.get("items") if isinstance(resolved.get("items"), dict) else {}
            base = f"list[{_type_hint(item_schema, root_schema)}]"
        elif current_type == "object":
            base = "dict[str, Any]"
        elif current_type == "null":
            base = "None"
        else:
            base = "Any"
    return f"Nullable[{base}]" if nullable else base


def _field_type_for_summary(field: VerdictField) -> str:
    return _type_hint(field.value_schema, {"$defs": {}})


def _field_default(name: str, schema: JsonDict, root_schema: JsonDict) -> str:
    resolved = deref(schema, root_schema)
    desc = resolved.get("description")
    args: list[str] = []
    if isinstance(desc, str) and desc.strip():
        args.append(f"description={json.dumps(desc, ensure_ascii=False)}")
    if safe_name(name) != name:
        args.append(f"alias={json.dumps(name, ensure_ascii=False)}")
    return f" = Field({', '.join(args)})" if args else ""


def _collect_refs(schema: JsonDict) -> set[str]:
    refs: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            ref = value.get("$ref")
            if isinstance(ref, str):
                refs.add(ref)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(schema)
    return refs


def _def_alias(def_name: str, schema: JsonDict) -> str:
    title = schema.get("title") if isinstance(schema, dict) else None
    return pascal_case(title if isinstance(title, str) and title.strip() else def_name)


def _render_stable_fields_section(scope: JudgeScope) -> str:
    if not scope.stable_fields:
        return "CAMPOS YA CONSENSUADOS:\n- Ningún campo consensuado.\n\n"
    lines = []
    for field_name, value in scope.stable_fields.items():
        value_json = json.dumps(value, ensure_ascii=False, sort_keys=True)
        lines.append(f"- {field_name}: {value_json}")
    return "CAMPOS YA CONSENSUADOS:\n" + "\n".join(lines) + "\n\n"
