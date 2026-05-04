from __future__ import annotations

import json
import keyword
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple


JsonDict = Dict[str, Any]


@dataclass(frozen=True)
class FieldInfo:
    path: str
    name: str
    required: bool
    json_type: str
    nullable: bool
    description: Optional[str]
    enum: Optional[List[Any]]
    minimum: Optional[float]
    maximum: Optional[float]
    ref: Optional[str]
    items: Optional["FieldInfo"]
    properties: Optional[List["FieldInfo"]]


def _is_null_schema(s: JsonDict) -> bool:
    return s.get("type") == "null"


def _resolve_local_ref(root_schema: JsonDict, ref: str) -> JsonDict:
    """
    Resolves only local JSON-pointer refs like '#/$defs/Foo'.
    Returns {} if ref is unsupported/unresolvable.
    """
    if not ref.startswith("#/"):
        return {}
    curr: Any = root_schema
    for part in ref[2:].split("/"):
        if not isinstance(curr, dict):
            return {}
        curr = curr.get(part)
        if curr is None:
            return {}
    return curr if isinstance(curr, dict) else {}


def _deref(schema: JsonDict, root_schema: JsonDict) -> JsonDict:
    if "$ref" in schema:
        resolved = _resolve_local_ref(root_schema, schema["$ref"])
        if not resolved:
            return schema
        # JSON Schema allows sibling keys next to $ref; for our prompt/pydantic rendering
        # we prefer local overrides to win (e.g., description).
        merged = dict(resolved)
        merged.update({k: v for k, v in schema.items() if k != "$ref"})
        return merged
    return schema


def _unwrap_nullable_anyof(schema: JsonDict, root_schema: JsonDict) -> Tuple[JsonDict, bool]:
    """
    Common pattern in this repo: anyOf([T, null]) with default null.
    Returns (inner_schema, nullable).
    If anyOf contains multiple non-null alternatives, returns (schema, False).
    """
    schema = _deref(schema, root_schema)
    any_of = schema.get("anyOf")
    if not isinstance(any_of, list) or not any_of:
        return schema, False

    alts: List[JsonDict] = []
    has_null = False
    for alt in any_of:
        if not isinstance(alt, dict):
            return schema, False
        alt = _deref(alt, root_schema)
        if _is_null_schema(alt):
            has_null = True
        else:
            alts.append(alt)

    if has_null and len(alts) == 1:
        # keep outer metadata like description/title/default if present
        inner = dict(alts[0])
        for k in ("description", "title", "default", "examples"):
            if k in schema and k not in inner:
                inner[k] = schema[k]
        return inner, True

    return schema, False


def _schema_type(schema: JsonDict) -> str:
    t = schema.get("type")
    return t if isinstance(t, str) else ""


def _safe_name(s: str) -> str:
    s2 = re.sub(r"[^0-9a-zA-Z_]+", "_", s).strip("_")
    if not s2:
        s2 = "field"
    if s2[0].isdigit():
        s2 = f"f_{s2}"
    if keyword.iskeyword(s2):
        s2 = f"{s2}_"
    return s2


def _pascal_case(s: str) -> str:
    parts = re.split(r"[^0-9a-zA-Z]+", s)
    parts = [p for p in parts if p]
    if not parts:
        return "Model"
    out = "".join(p[:1].upper() + p[1:] for p in parts)
    if out[0].isdigit():
        out = f"M{out}"
    return out


def parse_schema_fields(schema: JsonDict) -> List[FieldInfo]:
    """
    Parses the root schema into a list of FieldInfo (top-level properties).
    Assumes the root schema is an object (as in GenSIE tasks).
    """
    root_schema = schema
    schema = _deref(schema, root_schema)
    if schema.get("type") != "object":
        return []
    required_set = set(schema.get("required") or [])
    props = schema.get("properties") or {}
    if not isinstance(props, dict):
        return []

    out: List[FieldInfo] = []
    for name, prop_schema in props.items():
        if not isinstance(prop_schema, dict):
            continue
        out.append(
            _parse_field(
                name=name,
                schema=prop_schema,
                root_schema=root_schema,
                path=name,
                required=name in required_set,
            )
        )
    return out


def _parse_field(
    *,
    name: str,
    schema: JsonDict,
    root_schema: JsonDict,
    path: str,
    required: bool,
) -> FieldInfo:
    ref = schema.get("$ref") if isinstance(schema.get("$ref"), str) else None
    schema2, nullable = _unwrap_nullable_anyof(schema, root_schema)
    schema2 = _deref(schema2, root_schema)

    json_type = _schema_type(schema2)
    description = schema2.get("description") if isinstance(schema2.get("description"), str) else None
    enum = schema2.get("enum") if isinstance(schema2.get("enum"), list) else None
    minimum = schema2.get("minimum")
    maximum = schema2.get("maximum")
    minimum = float(minimum) if isinstance(minimum, (int, float)) else None
    maximum = float(maximum) if isinstance(maximum, (int, float)) else None

    items: Optional[FieldInfo] = None
    properties: Optional[List[FieldInfo]] = None

    if json_type == "array" and isinstance(schema2.get("items"), dict):
        items = _parse_field(
            name=f"{name}__item",
            schema=schema2["items"],
            root_schema=root_schema,
            path=f"{path}[]",
            required=True,
        )
    elif json_type == "object":
        props = schema2.get("properties")
        if isinstance(props, dict):
            req_set = set(schema2.get("required") or [])
            properties = []
            for child_name, child_schema in props.items():
                if not isinstance(child_schema, dict):
                    continue
                properties.append(
                    _parse_field(
                        name=child_name,
                        schema=child_schema,
                        root_schema=root_schema,
                        path=f"{path}.{child_name}",
                        required=child_name in req_set,
                    )
                )

    return FieldInfo(
        path=path,
        name=name,
        required=required,
        json_type=json_type or ("enum" if enum is not None else "any"),
        nullable=nullable,
        description=description,
        enum=list(enum) if enum is not None else None,
        minimum=minimum,
        maximum=maximum,
        ref=ref,
        items=items,
        properties=properties,
    )


def _type_repr_for_prompt(fi: FieldInfo) -> str:
    base = ""
    if fi.enum is not None:
        base = f"enum[{len(fi.enum)}]"
    elif fi.json_type in ("string", "integer", "number", "boolean", "object", "array"):
        base = fi.json_type
    else:
        base = "any"

    if fi.json_type == "array" and fi.items is not None:
        base = f"array[{_type_repr_for_prompt(fi.items)}]"
    if fi.nullable:
        base = f"nullable[{base}]"
    return base


def render_field_cards(schema: JsonDict, *, enum_preview: int = 20) -> str:
    """
    Human-friendly, compact “cards” per field path.
    """
    fields = parse_schema_fields(schema)
    lines: List[str] = []

    def emit(fi: FieldInfo, indent: int = 0):
        prefix = "  " * indent
        req = "required" if fi.required else "optional"
        t = _type_repr_for_prompt(fi)
        parts = [f"{prefix}- {fi.path} :: {t} ({req})"]

        constraints: List[str] = []
        if fi.minimum is not None:
            constraints.append(f"min={int(fi.minimum) if fi.minimum.is_integer() else fi.minimum}")
        if fi.maximum is not None:
            constraints.append(f"max={int(fi.maximum) if fi.maximum.is_integer() else fi.maximum}")
        if constraints:
            parts.append(f"{prefix}  constraints: {', '.join(constraints)}")

        if fi.enum is not None:
            preview = fi.enum[:enum_preview]
            preview_txt = ", ".join(json.dumps(x, ensure_ascii=False) for x in preview)
            suffix = "" if len(preview) == len(fi.enum) else f", ... (+{len(fi.enum)-len(preview)} more)"
            parts.append(f"{prefix}  enum: {preview_txt}{suffix}")

        if fi.description:
            parts.append(f"{prefix}  desc: {fi.description.strip()}")

        if not fi.required:
            if fi.nullable:
                parts.append(f"{prefix}  rule: if not in TEXT => null")
            else:
                parts.append(f"{prefix}  rule: if not in TEXT => omit field")
        elif fi.nullable:
            parts.append(f"{prefix}  rule: if not in TEXT => null (nullable)")

        lines.extend(parts)

        if fi.json_type == "object" and fi.properties:
            for ch in fi.properties:
                emit(ch, indent + 1)
        elif fi.json_type == "array" and fi.items and fi.items.json_type == "object" and fi.items.properties:
            # show item fields under the array
            for ch in fi.items.properties:
                emit(ch, indent + 1)

    for f in fields:
        emit(f, 0)

    return "\n".join(lines).strip() + "\n"


def _typing_for_field(fi: FieldInfo, *, ref_name_map: Dict[str, str]) -> str:
    base: str
    if fi.enum is not None:
        base = "Literal[" + ", ".join(json.dumps(x, ensure_ascii=False) for x in fi.enum) + "]"
    elif fi.ref and fi.ref in ref_name_map:
        base = ref_name_map[fi.ref]
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
            inner = _typing_for_field(fi.items, ref_name_map=ref_name_map)
        base = f"List[{inner}]"
    elif fi.json_type == "object":
        # for inline objects we generate a nested class name from the path
        base = _pascal_case(fi.path.replace("[]", "_item").replace(".", "_"))
    else:
        base = "Any"

    if fi.nullable:
        return f"Optional[{base}]"
    return base


def render_pydantic_code(schema: JsonDict, *, root_name: Optional[str] = None) -> str:
    """
    Renders a Pydantic-like representation of the JSON Schema (as a string).
    This is meant for prompt injection (not necessarily executed).
    """
    root_schema = schema
    root_title = schema.get("title") if isinstance(schema.get("title"), str) else None
    model_name = _pascal_case(root_name or root_title or "ExtractionModel")

    defs = schema.get("$defs") if isinstance(schema.get("$defs"), dict) else {}
    ref_name_map: Dict[str, str] = {}

    lines: List[str] = []
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("from typing import Any, List, Optional, Literal")
    lines.append("from pydantic import BaseModel, Field")
    lines.append("")

    # Render $defs first (enums or objects)
    if defs:
        for def_name, def_schema in defs.items():
            if not isinstance(def_schema, dict):
                continue
            def_schema = _deref(def_schema, root_schema)
            def_title = def_schema.get("title") if isinstance(def_schema.get("title"), str) else def_name
            alias_name = _pascal_case(def_title)
            ref_name_map[f"#/$defs/{def_name}"] = alias_name
            t = _schema_type(def_schema)
            if "enum" in def_schema and isinstance(def_schema.get("enum"), list):
                enum_vals = def_schema["enum"]
                lit = "Literal[" + ", ".join(json.dumps(x, ensure_ascii=False) for x in enum_vals) + "]"
                lines.append(f"{alias_name} = {lit}")
                lines.append("")
            elif t == "object":
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

    # Render root model (with nested models for inline objects)
    root_deref = _deref(schema, root_schema)
    if root_deref.get("type") == "object":
        lines.extend(
            _render_object_model(
                model_name,
                root_deref,
                root_schema,
                class_hint=model_name,
                ref_name_map=ref_name_map,
            )
        )
    else:
        lines.append(f"class {model_name}(BaseModel):")
        lines.append("    value: Any")

    return "\n".join(lines).rstrip() + "\n"


def _render_object_model(
    class_name: str,
    schema: JsonDict,
    root_schema: JsonDict,
    *,
    class_hint: str,
    ref_name_map: Dict[str, str],
) -> List[str]:
    props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    required_set = set(schema.get("required") or [])

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
            required=prop_name in required_set,
        )
        fields.append((prop_name, fi))
        if fi.json_type == "object":
            # Inline objects only (avoid duplicating $defs models)
            if not (fi.ref and fi.ref in ref_name_map):
                nested_models.append(
                    (
                        _pascal_case(fi.path.replace("[]", "_item").replace(".", "_")),
                        prop_schema,
                    )
                )
        elif fi.json_type == "array" and fi.items and fi.items.json_type == "object":
            # Inline item objects only (avoid duplicating $defs models)
            if not (fi.items.ref and fi.items.ref in ref_name_map):
                nested_models.append(
                    (
                        _pascal_case(fi.items.path.replace("[]", "_item").replace(".", "_")),
                        prop_schema.get("items", {}),
                    )
                )

    out: List[str] = []

    # Nested models first, so they are in scope for type hints
    for nested_name, nested_schema in nested_models:
        nested_deref = _deref(nested_schema, root_schema)
        # if nested schema is an anyOf nullable wrapper, unwrap for object rendering
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

    for prop_name, fi in fields:
        py_name = _safe_name(prop_name)
        type_hint = _typing_for_field(fi, ref_name_map=ref_name_map)

        field_args: List[str] = []
        if fi.description:
            field_args.append(f"description={json.dumps(fi.description, ensure_ascii=False)}")
        if fi.minimum is not None:
            field_args.append(f"ge={fi.minimum}")
        if fi.maximum is not None:
            field_args.append(f"le={fi.maximum}")
        if py_name != prop_name:
            field_args.append(f"alias={json.dumps(prop_name, ensure_ascii=False)}")

        default_expr = "..."
        if not fi.required:
            default_expr = "None"

        if field_args:
            out.append(f"    {py_name}: {type_hint} = Field({default_expr}, {', '.join(field_args)})")
        else:
            out.append(f"    {py_name}: {type_hint} = {default_expr}")

    return out


def build_enriched_prompt(
    *,
    instruction: str,
    input_text: str,
    target_schema: JsonDict,
    rules: Optional[List[str]] = None,
) -> str:
    cards = render_field_cards(target_schema)
    pydantic_code = render_pydantic_code(target_schema)
    raw = json.dumps(target_schema, indent=2, ensure_ascii=False)

    rules_block = ""
    if rules:
        rules_block = "Rules:\n" + "\n".join(f"- {r}" for r in rules) + "\n\n"

    return (
        f"{instruction.strip()}\n\n"
        f"{rules_block}"
        f"TEXT:\n{input_text}"
        #f"SCHEMA (FIELD CARDS):\n{cards}\n"
        f"SCHEMA (PYDANTIC):\n{pydantic_code}\n"
        #f"SCHEMA (RAW JSON):\n{raw}\n\n"
    )

