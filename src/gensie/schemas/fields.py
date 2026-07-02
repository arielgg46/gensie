from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from gensie.schemas.inspect import JsonDict, deref, schema_type, unwrap_nullable_anyof


@dataclass(frozen=True)
class FieldInfo:
    path: str
    name: str
    required: bool
    json_type: str
    nullable: bool
    description: str | None
    enum: list[Any] | None
    minimum: float | None
    maximum: float | None
    ref: str | None
    items: "FieldInfo | None"
    properties: list["FieldInfo"] | None


def parse_schema_fields(schema: JsonDict) -> list[FieldInfo]:
    root_schema = schema
    schema = deref(schema, root_schema)
    if schema.get("type") != "object":
        return []

    required_set = set(schema.get("required") or [])
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return []

    fields: list[FieldInfo] = []
    for name, property_schema in properties.items():
        if not isinstance(property_schema, dict):
            continue
        fields.append(
            parse_field(
                name=name,
                schema=property_schema,
                root_schema=root_schema,
                path=name,
                required=name in required_set,
            )
        )
    return fields


def parse_field(
    *,
    name: str,
    schema: JsonDict,
    root_schema: JsonDict,
    path: str,
    required: bool,
    seen_refs: frozenset[str] = frozenset(),
) -> FieldInfo:
    ref = schema.get("$ref") if isinstance(schema.get("$ref"), str) else None
    schema, nullable = unwrap_nullable_anyof(schema, root_schema)
    inner_ref = schema.get("$ref") if isinstance(schema.get("$ref"), str) else None
    schema = deref(schema, root_schema)

    # Guard against self-referential schemas (e.g. a ``Taxon`` whose ``children``
    # items point back to ``#/$defs/Taxon``). Once a ``$ref`` has been expanded on
    # the current branch, stop descending into it to avoid infinite recursion.
    active_ref = ref or inner_ref
    stop_recursion = active_ref is not None and active_ref in seen_refs
    next_seen = seen_refs | {active_ref} if active_ref is not None else seen_refs

    current_type = schema_type(schema)
    description = schema.get("description")
    enum = schema.get("enum")
    minimum = schema.get("minimum")
    maximum = schema.get("maximum")

    items: FieldInfo | None = None
    properties: list[FieldInfo] | None = None

    if stop_recursion:
        pass
    elif current_type == "array" and isinstance(schema.get("items"), dict):
        items = parse_field(
            name=f"{name}__item",
            schema=schema["items"],
            root_schema=root_schema,
            path=f"{path}[]",
            required=True,
            seen_refs=next_seen,
        )
    elif current_type == "object":
        child_properties = schema.get("properties")
        if isinstance(child_properties, dict):
            child_required = set(schema.get("required") or [])
            properties = [
                parse_field(
                    name=child_name,
                    schema=child_schema,
                    root_schema=root_schema,
                    path=f"{path}.{child_name}",
                    required=child_name in child_required,
                    seen_refs=next_seen,
                )
                for child_name, child_schema in child_properties.items()
                if isinstance(child_schema, dict)
            ]

    return FieldInfo(
        path=path,
        name=name,
        required=required,
        json_type=current_type or ("enum" if isinstance(enum, list) else "any"),
        nullable=nullable,
        description=description if isinstance(description, str) else None,
        enum=list(enum) if isinstance(enum, list) else None,
        minimum=float(minimum) if isinstance(minimum, (int, float)) else None,
        maximum=float(maximum) if isinstance(maximum, (int, float)) else None,
        ref=ref,
        items=items,
        properties=properties,
    )


def render_field_cards(schema: JsonDict, *, enum_preview: int = 20) -> str:
    lines: list[str] = []

    def emit(field: FieldInfo, indent: int = 0) -> None:
        prefix = "  " * indent
        required = "requerido" if field.required else "opcional"
        lines.append(f"{prefix}- {field.path} :: {_type_repr(field)} ({required})")

        constraints: list[str] = []
        if field.minimum is not None:
            constraints.append(f"min={_number_repr(field.minimum)}")
        if field.maximum is not None:
            constraints.append(f"max={_number_repr(field.maximum)}")
        if constraints:
            lines.append(f"{prefix}  restricciones: {', '.join(constraints)}")

        if field.enum is not None:
            preview = field.enum[:enum_preview]
            preview_text = ", ".join(json.dumps(item, ensure_ascii=False) for item in preview)
            suffix = "" if len(preview) == len(field.enum) else f", ... (+{len(field.enum) - len(preview)} more)"
            lines.append(f"{prefix}  enum: {preview_text}{suffix}")

        if field.description:
            lines.append(f"{prefix}  descripción: {field.description.strip()}")

        if not field.required:
            if field.nullable:
                lines.append(f"{prefix}  regla: si no está en el TEXTO => null")
            else:
                lines.append(f"{prefix}  regla: si no está en el TEXTO => omitir campo")
        elif field.nullable:
            lines.append(f"{prefix}  regla: si no está en el TEXTO => null (nullable)")

        if field.json_type == "object" and field.properties:
            for child in field.properties:
                emit(child, indent + 1)
        elif (
            field.json_type == "array"
            and field.items
            and field.items.json_type == "object"
            and field.items.properties
        ):
            for child in field.items.properties:
                emit(child, indent + 1)

    for field in parse_schema_fields(schema):
        emit(field)

    return "\n".join(lines).strip() + "\n" if lines else ""


def _type_repr(field: FieldInfo) -> str:
    if field.enum is not None:
        base = f"enum[{len(field.enum)}]"
    elif field.json_type in {"string", "integer", "number", "boolean", "object", "array"}:
        base = field.json_type
    else:
        base = "any"

    if field.json_type == "array" and field.items is not None:
        base = f"array[{_type_repr(field.items)}]"
    if field.nullable:
        base = f"nullable[{base}]"
    return base


def _number_repr(value: float) -> str:
    return str(int(value)) if value.is_integer() else str(value)
