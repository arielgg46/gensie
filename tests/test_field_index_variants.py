from __future__ import annotations

from gensie.fsp.field_rag import (
    FIELD_INDEX_VARIANTS,
    PARTIAL_COVERED_SCHEMA_TYPES,
    resolve_field_index_tag,
    select_task_ids_for_partial_index,
    task_schema_type,
)
from gensie.task import Task


def _task(task_id: str, schema_title: str) -> Task:
    return Task(
        id=task_id,
        input_text="texto",
        instruction="instrucción",
        target_schema={
            "title": schema_title,
            "type": "object",
            "properties": {"x": {"type": "string"}},
            "required": ["x"],
        },
    )


def test_task_schema_type_uses_title():
    task = _task("a", "NewsArticle")
    assert task_schema_type(task) == "NewsArticle"


def test_resolve_field_index_tag_unknown_defaults_to_full():
    variant = resolve_field_index_tag("no-existe")
    assert variant.tag == "full"
    assert variant is FIELD_INDEX_VARIANTS["full"]


def test_resolve_field_index_tag_known_variants():
    assert resolve_field_index_tag("p25").tag == "p25"
    assert resolve_field_index_tag("p50").tag == "p50"


def test_partial_index_only_covers_selected_schema_types():
    tasks = [
        _task("news_1", "NewsArticle"),
        _task("news_2", "NewsArticle"),
        _task("news_3", "NewsArticle"),
        _task("news_4", "NewsArticle"),
        _task("ent_1", "NamedEntities"),
        _task("ent_2", "NamedEntities"),
        _task("mon_1", "MonumentBIC"),
        _task("mon_2", "MonumentBIC"),
    ]
    selected = select_task_ids_for_partial_index(
        tasks,
        fraction=0.25,
        covered_schema_types=PARTIAL_COVERED_SCHEMA_TYPES,
    )
    assert "mon_1" not in selected
    assert "mon_2" not in selected
    assert len(selected & {"news_1", "news_2", "news_3", "news_4"}) == 1
    assert len(selected & {"ent_1", "ent_2"}) == 1


def test_partial_index_p50_includes_more_than_p25():
    tasks = [_task(f"news_{i}", "NewsArticle") for i in range(8)]
    p25 = select_task_ids_for_partial_index(
        tasks,
        fraction=0.25,
        covered_schema_types=frozenset({"NewsArticle"}),
        seed=42,
    )
    p50 = select_task_ids_for_partial_index(
        tasks,
        fraction=0.50,
        covered_schema_types=frozenset({"NewsArticle"}),
        seed=42,
    )
    assert len(p25) == 2
    assert len(p50) == 4
    assert p25.issubset(p50)
