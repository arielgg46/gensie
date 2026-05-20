from __future__ import annotations

from gensie.fsp.examples import StructuredFspCase
from gensie.fsp.resources import load_fsp_case_resource


def quijote_cultural_literature_case() -> StructuredFspCase:
    return load_fsp_case_resource("cultural_literature_quijote.json")


def default_fsp_cases() -> tuple[StructuredFspCase, ...]:
    return (quijote_cultural_literature_case(),)
