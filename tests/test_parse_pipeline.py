from gensie.parse_pipeline import (
    _overlay_rich_schema,
    _validate_scope,
)


def test_overlay_adds_description_without_changing_keys():
    base = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
        },
        "required": ["name"],
        "additionalProperties": False,
    }
    refined = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Full person name",
            },
        },
        "required": ["name"],
    }
    merged = _overlay_rich_schema(base, refined)
    assert merged["properties"]["name"]["description"] == "Full person name"
    assert merged["required"] == ["name"]


def test_validate_scope_required_from_base_only():
    base = {
        "type": "object",
        "properties": {
            "a": {"type": "string"},
        },
        "required": ["a"],
        "additionalProperties": False,
    }
    rules = base
    errors = _validate_scope("hello", base, rules, {})
    assert any("Missing or null required" in e for e in errors)


def test_validate_scope_grounding_and_pattern():
    base = {
        "type": "object",
        "properties": {
            "code": {"type": "string"},
        },
        "additionalProperties": False,
    }
    rules = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "pattern": "^[A-Z]{3}$"},
        },
        "additionalProperties": False,
    }
    err = _validate_scope(
        "no code here",
        base,
        rules,
        {"code": "ZZZ"},
    )
    assert any("Grounding" in e for e in err)

    ok = _validate_scope(
        "The code is ABC today",
        base,
        rules,
        {"code": "ABC"},
    )
    assert ok == []
