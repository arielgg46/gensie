from pathlib import Path

from gensie.cli import _resolve_eval_artifact_paths


def test_auto_output_paths_use_pipeline_and_timestamp():
    output, details_dir, timestamp = _resolve_eval_artifact_paths(
        pipeline="verbatim-entities-enriched-inline-reasoning",
        output=None,
        details_dir=None,
        auto_output_paths=True,
        run_timestamp="20260514-123456",
    )

    assert timestamp == "20260514-123456"
    assert details_dir == (
        Path("local-results")
        / "verbatim-entities-enriched-inline-reasoning"
        / "20260514-123456"
    ).absolute()
    assert output == (
        Path("local-results")
        / "verbatim-entities-enriched-inline-reasoning"
        / "20260514-123456"
        / "verbatim-entities-enriched-inline-reasoning-20260514-123456-summary.json"
    ).absolute()


def test_explicit_output_paths_win_over_auto_paths():
    explicit_output = Path("local-results/custom-summary.json")
    explicit_details = Path("local-results/custom-details")

    output, details_dir, _ = _resolve_eval_artifact_paths(
        pipeline="enriched-inline-reasoning",
        output=explicit_output,
        details_dir=explicit_details,
        auto_output_paths=True,
        run_timestamp="20260514-123456",
    )

    assert output == explicit_output.absolute()
    assert details_dir == explicit_details.absolute()
