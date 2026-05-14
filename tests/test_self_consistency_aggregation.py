from gensie.aggregation import (
    LexicalStringSimilarity,
    SchemaAwareSelfConsistencyAggregator,
    SelfConsistencyConfig,
)
from gensie.aggregation.clustering import HeuristicIdentityFieldSelector


def _aggregator(**config_overrides):
    return SchemaAwareSelfConsistencyAggregator(
        config=SelfConsistencyConfig(**config_overrides),
        string_similarity=LexicalStringSimilarity(),
    )


def test_string_fields_use_cluster_medoid_not_exact_repetition():
    schema = {"type": "object", "properties": {"summary": {"type": "string"}}}
    outputs = [
        {"summary": "dolor en el sitio de inyeccion"},
        {"summary": "dolor en sitio de inyeccion"},
        {"summary": "cefalea aislada"},
    ]

    result = _aggregator(scalar_string_threshold=0.65).aggregate(outputs, schema)

    assert "dolor" in result["summary"]
    assert "cefalea" not in result["summary"]


def test_array_of_strings_is_built_item_wise():
    schema = {
        "type": "object",
        "properties": {
            "symptoms": {"type": "array", "items": {"type": "string"}},
        },
    }
    outputs = [
        {"symptoms": ["fatiga", "cefalea"]},
        {"symptoms": ["cefalea", "dolor en sitio de inyeccion"]},
        {"symptoms": ["fatiga", "dolor en el sitio de inyeccion"]},
    ]

    result = _aggregator(array_string_threshold=0.65).aggregate(outputs, schema)

    assert set(result["symptoms"]) >= {"fatiga", "cefalea"}
    assert any("dolor" in item for item in result["symptoms"])
    assert result["symptoms"] not in [output["symptoms"] for output in outputs]


def test_identity_field_selector_prefers_entity_text_fields():
    selector = HeuristicIdentityFieldSelector()
    config = SelfConsistencyConfig()
    schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "label": {"type": "string", "enum": ["PERSON", "LOCATION"]},
        },
        "required": ["text", "label"],
    }

    decision = selector.select(schema, schema, config=config)

    assert decision.field_name == "text"


def test_array_of_objects_uses_identity_field_before_aggregating_subfields():
    schema = {
        "type": "object",
        "properties": {
            "entities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "text": {"type": "string"},
                        "label": {
                            "type": "string",
                            "enum": ["LOCATION", "MISCELLANEOUS"],
                        },
                    },
                    "required": ["text", "label"],
                },
            },
        },
    }
    outputs = [
        {"entities": [{"text": "Nakatomi", "label": "LOCATION"}]},
        {"entities": [{"text": "Nakatomi", "label": "MISCELLANEOUS"}]},
        {"entities": [{"text": "Nakatomi", "label": "LOCATION"}]},
    ]

    result, diagnostics = _aggregator().aggregate_with_diagnostics(outputs, schema)

    assert result["entities"] == [{"text": "Nakatomi", "label": "LOCATION"}]
    assert diagnostics["fields"]["entities"]["cluster_similarity"] == "identity_field"
