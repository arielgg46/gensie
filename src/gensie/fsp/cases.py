from __future__ import annotations

from importlib import resources

from gensie.fsp.examples import StructuredFspCase
from gensie.fsp.resources import load_fsp_case_resource


QUIJOTE_CULTURAL_LITERATURE_RESOURCE = "cultural_literature_quijote.json"


def quijote_cultural_literature_case() -> StructuredFspCase:
    return load_fsp_case_resource(QUIJOTE_CULTURAL_LITERATURE_RESOURCE)


def default_fsp_cases() -> tuple[StructuredFspCase, ...]:
    return _load_case_resources()


def default_extraction_fsp_cases() -> tuple[StructuredFspCase, ...]:
    return _load_case_resources(exclude=(QUIJOTE_CULTURAL_LITERATURE_RESOURCE,))


def _load_case_resources(
    *, exclude: tuple[str, ...] = ()
) -> tuple[StructuredFspCase, ...]:
    excluded = set(exclude)
    case_dir = resources.files("gensie.fsp").joinpath("resources", "cases")
    names = sorted(
        item.name
        for item in case_dir.iterdir()
        if item.name.endswith(".json") and item.name not in excluded
    )
    return tuple(load_fsp_case_resource(name) for name in names)
