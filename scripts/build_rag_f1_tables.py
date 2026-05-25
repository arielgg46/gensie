from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


PIPELINES = (
    "enriched-schema-rag",
    "enriched-inline-reasoning-rag",
)

TABLES = (
    ("Field Tag", "field_tag", "by_field_tag.json"),
    ("Prefix", "prefix", "by_prefix.json"),
    ("Schema", "schema", "by_schema.json"),
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--metrics-dir",
        type=Path,
        default=Path("analysis/qwen3-14b-rag-golden-cover/metrics"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    output = args.output or args.metrics_dir / "f1_tables.md"
    sections = ["# F1 comparativo por extractor", ""]
    for title, row_label, filename in TABLES:
        payload = _read_json(args.metrics_dir / filename)
        sections.extend(_render_table(title, row_label, payload))
        sections.append("")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(sections), encoding="utf-8")
    print(f"wrote {output}")


def _render_table(title: str, row_label: str, payload: dict[str, Any]) -> list[str]:
    groups_by_pipeline = {
        pipeline: (payload.get("pipelines", {}).get(pipeline, {}).get("groups", {}))
        for pipeline in PIPELINES
    }
    row_keys = sorted(
        set().union(*(groups.keys() for groups in groups_by_pipeline.values())),
        key=lambda key: _row_text(row_label, key, groups_by_pipeline),
    )

    lines = [
        f"## {title}",
        "",
        (
            f"| {title} | {PIPELINES[0]} F1 | {PIPELINES[0]} n | "
            f"{PIPELINES[1]} F1 | {PIPELINES[1]} n |"
        ),
        "|---|---:|---:|---:|---:|",
    ]
    for key in row_keys:
        cells = []
        for pipeline in PIPELINES:
            group = groups_by_pipeline[pipeline].get(key)
            cells.extend(
                (
                    _format_f1(group),
                    _format_support(group),
                )
            )
        lines.append(
            f"| {_escape_pipe(_row_text(row_label, key, groups_by_pipeline))} | "
            f"{cells[0]} | {cells[1]} | {cells[2]} | {cells[3]} |"
        )
    return lines


def _format_support(group: Any) -> str:
    if not isinstance(group, dict):
        return "-"
    value = group.get("prediction_count")
    return "-" if value is None else str(int(value))


def _format_f1(group: Any) -> str:
    if not isinstance(group, dict):
        return "-"
    value = (group.get("metrics") or {}).get("f1")
    return "-" if value is None else f"{float(value):.4f}"


def _row_text(
    row_label: str,
    key: str,
    groups_by_pipeline: dict[str, dict[str, Any]],
) -> str:
    if row_label != "schema":
        return key
    group = next(
        (groups.get(key) for groups in groups_by_pipeline.values() if key in groups),
        {},
    )
    description = str(group.get("description") or "").splitlines()[0].strip()
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:8]
    return f"{description or 'schema'} [{digest}]"


def _escape_pipe(value: str) -> str:
    return value.replace("|", "\\|")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
