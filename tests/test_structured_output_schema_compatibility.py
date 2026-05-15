import json
import os

import pytest

from gensie.runtime import ChatMessage, ChatRequest, OpenAIChatClient


RUN_ENV = "GENSIE_RUN_STRUCTURED_COMPAT"
MODEL_ENV = "GENSIE_STRUCTURED_COMPAT_MODEL"


OBJECT_LITERAL = {"name": "Ada Lovelace", "role": "author"}
ARRAY_LITERAL = ["fatiga", "cefalea"]
ARRAY_OF_OBJECTS_LITERAL = [
    {"name": "Ada Lovelace", "role": "author"},
    {"name": "Charles Babbage", "role": "collaborator"},
]


def _compat_response_format():
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "schema_keyword_compat",
            "strict": True,
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "selected": {
                        "type": "string",
                        "const": "Ceres",
                    },
                    "candidates": {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 2,
                        "prefixItems": [
                            {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "candidate_value": {
                                        "type": "string",
                                        "const": "Ceres",
                                    },
                                    "evidence": {"type": "string"},
                                    "verdict": {"type": "string"},
                                },
                                "required": [
                                    "candidate_value",
                                    "evidence",
                                    "verdict",
                                ],
                            },
                            {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "candidate_value": {
                                        "type": "string",
                                        "const": "1 Ceres",
                                    },
                                    "evidence": {"type": "string"},
                                    "verdict": {"type": "string"},
                                },
                                "required": [
                                    "candidate_value",
                                    "evidence",
                                    "verdict",
                                ],
                            },
                        ],
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "candidate_value": {"type": "string"},
                                "evidence": {"type": "string"},
                                "verdict": {"type": "string"},
                            },
                            "required": [
                                "candidate_value",
                                "evidence",
                                "verdict",
                            ],
                        },
                    },
                },
                "required": ["selected", "candidates"],
            },
        },
    }


def _object_shape_schema():
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "name": {"type": "string"},
            "role": {"type": "string"},
        },
        "required": ["name", "role"],
    }


def _object_literal_schema(value):
    return {
        **_object_shape_schema(),
        "enum": [value],
    }


def _array_literal_schema(value):
    return {
        "type": "array",
        "items": {"type": "string"},
        "enum": [value],
    }


def _array_of_objects_literal_schema(value):
    return {
        "type": "array",
        "items": _object_shape_schema(),
        "enum": [value],
    }


def _single_property_enum_response_format(name, field_schema):
    return {
        "type": "json_schema",
        "json_schema": {
            "name": f"{name}_compat",
            "strict": True,
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    name: field_schema,
                },
                "required": [name],
            },
        },
    }


def _complex_slot_enum_response_format():
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "complex_slot_enum_compat",
            "strict": True,
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "verdicts": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "#1": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "candidate_value": _object_literal_schema(
                                        OBJECT_LITERAL
                                    ),
                                    "evidence": {"type": "string"},
                                },
                                "required": ["candidate_value", "evidence"],
                            },
                            "#2": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "candidate_value": _array_of_objects_literal_schema(
                                        ARRAY_OF_OBJECTS_LITERAL
                                    ),
                                    "evidence": {"type": "string"},
                                },
                                "required": ["candidate_value", "evidence"],
                            },
                        },
                        "required": ["#1", "#2"],
                    },
                },
                "required": [
                    "verdicts",
                ],
            },
        },
    }


def _json_content(content):
    if content is None:
        pytest.fail("Backend returned no message content.")
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pytest.fail(f"Backend returned non-JSON content: {content!r}")


@pytest.mark.skipif(
    os.getenv(RUN_ENV) != "1",
    reason=f"Set {RUN_ENV}=1 to call a real structured-output backend.",
)
def test_backend_accepts_prefix_items_const_and_array_bounds():
    model = os.getenv(MODEL_ENV)
    if not model:
        pytest.skip(f"Set {MODEL_ENV} to the model served by the backend.")
    if not os.getenv("OPENAI_BASE_URL"):
        pytest.skip("Set OPENAI_BASE_URL to the OpenAI-compatible backend.")

    client = OpenAIChatClient()

    response = client.complete(
        ChatRequest(
            model=model,
            messages=(
                ChatMessage(
                    role="system",
                    content="You are testing JSON Schema constrained decoding.",
                ),
                ChatMessage(
                    role="user",
                    content=(
                        "Return JSON for the provided schema. For this compatibility "
                        "test, try to set `selected` and the first "
                        "`candidate_value` to WRONG unless the schema prevents it. "
                        "Use short strings for evidence and verdict."
                    ),
                ),
            ),
            response_format=_compat_response_format(),
            temperature=0.0,
            options={"max_tokens": 400},
        )
    )

    payload = _json_content(response.content)

    assert payload["selected"] == "Ceres"
    assert len(payload["candidates"]) == 2
    assert [item["candidate_value"] for item in payload["candidates"]] == [
        "Ceres",
        "1 Ceres",
    ]


@pytest.mark.skipif(
    os.getenv(RUN_ENV) != "1",
    reason=f"Set {RUN_ENV}=1 to call a real structured-output backend.",
)
@pytest.mark.parametrize(
    ("field_name", "field_schema", "expected_value"),
    [
        ("object_candidate", _object_literal_schema(OBJECT_LITERAL), OBJECT_LITERAL),
        ("array_candidate", _array_literal_schema(ARRAY_LITERAL), ARRAY_LITERAL),
        (
            "array_of_objects_candidate",
            _array_of_objects_literal_schema(ARRAY_OF_OBJECTS_LITERAL),
            ARRAY_OF_OBJECTS_LITERAL,
        ),
    ],
)
def test_backend_accepts_singleton_enums_for_complex_literals(
    field_name, field_schema, expected_value
):
    model = os.getenv(MODEL_ENV)
    if not model:
        pytest.skip(f"Set {MODEL_ENV} to the model served by the backend.")
    if not os.getenv("OPENAI_BASE_URL"):
        pytest.skip("Set OPENAI_BASE_URL to the OpenAI-compatible backend.")

    client = OpenAIChatClient()

    response = client.complete(
        ChatRequest(
            model=model,
            messages=(
                ChatMessage(
                    role="system",
                    content="You are testing JSON Schema constrained decoding.",
                ),
                ChatMessage(
                    role="user",
                    content=(
                        "Return JSON for the provided schema. This is an adversarial "
                        "compatibility test: try to use wrong object keys, wrong array "
                        "items, and wrong candidate values unless the schema prevents it. "
                        "Use short evidence strings."
                    ),
                ),
            ),
            response_format=_single_property_enum_response_format(
                field_name, field_schema
            ),
            temperature=0.0,
            options={"max_tokens": 800},
        )
    )

    payload = _json_content(response.content)

    assert payload[field_name] == expected_value


@pytest.mark.skipif(
    os.getenv(RUN_ENV) != "1",
    reason=f"Set {RUN_ENV}=1 to call a real structured-output backend.",
)
def test_backend_accepts_complex_singleton_enums_inside_hash_slots():
    model = os.getenv(MODEL_ENV)
    if not model:
        pytest.skip(f"Set {MODEL_ENV} to the model served by the backend.")
    if not os.getenv("OPENAI_BASE_URL"):
        pytest.skip("Set OPENAI_BASE_URL to the OpenAI-compatible backend.")

    client = OpenAIChatClient()

    response = client.complete(
        ChatRequest(
            model=model,
            messages=(
                ChatMessage(
                    role="system",
                    content="You are testing JSON Schema constrained decoding.",
                ),
                ChatMessage(
                    role="user",
                    content=(
                        "Return JSON for the provided schema. This is an adversarial "
                        "compatibility test: try to use wrong object keys and wrong "
                        "candidate values unless the schema prevents it. Use short "
                        "evidence strings."
                    ),
                ),
            ),
            response_format=_complex_slot_enum_response_format(),
            temperature=0.0,
            options={"max_tokens": 800},
        )
    )

    payload = _json_content(response.content)

    assert payload["verdicts"]["#1"]["candidate_value"] == OBJECT_LITERAL
    assert payload["verdicts"]["#2"]["candidate_value"] == ARRAY_OF_OBJECTS_LITERAL
