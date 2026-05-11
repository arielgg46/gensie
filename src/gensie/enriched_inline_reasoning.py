import copy
import json
from typing import Any, Dict, List, Sequence, Tuple

from gensie.inline_reasoning import (
    CULTURAL_LITERATURE_FEW_SHOT_INPUT_TEXT,
    CULTURAL_LITERATURE_FEW_SHOT_INSTRUCTION,
    CULTURAL_LITERATURE_FEW_SHOT_OUTPUT,
    CULTURAL_LITERATURE_FEW_SHOT_SCHEMA,
    INLINE_REASONING_DESCRIPTION,
    build_inline_reasoning_schema,
    unwrap_inline_reasoning_output,
)
from gensie.prompting import clean_schema_for_prompt
from gensie.schema_enrichment import (
    FieldInfo,
    JsonDict,
    _deref,
    _parse_field,
    _pascal_case,
    _safe_name,
    _schema_type,
    _unwrap_nullable_anyof,
)
from gensie.super_fsp import build_super_fsp_example
from gensie.task import Task


INCLUDE_ENRICHED_INLINE_REASONING_FEW_SHOT = True


ENRICHED_INLINE_REASONING_SYSTEM_PROMPT = (
    "Eres un motor experto de extracción de información en español.\n"
    "Devuelve solo el objeto JSON requerido por el schema.\n"
    "Usa solo evidencia del texto fuente.\n"
    "Cada campo de primer nivel debe incluir reasoning y value.\n"
    "En cada reasoning, cita texto exacto cuando exista evidencia, o indica que no hay evidencia textual."
)


DEEP_INLINE_REASONING_SYSTEM_PROMPT = (
    "Eres un motor experto de extracción de información en español.\n"
    "Devuelve solo el objeto JSON requerido por el schema.\n"
    "Usa solo evidencia del texto fuente.\n"
    "Cada campo, subcampo y elemento de array debe incluir reasoning y value.\n"
    "En cada reasoning, cita texto exacto cuando exista evidencia, o indica que no hay evidencia textual."
)


def render_reasoned_pydantic_schema(schema: JsonDict) -> str:
    """Render a compact Pydantic-like schema using Reasoned[T] wrappers."""
    root_schema = schema
    model_name = "Output"
    defs = schema.get("$defs") if isinstance(schema.get("$defs"), dict) else {}
    ref_name_map: Dict[str, str] = {}

    lines: List[str] = _reasoned_pydantic_prelude()
    for def_name, def_schema in defs.items():
        if not isinstance(def_schema, dict):
            continue
        def_schema = _deref(def_schema, root_schema)
        def_title = def_schema.get("title") if isinstance(def_schema.get("title"), str) else def_name
        alias_name = _pascal_case(def_title)
        ref_name_map[f"#/$defs/{def_name}"] = alias_name
        if "enum" in def_schema and isinstance(def_schema.get("enum"), list):
            lines.append(f"{alias_name} = {_literal_type(def_schema['enum'])}")
            lines.append("")
        elif _schema_type(def_schema) == "object":
            lines.extend(
                _render_object_model(
                    alias_name,
                    def_schema,
                    root_schema,
                    class_hint=alias_name,
                    ref_name_map=ref_name_map,
                )
            )
            lines.append("")

    root_deref = _deref(schema, root_schema)
    if root_deref.get("type") == "object":
        lines.extend(
            _render_reasoned_root_model(
                model_name,
                root_deref,
                root_schema,
                ref_name_map=ref_name_map,
            )
        )
    else:
        lines.append(f"class {model_name}(BaseModel):")
        lines.append("    value: Reasoned[Any]")

    return "\n".join(lines).rstrip() + "\n"


def _reasoned_pydantic_prelude() -> List[str]:
    return [
        "Nullable[T] = T | null",
        "",
        "class Reasoned[T](BaseModel):",
        "    reasoning: str",
        "    value: T",
        "",
    ]


def build_deep_inline_reasoning_schema(schema: JsonDict) -> JsonDict:
    """
    Wrap every schema field and array item as {reasoning, value}.

    The root object itself is not wrapped, matching the existing inline
    reasoning shape, but every root property, nested object property, and array
    item is generated through a Reasoned wrapper.
    """
    original = copy.deepcopy(schema)
    properties = original.get("properties")
    if original.get("type") != "object" or not isinstance(properties, dict):
        raise ValueError("Deep inline reasoning requires a root object schema with properties.")

    transformed_defs = {}
    defs = original.get("$defs") if isinstance(original.get("$defs"), dict) else {}
    for def_name, def_schema in defs.items():
        if isinstance(def_schema, dict):
            transformed_defs[def_name] = _deep_reasoning_value_schema(def_schema)

    wrapped_properties = {
        field_name: _reasoning_wrapper_schema(_deep_reasoning_value_schema(field_schema))
        for field_name, field_schema in properties.items()
        if isinstance(field_schema, dict)
    }

    reasoning_schema: JsonDict = {
        "type": "object",
        "additionalProperties": False,
        "properties": wrapped_properties,
        "required": list(wrapped_properties.keys()),
    }

    if transformed_defs:
        reasoning_schema["$defs"] = transformed_defs
    if "description" in original:
        reasoning_schema["description"] = (
            "Deep inline reasoning wrapper for: " + str(original["description"])
        )
    if "title" in original:
        reasoning_schema["title"] = str(original["title"]) + "DeepInlineReasoning"

    return reasoning_schema


def _reasoning_wrapper_schema(value_schema: JsonDict) -> JsonDict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "reasoning": {
                "type": "string",
                "description": INLINE_REASONING_DESCRIPTION,
            },
            "value": value_schema,
        },
        "required": ["reasoning", "value"],
    }


def _deep_reasoning_value_schema(schema: JsonDict) -> JsonDict:
    schema = copy.deepcopy(schema)

    if "$ref" in schema:
        return schema

    any_of = schema.get("anyOf")
    if isinstance(any_of, list):
        transformed_any_of = []
        for alt in any_of:
            if isinstance(alt, dict) and alt.get("type") != "null":
                transformed_any_of.append(_deep_reasoning_value_schema(alt))
            else:
                transformed_any_of.append(copy.deepcopy(alt))
        schema["anyOf"] = transformed_any_of
        return schema

    schema_type = schema.get("type")
    if schema_type == "object":
        props = schema.get("properties")
        if isinstance(props, dict):
            wrapped_props = {
                name: _reasoning_wrapper_schema(_deep_reasoning_value_schema(prop_schema))
                for name, prop_schema in props.items()
                if isinstance(prop_schema, dict)
            }
            schema["properties"] = wrapped_props
            schema["required"] = list(wrapped_props.keys())
            schema["additionalProperties"] = False
        return schema

    if schema_type == "array":
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            schema["items"] = _reasoning_wrapper_schema(
                _deep_reasoning_value_schema(item_schema)
            )
        return schema

    return schema


def unwrap_deep_inline_reasoning_output(
    raw_output: JsonDict, original_schema: JsonDict
) -> JsonDict:
    """Return official GenSIE output by recursively keeping only wrapper values."""
    if not isinstance(raw_output, dict):
        raise ValueError("Deep inline reasoning output must be a JSON object.")
    root_schema = original_schema
    schema = _deref(original_schema, root_schema)
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        raise ValueError("Original schema has no root properties.")
    return _unwrap_deep_reasoned_object(raw_output, schema, root_schema, root=True)


def _unwrap_deep_reasoned_wrapper(
    wrapped_value: Any,
    schema: JsonDict,
    root_schema: JsonDict,
) -> Any:
    if not isinstance(wrapped_value, dict) or "value" not in wrapped_value:
        raise ValueError("Missing deep inline reasoning value wrapper.")
    return _unwrap_deep_reasoned_value(wrapped_value["value"], schema, root_schema)


def _unwrap_deep_reasoned_value(
    value: Any,
    schema: JsonDict,
    root_schema: JsonDict,
) -> Any:
    schema, nullable = _unwrap_nullable_anyof(schema, root_schema)
    schema = _deref(schema, root_schema)
    if value is None:
        if nullable:
            return None
        return None

    schema_type = _schema_type(schema)
    if schema_type == "array":
        item_schema = schema.get("items") if isinstance(schema.get("items"), dict) else {}
        if not isinstance(value, list):
            raise ValueError("Expected list value in deep inline reasoning output.")
        return [
            _unwrap_deep_reasoned_wrapper(item, item_schema, root_schema)
            for item in value
        ]

    if schema_type == "object":
        if not isinstance(value, dict):
            raise ValueError("Expected object value in deep inline reasoning output.")
        return _unwrap_deep_reasoned_object(value, schema, root_schema, root=False)

    return value


def _unwrap_deep_reasoned_object(
    value: JsonDict,
    schema: JsonDict,
    root_schema: JsonDict,
    *,
    root: bool,
) -> JsonDict:
    props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    required = set(props.keys() if root else schema.get("required") or [])
    out: JsonDict = {}
    for name, prop_schema in props.items():
        if name not in value:
            if name in required:
                raise ValueError(f"Missing deep inline reasoning field: {name}")
            continue
        if not isinstance(prop_schema, dict):
            continue
        out[name] = _unwrap_deep_reasoned_wrapper(value[name], prop_schema, root_schema)
    return out


def render_deep_reasoned_pydantic_schema(schema: JsonDict) -> str:
    """Render Pydantic-like schema where all fields and array items are Reasoned."""
    root_schema = schema
    model_name = "Output"
    defs = schema.get("$defs") if isinstance(schema.get("$defs"), dict) else {}
    ref_name_map: Dict[str, str] = {}

    lines: List[str] = _reasoned_pydantic_prelude()
    for def_name, def_schema in defs.items():
        if not isinstance(def_schema, dict):
            continue
        def_schema = _deref(def_schema, root_schema)
        def_title = def_schema.get("title") if isinstance(def_schema.get("title"), str) else def_name
        alias_name = _pascal_case(def_title)
        ref_name_map[f"#/$defs/{def_name}"] = alias_name
        if "enum" in def_schema and isinstance(def_schema.get("enum"), list):
            lines.append(f"{alias_name} = {_literal_type(def_schema['enum'])}")
            lines.append("")
        elif _schema_type(def_schema) == "object":
            lines.extend(
                _render_deep_reasoned_object_model(
                    alias_name,
                    def_schema,
                    root_schema,
                    class_hint=alias_name,
                    ref_name_map=ref_name_map,
                )
            )
            lines.append("")

    root_deref = _deref(schema, root_schema)
    if root_deref.get("type") == "object":
        lines.extend(
            _render_deep_reasoned_object_model(
                model_name,
                root_deref,
                root_schema,
                class_hint=model_name,
                ref_name_map=ref_name_map,
            )
        )
    else:
        lines.append(f"class {model_name}(BaseModel):")
        lines.append("    value: Reasoned[Any]")

    return "\n".join(lines).rstrip() + "\n"


def _literal_type(values: List[Any]) -> str:
    return "Literal[" + ", ".join(json.dumps(x, ensure_ascii=False) for x in values) + "]"


def _type_for_field(fi: FieldInfo, *, ref_name_map: Dict[str, str]) -> str:
    if fi.ref and fi.ref in ref_name_map:
        base = ref_name_map[fi.ref]
    elif fi.enum is not None:
        base = _literal_type(fi.enum)
    elif fi.json_type == "string":
        base = "str"
    elif fi.json_type == "integer":
        base = "int"
    elif fi.json_type == "number":
        base = "float"
    elif fi.json_type == "boolean":
        base = "bool"
    elif fi.json_type == "array":
        inner = "Any"
        if fi.items is not None:
            inner = _type_for_field(fi.items, ref_name_map=ref_name_map)
        base = f"List[{inner}]"
    elif fi.json_type == "object":
        base = _pascal_case(fi.path.replace("[]", "_item").replace(".", "_"))
    else:
        base = "Any"

    if fi.nullable:
        return f"Nullable[{base}]"
    return base


def _field_expr(fi: FieldInfo, *, description_for_value: bool = False) -> str:
    args: List[str] = []
    if fi.description:
        args.append(f"description={json.dumps(fi.description, ensure_ascii=False)}")
    if not description_for_value:
        if fi.minimum is not None:
            args.append(f"ge={_number_repr(fi.minimum)}")
        if fi.maximum is not None:
            args.append(f"le={_number_repr(fi.maximum)}")
    if _safe_name(fi.name) != fi.name:
        args.append(f"alias={json.dumps(fi.name, ensure_ascii=False)}")
    return f" = Field({', '.join(args)})" if args else ""


def _number_repr(value: float) -> str:
    return str(int(value)) if value.is_integer() else str(value)


def _render_object_model(
    class_name: str,
    schema: JsonDict,
    root_schema: JsonDict,
    *,
    class_hint: str,
    ref_name_map: Dict[str, str],
) -> List[str]:
    props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    nested_models: List[Tuple[str, JsonDict]] = []
    fields: List[Tuple[str, FieldInfo]] = []

    for prop_name, prop_schema in props.items():
        if not isinstance(prop_schema, dict):
            continue
        fi = _parse_field(
            name=prop_name,
            schema=prop_schema,
            root_schema=root_schema,
            path=f"{class_hint}.{prop_name}",
            required=True,
        )
        fields.append((prop_name, fi))
        nested_models.extend(_nested_models_for_field(fi, prop_schema, ref_name_map))

    out: List[str] = []
    for nested_name, nested_schema in nested_models:
        nested_deref = _deref(nested_schema, root_schema)
        nested_deref, _ = _unwrap_nullable_anyof(nested_deref, root_schema)
        nested_deref = _deref(nested_deref, root_schema)
        if nested_deref.get("type") == "object":
            out.extend(
                _render_object_model(
                    nested_name,
                    nested_deref,
                    root_schema,
                    class_hint=nested_name,
                    ref_name_map=ref_name_map,
                )
            )
            out.append("")

    out.append(f"class {class_name}(BaseModel):")
    if not fields:
        out.append("    pass")
        return out

    for _, fi in fields:
        py_name = _safe_name(fi.name)
        type_hint = _type_for_field(fi, ref_name_map=ref_name_map)
        out.append(f"    {py_name}: {type_hint}{_field_expr(fi)}")
    return out


def _deep_type_for_field(fi: FieldInfo, *, ref_name_map: Dict[str, str]) -> str:
    if fi.ref and fi.ref in ref_name_map:
        base = ref_name_map[fi.ref]
    elif fi.enum is not None:
        base = _literal_type(fi.enum)
    elif fi.json_type == "string":
        base = "str"
    elif fi.json_type == "integer":
        base = "int"
    elif fi.json_type == "number":
        base = "float"
    elif fi.json_type == "boolean":
        base = "bool"
    elif fi.json_type == "array":
        inner = "Any"
        if fi.items is not None:
            inner = _deep_type_for_field(fi.items, ref_name_map=ref_name_map)
        base = f"List[Reasoned[{inner}]]"
    elif fi.json_type == "object":
        base = _pascal_case(fi.path.replace("[]", "_item").replace(".", "_"))
    else:
        base = "Any"

    if fi.nullable:
        return f"Nullable[{base}]"
    return base


def _render_deep_reasoned_object_model(
    class_name: str,
    schema: JsonDict,
    root_schema: JsonDict,
    *,
    class_hint: str,
    ref_name_map: Dict[str, str],
) -> List[str]:
    props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    nested_models: List[Tuple[str, JsonDict]] = []
    fields: List[Tuple[str, FieldInfo]] = []

    for prop_name, prop_schema in props.items():
        if not isinstance(prop_schema, dict):
            continue
        fi = _parse_field(
            name=prop_name,
            schema=prop_schema,
            root_schema=root_schema,
            path=f"{class_hint}.{prop_name}",
            required=True,
        )
        fields.append((prop_name, fi))
        nested_models.extend(_nested_models_for_field(fi, prop_schema, ref_name_map))

    out: List[str] = []
    for nested_name, nested_schema in nested_models:
        nested_deref = _deref(nested_schema, root_schema)
        nested_deref, _ = _unwrap_nullable_anyof(nested_deref, root_schema)
        nested_deref = _deref(nested_deref, root_schema)
        if nested_deref.get("type") == "object":
            out.extend(
                _render_deep_reasoned_object_model(
                    nested_name,
                    nested_deref,
                    root_schema,
                    class_hint=nested_name,
                    ref_name_map=ref_name_map,
                )
            )
            out.append("")

    out.append(f"class {class_name}(BaseModel):")
    if not fields:
        out.append("    pass")
        return out

    for _, fi in fields:
        py_name = _safe_name(fi.name)
        type_hint = _deep_type_for_field(fi, ref_name_map=ref_name_map)
        out.append(
            f"    {py_name}: Reasoned[{type_hint}]{_field_expr(fi, description_for_value=True)}"
        )
    return out


def _render_reasoned_root_model(
    class_name: str,
    schema: JsonDict,
    root_schema: JsonDict,
    *,
    ref_name_map: Dict[str, str],
) -> List[str]:
    props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    nested_models: List[Tuple[str, JsonDict]] = []
    fields: List[Tuple[str, FieldInfo]] = []

    for prop_name, prop_schema in props.items():
        if not isinstance(prop_schema, dict):
            continue
        fi = _parse_field(
            name=prop_name,
            schema=prop_schema,
            root_schema=root_schema,
            path=f"{class_name}.{prop_name}",
            required=True,
        )
        fields.append((prop_name, fi))
        nested_models.extend(_nested_models_for_field(fi, prop_schema, ref_name_map))

    out: List[str] = []
    for nested_name, nested_schema in nested_models:
        nested_deref = _deref(nested_schema, root_schema)
        nested_deref, _ = _unwrap_nullable_anyof(nested_deref, root_schema)
        nested_deref = _deref(nested_deref, root_schema)
        if nested_deref.get("type") == "object":
            out.extend(
                _render_object_model(
                    nested_name,
                    nested_deref,
                    root_schema,
                    class_hint=nested_name,
                    ref_name_map=ref_name_map,
                )
            )
            out.append("")

    out.append(f"class {class_name}(BaseModel):")
    if not fields:
        out.append("    pass")
        return out

    for _, fi in fields:
        py_name = _safe_name(fi.name)
        type_hint = _type_for_field(fi, ref_name_map=ref_name_map)
        out.append(
            f"    {py_name}: Reasoned[{type_hint}]{_field_expr(fi, description_for_value=True)}"
        )
    return out


def _nested_models_for_field(
    fi: FieldInfo, prop_schema: JsonDict, ref_name_map: Dict[str, str]
) -> List[Tuple[str, JsonDict]]:
    if fi.json_type == "object":
        if not (fi.ref and fi.ref in ref_name_map):
            return [
                (
                    _pascal_case(fi.path.replace("[]", "_item").replace(".", "_")),
                    prop_schema,
                )
            ]
    if fi.json_type == "array" and fi.items and fi.items.json_type == "object":
        if not (fi.items.ref and fi.items.ref in ref_name_map):
            return [
                (
                    _pascal_case(fi.items.path.replace("[]", "_item").replace(".", "_")),
                    prop_schema.get("items", {}),
                )
            ]
    return []


def _build_enriched_cultural_few_shot_schema() -> JsonDict:
    schema = copy.deepcopy(CULTURAL_LITERATURE_FEW_SHOT_SCHEMA)
    props = schema.setdefault("properties", {})
    props["literary_impact_evidence"] = {
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
            "El campo pide un fragmento verbatim completo de evidencia, no una "
            "etiqueta resumida como \"novela moderna\". La frase del texto que "
            "responde es larga y conecta la clasificacion con su impacto narrativo: "
            "\"Representa la primera novela moderna y la primera novela polifónica; "
            "como tal, ejerció un enorme influjo en toda la narrativa europea\". "
            "Por eso value copia el fragmento minimo completo."
        ),
        "value": (
            "Representa la primera novela moderna y la primera novela polifónica; "
            "como tal, ejerció un enorme influjo en toda la narrativa europea."
        ),
    }
    return output


def _build_cultural_enriched_inline_reasoning_few_shot_example() -> str:
    schema = _build_enriched_cultural_few_shot_schema()
    output = _build_enriched_cultural_few_shot_output()
    _, schema_description = clean_schema_for_prompt(schema)
    schema_code = render_reasoned_pydantic_schema(schema)
    output_json = json.dumps(output, ensure_ascii=False, indent=2)
    return (
        "EJEMPLO:\n"
        "Este ejemplo muestra cómo citar evidencia, razonar antes de escribir value "
        "y copiar fragmentos verbatim largos cuando un campo lo pide.\n\n"
        "INSTRUCCIÓN DEL EJEMPLO:\n"
        f"{CULTURAL_LITERATURE_FEW_SHOT_INSTRUCTION} Incluye tambien el fragmento verbatim completo que evidencia su importancia literaria.\n"
        f"{schema_description or 'No root schema description provided.'}\n\n"
        "SCHEMA PYDANTIC DEL EJEMPLO:\n"
        f"{schema_code}\n"
        "TEXTO FUENTE DEL EJEMPLO:\n"
        f"{CULTURAL_LITERATURE_FEW_SHOT_INPUT_TEXT}\n\n"
        "OUTPUT DEL EJEMPLO:\n"
        f"{output_json}\n\n"
        "FIN DEL EJEMPLO.\n"
    )


def build_enriched_inline_reasoning_few_shot_example() -> str:
    return _build_cultural_enriched_inline_reasoning_few_shot_example()


def _build_deep_cultural_few_shot_output() -> JsonDict:
    schema = _build_enriched_cultural_few_shot_schema()
    output = _build_enriched_cultural_few_shot_output()
    root_schema = schema
    props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    deep_output: JsonDict = {}
    for field_name, wrapped_field in output.items():
        field_schema = props.get(field_name) if isinstance(props.get(field_name), dict) else {}
        if not isinstance(wrapped_field, dict) or "value" not in wrapped_field:
            continue
        deep_output[field_name] = {
            "reasoning": wrapped_field.get("reasoning", ""),
            "value": _deep_reasoned_example_value(
                wrapped_field["value"],
                field_schema,
                root_schema,
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
    schema, nullable = _unwrap_nullable_anyof(schema, root_schema)
    schema = _deref(schema, root_schema)
    if value is None:
        return None if nullable else None

    schema_type = _schema_type(schema)
    if schema_type == "array":
        item_schema = schema.get("items") if isinstance(schema.get("items"), dict) else {}
        if not isinstance(value, list):
            return value
        return [
            {
                "reasoning": (
                    f"Este item de {path} se incluye porque esta apoyado por "
                    "la evidencia citada en el reasoning del campo."
                ),
                "value": _deep_reasoned_example_value(
                    item,
                    item_schema,
                    root_schema,
                    path=f"{path}[]",
                ),
            }
            for item in value
        ]

    if schema_type == "object":
        props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
        if not isinstance(value, dict):
            return value
        out: JsonDict = {}
        for prop_name, prop_schema in props.items():
            if prop_name not in value or not isinstance(prop_schema, dict):
                continue
            out[prop_name] = {
                "reasoning": (
                    f"El subcampo {prop_name} de {path} se extrae del mismo "
                    "item y se respalda con el texto fuente."
                ),
                "value": _deep_reasoned_example_value(
                    value[prop_name],
                    prop_schema,
                    root_schema,
                    path=f"{path}.{prop_name}",
                ),
            }
        return out

    return value


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
        f"{CULTURAL_LITERATURE_FEW_SHOT_INSTRUCTION} Incluye tambien el fragmento verbatim completo que evidencia su importancia literaria.\n"
        f"{schema_description or 'No root schema description provided.'}\n\n"
        "SCHEMA PYDANTIC DEL EJEMPLO:\n"
        f"{schema_code}\n"
        "TEXTO FUENTE DEL EJEMPLO:\n"
        f"{CULTURAL_LITERATURE_FEW_SHOT_INPUT_TEXT}\n\n"
        "OUTPUT DEL EJEMPLO:\n"
        f"{output_json}\n\n"
        "FIN DEL EJEMPLO.\n"
    )


def build_enriched_inline_reasoning_prompt(
    task: Task,
    *,
    verbatim_entity_list: Sequence[str] | None = None,
) -> str:
    few_shot_example = (
        build_enriched_inline_reasoning_few_shot_example() + "\n"
        if INCLUDE_ENRICHED_INLINE_REASONING_FEW_SHOT
        else ""
    )
    return _build_enriched_inline_reasoning_prompt(
        task,
        few_shot_example=few_shot_example,
        verbatim_entity_list=verbatim_entity_list,
    )


def build_enriched_inline_reasoning_super_fsp_prompt(task: Task) -> str:
    return _build_enriched_inline_reasoning_prompt(
        task,
        few_shot_example=build_super_fsp_example() + "\n",
        verbatim_entity_list=None,
    )


def _build_enriched_inline_reasoning_prompt(
    task: Task,
    *,
    few_shot_example: str,
    verbatim_entity_list: Sequence[str] | None,
) -> str:
    _, root_description = clean_schema_for_prompt(task.target_schema)
    schema_description = root_description or "No root schema description provided."
    schema_code = render_reasoned_pydantic_schema(task.target_schema)
    verbatim_entity_block = _build_verbatim_entity_list_prompt_block(
        verbatim_entity_list
    )

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
        "- Si un campo pide fragmento verbatim/source text/evidence, copia el fragmento minimo completo del texto que responde la pregunta; no devuelvas solo la entidad o respuesta normalizada.\n"
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
    verbatim_entity_list: Sequence[str] | None,
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


def _dedupe_prompt_entities(verbatim_entity_list: Sequence[str]) -> List[str]:
    seen: set[str] = set()
    entities: List[str] = []
    for item in verbatim_entity_list:
        if not isinstance(item, str):
            continue
        entity = item.strip()
        if not entity or entity in seen:
            continue
        seen.add(entity)
        entities.append(entity)
    return entities


def build_enriched_deep_inline_reasoning_prompt(task: Task) -> str:
    _, root_description = clean_schema_for_prompt(task.target_schema)
    schema_description = root_description or "No root schema description provided."
    schema_code = render_deep_reasoned_pydantic_schema(task.target_schema)
    few_shot_example = (
        build_enriched_deep_inline_reasoning_few_shot_example() + "\n"
        if INCLUDE_ENRICHED_INLINE_REASONING_FEW_SHOT
        else ""
    )

    return (
        "TAREA:\n"
        "Eres un extractor de información estructurada. Debes usar solo evidencia del TEXTO FUENTE.\n"
        "La salida debe seguir el schema de generación: cada campo, subcampo y elemento de array contiene reasoning y value.\n\n"
        "FORMATO DE RAZONAMIENTO RECURSIVO:\n"
        "- Completa todos los campos del schema.\n"
        "- En cada campo y subcampo, escribe primero reasoning y después value.\n"
        "- En arrays, value contiene una lista de Reasoned[item]; cada elemento tiene reasoning propio.\n"
        "- Si un elemento de array es un objeto, su value contiene un objeto cuyos campos tambien son Reasoned[T].\n"
        "- reasoning debe citar texto exacto del TEXTO FUENTE cuando exista evidencia.\n"
        "- Si no hay evidencia suficiente y value permite null, usa null y explica por qué.\n"
        "- value contiene solo la respuesta final de ese campo, subcampo o elemento, sin explicaciones.\n"
        "- Si un campo pide fragmento verbatim/source text/evidence, copia el fragmento minimo completo del texto que responde la pregunta; no devuelvas solo la entidad o respuesta normalizada.\n"
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
