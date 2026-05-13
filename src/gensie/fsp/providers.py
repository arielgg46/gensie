from __future__ import annotations

from dataclasses import dataclass

from gensie.fsp.base import FSPExample
from gensie.pipeline.context import PipelineContext
from gensie.pipeline.specs import ExtractionSpec


class NoFSPProvider:
    def examples(
        self, context: PipelineContext, extraction: ExtractionSpec
    ) -> tuple[FSPExample, ...]:
        del context, extraction
        return ()


@dataclass(frozen=True)
class StaticFSPProvider:
    items: tuple[FSPExample, ...]

    def __init__(self, items: tuple[FSPExample, ...] | list[FSPExample]):
        object.__setattr__(self, "items", tuple(items))

    def examples(
        self, context: PipelineContext, extraction: ExtractionSpec
    ) -> tuple[FSPExample, ...]:
        del context, extraction
        return self.items


@dataclass(frozen=True)
class TextFSPProvider:
    name: str
    text: str

    def examples(
        self, context: PipelineContext, extraction: ExtractionSpec
    ) -> tuple[FSPExample, ...]:
        del context, extraction
        return (
            FSPExample(
                name=self.name,
                prompt=self.text,
                output={},
                metadata={"format": "pre-rendered"},
            ),
        )
