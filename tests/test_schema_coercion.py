from gensie.schemas import coerce_nullable_string_nulls


def test_coerce_nullable_string_nulls_recursively_and_schema_aware():
    schema = {
        "$defs": {
            "Item": {
                "type": "object",
                "properties": {
                    "label": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "count": {"type": ["integer", "null"]},
                    "literal": {"type": "string"},
                },
            }
        },
        "type": "object",
        "properties": {
            "optional_text": {
                "anyOf": [{"type": "string"}, {"type": "null"}]
            },
            "non_nullable_text": {"type": "string"},
            "nullable_number": {"type": ["number", "null"]},
            "nested": {
                "type": "object",
                "properties": {
                    "child": {"oneOf": [{"type": "string"}, {"type": "null"}]},
                    "literal": {"type": "string"},
                },
            },
            "items": {"type": "array", "items": {"$ref": "#/$defs/Item"}},
            "nullable_items": {
                "type": "array",
                "items": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            },
        },
    }
    value = {
        "optional_text": " null ",
        "non_nullable_text": "null",
        "nullable_number": "NULL",
        "nested": {"child": "null", "literal": "null"},
        "items": [
            {"label": "null", "count": "null", "literal": "null"},
        ],
        "nullable_items": ["null", "kept"],
    }

    coerced = coerce_nullable_string_nulls(value, schema)

    assert coerced == {
        "optional_text": None,
        "non_nullable_text": "null",
        "nullable_number": None,
        "nested": {"child": None, "literal": "null"},
        "items": [
            {"label": None, "count": None, "literal": "null"},
        ],
        "nullable_items": [None, "kept"],
    }
    assert value["optional_text"] == " null "
