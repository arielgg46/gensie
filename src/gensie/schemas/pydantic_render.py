from __future__ import annotations

import json
from typing import Any

from gensie.schemas.fields import FieldInfo, parse_field
from gensie.schemas.inspect import (
    JsonDict,
    deref,
    pascal_case,
    safe_name,
    schema_type,
    unwrap_nullable_anyof,
)


def render_pydantic_code(schema: JsonDict, *, root_name: str | None = None) -> str:
    root_schema = schema
    model_name = pascal_case(root_name or _schema_title(schema) or "ExtractionModel")
    ref_name_map = _render_defs_name_map(schema)

    lines = _final_pydantic_prelude()
    lines.extend(_render_defs(schema, root_schema, ref_name_map, reasoned=False, deep=False))

    root = deref(schema, root_schema)
    if root.get("type") == "object":
        lines.extend(
            _render_object_model(
                model_name,
                root,
                root_schema,
                class_hint=model_name,
                ref_name_map=ref_name_map,
                reasoned=False,
                deep=False,
            )
        )
    else:
        lines.append(f"class {model_name}(BaseModel):")
        lines.append("    value: Any")

    return "\n".join(lines).rstrip() + "\n"


def render_plain_pydantic_schema(schema: JsonDict) -> str:
    root_schema = schema
    ref_name_map = _render_defs_name_map(schema)
    lines = _plain_pydantic_prelude()
    lines.extend(
        _render_defs(
            schema,
            root_schema,
            ref_name_map,
            reasoned=False,
            deep=False,
            nullable_alias=True,
        )
    )

    root = deref(schema, root_schema)
    if root.get("type") == "object":
        lines.extend(
            _render_object_model(
                "Output",
                root,
                root_schema,
                class_hint="Output",
                ref_name_map=ref_name_map,
                reasoned=False,
                deep=False,
                nullable_alias=True,
            )
        )
    else:
        lines.append("class Output(BaseModel):")
        lines.append("    value: Any")

    return "\n".join(lines).rstrip() + "\n"


def render_reasoned_pydantic_schema(schema: JsonDict) -> str:
    return _render_reasoned_schema(schema, deep=False)


def render_deep_reasoned_pydantic_schema(schema: JsonDict) -> str:
    return _render_reasoned_schema(schema, deep=True)


def _render_reasoned_schema(schema: JsonDict, *, deep: bool) -> str:
    root_schema = schema
    ref_name_map = _render_defs_name_map(schema)
    lines = _reasoned_pydantic_prelude()
    lines.extend(_render_defs(schema, root_schema, ref_name_map, reasoned=deep, deep=deep))

    root = deref(schema, root_schema)
    if root.get("type") == "object":
        lines.extend(
            _render_object_model(
                "Output",
                root,
                root_schema,
                class_hint="Output",
                ref_name_map=ref_name_map,
                reasoned=True,
                deep=deep,
            )
        )
    else:
        lines.append("class Output(BaseModel):")
        lines.append("    value: Reasoned[Any]")

    return "\n".join(lines).rstrip() + "\n"


def _final_pydantic_prelude() -> list[str]:
    return [
        "from __future__ import annotations",
        "",
        "from typing import Any, List, Optional, Literal",
        "from pydantic import BaseModel, Field",
        "",
    ]


def _plain_pydantic_prelude() -> list[str]:
    return [
        "Nullable[T] = T | null",
        "",
    ]


def _reasoned_pydantic_prelude() -> list[str]:
    return [
        "Nullable[T] = T | null",
        "",
        "class Reasoned[T](BaseModel):",
        "    reasoning: str",
        "    value: T",
        "",
    ]


def _render_defs_name_map(schema: JsonDict) -> dict[str, str]:
    defs = schema.get("$defs") if isinstance(schema.get("$defs"), dict) else {}
    return {
        f"#/$defs/{def_name}": pascal_case(_schema_title(def_schema) or def_name)
        for def_name, def_schema in defs.items()
        if isinstance(def_schema, dict)
    }


def _render_defs(
    schema: JsonDict,
    root_schema: JsonDict,
    ref_name_map: dict[str, str],
    *,
    reasoned: bool,
    deep: bool,
    nullable_alias: bool | None = None,
) -> list[str]:
    defs = schema.get("$defs") if isinstance(schema.get("$defs"), dict) else {}
    lines: list[str] = []
    for def_name, def_schema in defs.items():
        if not isinstance(def_schema, dict):
            continue
        def_schema = deref(def_schema, root_schema)
        alias_name = ref_name_map[f"#/$defs/{def_name}"]
        if isinstance(def_schema.get("enum"), list):
            lines.append(f"{alias_name} = {_literal_type(def_schema['enum'])}")
            lines.append("")
        elif schema_type(def_schema) == "object":
            lines.extend(
                _render_object_model(
                    alias_name,
                    def_schema,
                    root_schema,
                    class_hint=alias_name,
                    ref_name_map=ref_name_map,
                    reasoned=reasoned,
                    deep=deep,
                    nullable_alias=nullable_alias,
                )
            )
            lines.append("")
    return lines


def _render_object_model(
    class_name: str,
    schema: JsonDict,
    root_schema: JsonDict,
    *,
    class_hint: str,
    ref_name_map: dict[str, str],
    reasoned: bool,
    deep: bool,
    nullable_alias: bool | None = None,
) -> list[str]:
    properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    required_set = set(schema.get("required") or [])
    nested_models: list[tuple[str, JsonDict]] = []
    fields: list[FieldInfo] = []

    for property_name, property_schema in properties.items():
        if not isinstance(property_schema, dict):
            continue
        field = parse_field(
            name=property_name,
            schema=property_schema,
            root_schema=root_schema,
            path=f"{class_hint}.{property_name}",
            required=property_name in required_set,
        )
        fields.append(field)
        nested_models.extend(_nested_models_for_field(field, property_schema, ref_name_map))

    output: list[str] = []
    for nested_name, nested_schema in nested_models:
        nested_schema = deref(nested_schema, root_schema)
        nested_schema, _ = unwrap_nullable_anyof(nested_schema, root_schema)
        nested_schema = deref(nested_schema, root_schema)
        if nested_schema.get("type") == "object":
            output.extend(
                _render_object_model(
                    nested_name,
                    nested_schema,
                    root_schema,
                    class_hint=nested_name,
                    ref_name_map=ref_name_map,
                    reasoned=reasoned and deep,
                    deep=deep,
                    nullable_alias=nullable_alias,
                )
            )
            output.append("")

    output.append(f"class {class_name}(BaseModel):")
    if not fields:
        output.append("    pass")
        return output

    for field in fields:
        type_hint = _type_for_field(
            field,
            ref_name_map=ref_name_map,
            deep=deep,
            nullable_alias=reasoned if nullable_alias is None else nullable_alias,
        )
        if reasoned:
            type_hint = f"Reasoned[{type_hint}]"
        default = _default_expr(field, reasoned=reasoned)
        output.append(f"    {safe_name(field.name)}: {type_hint}{default}")
    return output


def _type_for_field(
    field: FieldInfo,
    *,
    ref_name_map: dict[str, str],
    deep: bool,
    nullable_alias: bool,
) -> str:
    if field.ref and field.ref in ref_name_map:
        base = ref_name_map[field.ref]
    elif field.enum is not None:
        base = _literal_type(field.enum)
    elif field.json_type == "string":
        base = "str"
    elif field.json_type == "integer":
        base = "int"
    elif field.json_type == "number":
        base = "float"
    elif field.json_type == "boolean":
        base = "bool"
    elif field.json_type == "array":
        inner = "Any"
        if field.items is not None:
            inner = _type_for_field(
                field.items,
                ref_name_map=ref_name_map,
                deep=deep,
                nullable_alias=nullable_alias,
            )
        if deep:
            inner = f"Reasoned[{inner}]"
        base = f"List[{inner}]"
    elif field.json_type == "object":
        base = pascal_case(field.path.replace("[]", "_item").replace(".", "_"))
    else:
        base = "Any"

    if field.nullable:
        return f"Nullable[{base}]" if nullable_alias else f"Optional[{base}]"
    return base


def _default_expr(field: FieldInfo, *, reasoned: bool) -> str:
    args: list[str] = []
    if field.description:
        args.append(f"description={json.dumps(field.description, ensure_ascii=False)}")
    if not reasoned:
        if field.minimum is not None:
            args.append(f"ge={_number_repr(field.minimum)}")
        if field.maximum is not None:
            args.append(f"le={_number_repr(field.maximum)}")
    if safe_name(field.name) != field.name:
        args.append(f"alias={json.dumps(field.name, ensure_ascii=False)}")

    if reasoned:
        return f" = Field({', '.join(args)})" if args else ""

    default = "..." if field.required else "None"
    if args:
        return f" = Field({default}, {', '.join(args)})"
    return f" = {default}"


def _nested_models_for_field(
    field: FieldInfo, property_schema: JsonDict, ref_name_map: dict[str, str]
) -> list[tuple[str, JsonDict]]:
    if field.json_type == "object" and not (field.ref and field.ref in ref_name_map):
        return [
            (
                pascal_case(field.path.replace("[]", "_item").replace(".", "_")),
                property_schema,
            )
        ]
    if (
        field.json_type == "array"
        and field.items
        and field.items.json_type == "object"
        and not (field.items.ref and field.items.ref in ref_name_map)
    ):
        return [
            (
                pascal_case(field.items.path.replace("[]", "_item").replace(".", "_")),
                property_schema.get("items", {}),
            )
        ]
    return []


def _schema_title(schema: Any) -> str | None:
    return schema.get("title") if isinstance(schema, dict) and isinstance(schema.get("title"), str) else None


def _literal_type(values: list[Any]) -> str:
    return "Literal[" + ", ".join(json.dumps(value, ensure_ascii=False) for value in values) + "]"


def _number_repr(value: float) -> str:
    return str(int(value)) if value.is_integer() else str(value)
