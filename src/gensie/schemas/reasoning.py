from __future__ import annotations

import copy
from typing import Any

from gensie.schemas.clean import clean_schema_for_prompt
from gensie.schemas.inspect import JsonDict, deref, schema_type, unwrap_nullable_anyof

REASONING_FIELD_DESCRIPTION = (
    "Reason about the field using source-text evidence, then put the final answer in value."
)


def transform_schema_for_reasoning(
    schema: JsonDict, reasoning: Any
) -> JsonDict:
    mode = _reasoning_value(reasoning)
    if mode == "none":
        return copy.deepcopy(schema)
    if mode == "top_level":
        return build_inline_reasoning_schema(schema)
    if mode == "deep":
        return build_deep_inline_reasoning_schema(schema)
    raise ValueError(f"unsupported reasoning mode: {reasoning}")


def unwrap_reasoning_output(
    raw_output: JsonDict, original_schema: JsonDict, reasoning: Any
) -> JsonDict:
    mode = _reasoning_value(reasoning)
    if mode == "none":
        return raw_output
    if mode == "top_level":
        return unwrap_inline_reasoning_output(raw_output, original_schema)
    if mode == "deep":
        return unwrap_deep_inline_reasoning_output(raw_output, original_schema)
    raise ValueError(f"unsupported reasoning mode: {reasoning}")


def build_inline_reasoning_schema(schema: JsonDict) -> JsonDict:
    original = copy.deepcopy(schema)
    properties = original.get("properties")
    if original.get("type") != "object" or not isinstance(properties, dict):
        raise ValueError("inline reasoning requires a root object schema with properties")

    wrapped_properties = {
        field_name: _reasoning_wrapper_schema(field_schema)
        for field_name, field_schema in properties.items()
        if isinstance(field_schema, dict)
    }
    reasoning_schema: JsonDict = {
        "type": "object",
        "additionalProperties": False,
        "properties": wrapped_properties,
        "required": list(wrapped_properties),
    }
    if "$defs" in original:
        reasoning_schema["$defs"] = original["$defs"]
    if "description" in original:
        reasoning_schema["description"] = "Inline reasoning wrapper for: " + str(original["description"])
    if "title" in original:
        reasoning_schema["title"] = str(original["title"]) + "InlineReasoning"
    return reasoning_schema


def build_inline_reasoning_prompt_schema(schema: JsonDict) -> JsonDict:
    clean_schema, _ = clean_schema_for_prompt(schema)
    properties = clean_schema.get("properties")
    if clean_schema.get("type") != "object" or not isinstance(properties, dict):
        raise ValueError("inline reasoning prompt schema requires a root object schema")

    wrapped_properties: dict[str, Any] = {}
    for field_name, field_schema in properties.items():
        if not isinstance(field_schema, dict):
            continue
        value_schema = copy.deepcopy(field_schema)
        field_description = value_schema.pop("description", None)
        wrapped_field: JsonDict = {
            "type": "object",
            "properties": {
                "reasoning": {"type": "string"},
                "value": value_schema,
            },
        }
        if field_description:
            wrapped_field["description"] = field_description
        wrapped_properties[field_name] = wrapped_field

    prompt_schema: JsonDict = {"type": "object", "properties": wrapped_properties}
    if "$defs" in clean_schema:
        prompt_schema["$defs"] = clean_schema["$defs"]
    return prompt_schema


def unwrap_inline_reasoning_output(raw_output: JsonDict, original_schema: JsonDict) -> JsonDict:
    properties = original_schema.get("properties")
    if not isinstance(properties, dict):
        raise ValueError("original schema has no root properties")
    if not isinstance(raw_output, dict):
        raise ValueError("inline reasoning output must be a JSON object")

    output: JsonDict = {}
    for field_name in properties:
        wrapped_field = raw_output.get(field_name)
        if not isinstance(wrapped_field, dict) or "value" not in wrapped_field:
            raise ValueError(f"missing inline reasoning value for field: {field_name}")
        output[field_name] = wrapped_field["value"]
    return output


def build_deep_inline_reasoning_schema(schema: JsonDict) -> JsonDict:
    original = copy.deepcopy(schema)
    properties = original.get("properties")
    if original.get("type") != "object" or not isinstance(properties, dict):
        raise ValueError("deep inline reasoning requires a root object schema with properties")

    defs = original.get("$defs") if isinstance(original.get("$defs"), dict) else {}
    transformed_defs = {
        def_name: _deep_reasoning_value_schema(def_schema)
        for def_name, def_schema in defs.items()
        if isinstance(def_schema, dict)
    }
    wrapped_properties = {
        field_name: _reasoning_wrapper_schema(_deep_reasoning_value_schema(field_schema))
        for field_name, field_schema in properties.items()
        if isinstance(field_schema, dict)
    }

    reasoning_schema: JsonDict = {
        "type": "object",
        "additionalProperties": False,
        "properties": wrapped_properties,
        "required": list(wrapped_properties),
    }
    if transformed_defs:
        reasoning_schema["$defs"] = transformed_defs
    if "description" in original:
        reasoning_schema["description"] = "Deep inline reasoning wrapper for: " + str(original["description"])
    if "title" in original:
        reasoning_schema["title"] = str(original["title"]) + "DeepInlineReasoning"
    return reasoning_schema


def unwrap_deep_inline_reasoning_output(raw_output: JsonDict, original_schema: JsonDict) -> JsonDict:
    if not isinstance(raw_output, dict):
        raise ValueError("deep inline reasoning output must be a JSON object")
    root_schema = original_schema
    schema = deref(original_schema, root_schema)
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        raise ValueError("original schema has no root properties")
    return _unwrap_deep_reasoned_object(raw_output, schema, root_schema, root=True)


def _reasoning_wrapper_schema(value_schema: JsonDict) -> JsonDict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "reasoning": {"type": "string", "description": REASONING_FIELD_DESCRIPTION},
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
        schema["anyOf"] = [
            _deep_reasoning_value_schema(alternative)
            if isinstance(alternative, dict) and alternative.get("type") != "null"
            else copy.deepcopy(alternative)
            for alternative in any_of
        ]
        return schema

    current_type = schema.get("type")
    if current_type == "object":
        properties = schema.get("properties")
        if isinstance(properties, dict):
            wrapped_properties = {
                name: _reasoning_wrapper_schema(_deep_reasoning_value_schema(property_schema))
                for name, property_schema in properties.items()
                if isinstance(property_schema, dict)
            }
            schema["properties"] = wrapped_properties
            schema["required"] = list(wrapped_properties)
            schema["additionalProperties"] = False
        return schema

    if current_type == "array":
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            schema["items"] = _reasoning_wrapper_schema(_deep_reasoning_value_schema(item_schema))
        return schema

    return schema


def _unwrap_deep_reasoned_wrapper(value: Any, schema: JsonDict, root_schema: JsonDict) -> Any:
    if not isinstance(value, dict) or "value" not in value:
        raise ValueError("missing deep inline reasoning value wrapper")
    return _unwrap_deep_reasoned_value(value["value"], schema, root_schema)


def _unwrap_deep_reasoned_value(value: Any, schema: JsonDict, root_schema: JsonDict) -> Any:
    schema, nullable = unwrap_nullable_anyof(schema, root_schema)
    schema = deref(schema, root_schema)
    if value is None:
        return None

    current_type = schema_type(schema)
    if current_type == "array":
        item_schema = schema.get("items") if isinstance(schema.get("items"), dict) else {}
        if not isinstance(value, list):
            raise ValueError("expected list value in deep inline reasoning output")
        return [_unwrap_deep_reasoned_wrapper(item, item_schema, root_schema) for item in value]

    if current_type == "object":
        if not isinstance(value, dict):
            raise ValueError("expected object value in deep inline reasoning output")
        return _unwrap_deep_reasoned_object(value, schema, root_schema, root=False)

    return value


def _unwrap_deep_reasoned_object(
    value: JsonDict, schema: JsonDict, root_schema: JsonDict, *, root: bool
) -> JsonDict:
    properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    required = set(properties if root else schema.get("required") or [])
    output: JsonDict = {}
    for name, property_schema in properties.items():
        if name not in value:
            if name in required:
                raise ValueError(f"missing deep inline reasoning field: {name}")
            continue
        if not isinstance(property_schema, dict):
            continue
        output[name] = _unwrap_deep_reasoned_wrapper(value[name], property_schema, root_schema)
    return output


def _reasoning_value(reasoning: Any) -> str:
    value = getattr(reasoning, "value", reasoning)
    return str(value)
