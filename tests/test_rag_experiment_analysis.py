import json
import shutil
from pathlib import Path

from gensie.analysis import analyze_rag_experiment_artifacts


class ExactEvaluator:
    def score_instance(self, gold, system, schema, root_schema=None):
        return 1.0 if gold == system else 0.0

    def calculate_metrics(self, tps_list, gold_counts, system_counts):
        total_tps = sum(tps_list)
        total_g = sum(gold_counts)
        total_s = sum(system_counts)
        precision = total_tps / total_s if total_s else 0.0
        recall = total_tps / total_g if total_g else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
        return {"precision": precision, "recall": recall, "f1": f1}


def test_rag_experiment_analysis_uses_golden_cover_as_reference():
    base_dir = Path("analysis/rag-experiment-analysis-test")
    shutil.rmtree(base_dir, ignore_errors=True)

    golden_dir = base_dir / "golden_cover"
    output_dir = base_dir / "analysis"
    schema_golden_dir = base_dir / "schema_golden"
    schema_dev_dir = base_dir / "schema_dev"
    inline_golden_dir = base_dir / "inline_golden"
    inline_dev_dir = base_dir / "inline_dev"
    mixed_dir = base_dir / "mixed"

    _write_json(
        golden_dir / "demo_001.json",
        {
            "id": "demo_001",
            "input_text": "Ada Lovelace",
            "instruction": "Extract the person.",
            "target_schema": {
                "type": "object",
                "description": "Demo schema",
                "properties": {
                    "name": {"type": "string", "description": "Person name"}
                },
                "required": ["name"],
            },
            "output": {"name": "Ada Lovelace"},
        },
    )

    _write_response(schema_golden_dir, "demo_001", {"name": "Ada Lovelace"})
    _write_response(schema_dev_dir, "demo_001", {"name": "Different Person"})
    _write_mixed_trial(
        mixed_dir,
        "demo_001",
        step_dir="01-self_consistency_trial_01",
        step_name="self_consistency_trial_01",
        extraction="enriched-inline-reasoning-rag",
        final_output={"name": "Ada Lovelace"},
    )
    _write_mixed_trial(
        mixed_dir,
        "demo_001",
        step_dir="02-self_consistency_trial_02",
        step_name="self_consistency_trial_02",
        extraction="enriched-schema-rag",
        final_output={"name": "Ada Lovelace"},
    )

    result = analyze_rag_experiment_artifacts(
        golden_dir=golden_dir,
        output_dir=output_dir,
        enriched_schema_golden_dir=schema_golden_dir,
        enriched_schema_dev_dir=schema_dev_dir,
        enriched_inline_golden_dir=inline_golden_dir,
        enriched_inline_dev_dir=inline_dev_dir,
        mixed_dir=mixed_dir,
        evaluator=ExactEvaluator(),
    )

    run_counts = _read_json(output_dir / "run_counts.json")
    assert run_counts["demo_001"]["enriched-schema-rag"]["count"] == 3
    assert run_counts["demo_001"]["enriched-inline-reasoning-rag"]["count"] == 1

    schema_metrics = result["metrics"]["overall"]["enriched-schema-rag"]["metrics"]
    assert schema_metrics == {
        "precision": 0.666667,
        "recall": 0.666667,
        "f1": 0.666667,
    }

    prediction = _read_json(
        output_dir
        / "predictions"
        / "enriched-schema-rag"
        / "demo_001"
        / "dev_direct.json"
    )
    assert prediction == {"name": "Different Person"}


def _write_response(run_dir: Path, task_id: str, final_output):
    _write_json(
        run_dir / task_id / "steps" / "01-extract" / "response.json",
        {"final_output": final_output},
    )


def _write_mixed_trial(
    run_dir: Path,
    task_id: str,
    *,
    step_dir: str,
    step_name: str,
    extraction: str,
    final_output,
):
    base = run_dir / task_id / "steps" / step_dir
    _write_json(
        base / "summary.json",
        {
            "step_name": step_name,
            "error": None,
            "request_metadata": {"extraction": extraction},
        },
    )
    _write_json(base / "response.json", {"final_output": final_output})


def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))
