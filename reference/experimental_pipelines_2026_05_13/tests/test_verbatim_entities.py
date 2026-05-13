import shutil
import uuid
from pathlib import Path
from types import SimpleNamespace

from gensie.verbatim_entities import (
    VERBATIM_ENTITY_FIELDS,
    build_verbatim_entity_prompt,
    build_verbatim_entity_response_format,
    build_verbatim_entity_schema,
    evaluate_verbatim_entity_tasks,
    extract_verbatim_entities,
    flatten_verbatim_entities,
    normalize_verbatim_entities,
    parse_verbatim_entity_response,
    score_verbatim_entities,
)


def test_verbatim_entity_schema_has_required_string_lists():
    schema = build_verbatim_entity_schema()

    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert tuple(schema["required"]) == VERBATIM_ENTITY_FIELDS
    assert tuple(schema["properties"]) == VERBATIM_ENTITY_FIELDS
    for field_name in VERBATIM_ENTITY_FIELDS:
        field_schema = schema["properties"][field_name]
        assert field_schema["type"] == "array"
        assert field_schema["items"] == {"type": "string"}


def test_verbatim_entity_prompt_requires_literal_grounded_entities():
    prompt = build_verbatim_entity_prompt(
        "Madrid, 14 de abril de 2026. Lucia Ferrer presento Atlas-IE."
    )

    assert "Extrae entidades verbatim" in prompt
    assert "Copia cada entidad exactamente como aparece" in prompt
    assert "No normalices fechas" in prompt
    assert "No inventes entidades" in prompt
    assert "Madrid, 14 de abril de 2026" in prompt


def test_parse_and_normalize_verbatim_entities_preserves_known_string_lists():
    parsed = parse_verbatim_entity_response(
        """
        {
          "personas": [" Lucia Ferrer ", "Lucia Ferrer", 12],
          "organizaciones": ["Instituto Iberico de IA"],
          "fechas": "2026",
          "lugares": ["Madrid", ""],
          "otros": ["Atlas-IE"],
          "extra": ["ignored"]
        }
        """
    )

    assert parsed == {
        "personas": ["Lucia Ferrer"],
        "organizaciones": ["Instituto Iberico de IA"],
        "fechas": [],
        "lugares": ["Madrid"],
        "otros": ["Atlas-IE"],
    }


def test_extract_verbatim_entities_calls_slm_once_with_strict_schema():
    calls = []
    content = (
        '{"personas":["Lucia Ferrer"],'
        '"organizaciones":["Instituto Iberico de IA"],'
        '"fechas":["14 de abril de 2026"],'
        '"lugares":["Madrid"],'
        '"otros":["Atlas-IE"]}'
    )

    class FakeCompletions:
        def create(self, **kwargs):
            calls.append(kwargs)
            message = SimpleNamespace(content=content)
            choice = SimpleNamespace(message=message)
            return SimpleNamespace(choices=[choice])

    class FakeClient:
        chat = SimpleNamespace(completions=FakeCompletions())

    result = extract_verbatim_entities(
        "Madrid, 14 de abril de 2026. Lucia Ferrer presento Atlas-IE.",
        "dummy-model",
        client=FakeClient(),
    )

    assert len(calls) == 1
    assert result == {
        "personas": ["Lucia Ferrer"],
        "organizaciones": ["Instituto Iberico de IA"],
        "fechas": ["14 de abril de 2026"],
        "lugares": ["Madrid"],
        "otros": ["Atlas-IE"],
    }
    call = calls[0]
    assert call["model"] == "dummy-model"
    assert call["temperature"] == 0.0
    assert call["messages"][0]["role"] == "system"
    assert call["messages"][1]["role"] == "user"
    assert call["response_format"] == build_verbatim_entity_response_format()


def test_normalize_verbatim_entities_fills_missing_fields():
    assert normalize_verbatim_entities({}) == {
        "personas": [],
        "organizaciones": [],
        "fechas": [],
        "lugares": [],
        "otros": [],
    }


def test_flatten_verbatim_entities_returns_one_deduped_list():
    flattened = flatten_verbatim_entities(
        {
            "personas": ["Ada Lovelace", "Ada Lovelace"],
            "organizaciones": ["Royal Society"],
            "fechas": ["1843"],
            "lugares": ["Londres", "Royal Society"],
            "otros": ["Maquina Analitica"],
        }
    )

    assert flattened == [
        "Ada Lovelace",
        "Royal Society",
        "1843",
        "Londres",
        "Maquina Analitica",
    ]


def test_score_verbatim_entities_reports_micro_and_field_errors():
    score = score_verbatim_entities(
        {
            "personas": ["Ada Lovelace", "Alan Turing"],
            "organizaciones": ["Royal Society"],
            "fechas": [],
            "lugares": ["Londres"],
            "otros": [],
        },
        {
            "personas": ["Ada Lovelace"],
            "organizaciones": [],
            "fechas": ["1843"],
            "lugares": ["Londres"],
            "otros": [],
        },
    )

    assert score["exact_match"] is False
    assert score["micro"]["true_positives"] == 2
    assert score["micro"]["false_positives"] == 2
    assert score["micro"]["false_negatives"] == 1
    assert score["micro"]["precision"] == 0.5
    assert score["micro"]["recall"] == 2 / 3
    assert score["fields"]["personas"]["extra"] == ["Alan Turing"]
    assert score["fields"]["fechas"]["missing"] == ["1843"]


def test_evaluate_verbatim_entity_tasks_runs_folder_and_writes_report():
    base_dir = Path("test-artifacts") / f"verbatim-{uuid.uuid4().hex}"
    task_dir = base_dir / "entities"
    try:
        task_dir.mkdir(parents=True)
        (task_dir / "task_a.json").write_text(
            """
            {
              "input_text": "Ada trabajo en Londres en 1843.",
              "output": {
                "personas": ["Ada"],
                "organizaciones": [],
                "fechas": ["1843"],
                "lugares": ["Londres"],
                "otros": []
              }
            }
            """,
            encoding="utf-8",
        )
        (task_dir / "task_b.json").write_text(
            """
            {
              "input_text": "La NASA lanzo MESSENGER.",
              "output": {
                "personas": [],
                "organizaciones": ["NASA"],
                "fechas": [],
                "lugares": [],
                "otros": ["MESSENGER"]
              }
            }
            """,
            encoding="utf-8",
        )
        predictions = {
            "Ada trabajo en Londres en 1843.": {
                "personas": ["Ada"],
                "organizaciones": [],
                "fechas": [],
                "lugares": ["Londres"],
                "otros": [],
            },
            "La NASA lanzo MESSENGER.": {
                "personas": [],
                "organizaciones": ["NASA"],
                "fechas": [],
                "lugares": [],
                "otros": ["MESSENGER", "lanzo"],
            },
        }
        out = base_dir / "report.json"

        report = evaluate_verbatim_entity_tasks(
            task_dir,
            "dummy-model",
            extractor=lambda text: predictions[text],
            output_path=out,
            artifacts_dir=base_dir / "artifacts",
        )

        assert out.exists()
        task_a_dir = base_dir / "artifacts" / "task_a"
        assert (task_a_dir / "prompt.txt").exists()
        assert (task_a_dir / "output.json").exists()
        assert (task_a_dir / "gold.json").exists()
        assert (task_a_dir / "metrics.json").exists()
        assert "SYSTEM:" in (task_a_dir / "prompt.txt").read_text(encoding="utf-8")
        assert "Ada trabajo en Londres" in (task_a_dir / "prompt.txt").read_text(
            encoding="utf-8"
        )
        assert '"personas": [' in (task_a_dir / "output.json").read_text(
            encoding="utf-8"
        )
        assert report["task_count"] == 2
        assert report["exact_match_rate"] == 0.0
        assert report["micro"]["true_positives"] == 4
        assert report["micro"]["false_positives"] == 1
        assert report["micro"]["false_negatives"] == 1
        assert report["fields"]["fechas"]["false_negatives"] == 1
        assert report["fields"]["otros"]["false_positives"] == 1
        assert [task["id"] for task in report["tasks"]] == ["task_a", "task_b"]
        assert Path(report["tasks"][0]["artifact_dir"]).name == "task_a"
    finally:
        if base_dir.exists():
            shutil.rmtree(base_dir)
