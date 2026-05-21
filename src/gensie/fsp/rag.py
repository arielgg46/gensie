from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from gensie.fsp.base import FSPExample, FSPProvider
from gensie.fsp.cases import default_extraction_fsp_cases
from gensie.fsp.examples import (
    DEFAULT_REASONING_SECTION_LABELS,
    ReasoningSectionLabels,
    StructuredFspCase,
)
from gensie.fsp.retrieval import FspRetrievalResult, rank_fsp_cases
from gensie.fsp.render_extraction import render_extraction_fsp_example
from gensie.pipeline.context import PipelineContext
from gensie.pipeline.specs import ExtractionSpec, ReasoningMode


@dataclass(frozen=True)
class RagExtractionFspProvider(FSPProvider):
    cases: tuple[StructuredFspCase, ...] = field(
        default_factory=default_extraction_fsp_cases
    )
    top_k: int = 1
    labels: ReasoningSectionLabels = DEFAULT_REASONING_SECTION_LABELS
    max_prompt_chars: int | None = None

    def __init__(
        self,
        cases: Sequence[StructuredFspCase] | None = None,
        *,
        top_k: int = 1,
        labels: ReasoningSectionLabels = DEFAULT_REASONING_SECTION_LABELS,
        max_prompt_chars: int | None = None,
    ):
        object.__setattr__(
            self,
            "cases",
            tuple(cases) if cases is not None else default_extraction_fsp_cases(),
        )
        object.__setattr__(self, "top_k", max(1, top_k))
        object.__setattr__(self, "labels", labels)
        if max_prompt_chars is not None and max_prompt_chars < 1:
            max_prompt_chars = None
        object.__setattr__(self, "max_prompt_chars", max_prompt_chars)

    def examples(
        self, context: PipelineContext, extraction: ExtractionSpec
    ) -> tuple[FSPExample, ...]:
        if extraction.reasoning is ReasoningMode.DEEP:
            return ()

        candidate_limit = (
            len(self.cases) if self.max_prompt_chars is not None else self.top_k
        )
        selected = self.retrieve(context, top_k=candidate_limit)
        examples: list[FSPExample] = []
        for result in selected:
            prompt = render_extraction_fsp_example(
                result.case,
                extraction,
                labels=self.labels,
            )
            if (
                self.max_prompt_chars is not None
                and len(prompt) > self.max_prompt_chars
            ):
                continue
            examples.append(
                FSPExample(
                    name=result.case.id,
                    prompt=prompt,
                    output={},
                    metadata={
                        "format": "structured-rag",
                        "case_id": result.case.id,
                        "reasoning": extraction.reasoning.value,
                        "retrieval": result.metadata(),
                    },
                )
            )
            if len(examples) >= self.top_k:
                break
        return tuple(examples)

    def retrieve(
        self, context: PipelineContext, *, top_k: int | None = None
    ) -> tuple[FspRetrievalResult, ...]:
        task = context.task
        task_text = " ".join(
            (
                task.id,
                task.instruction,
                str(task.target_schema.get("description") or ""),
            )
        )
        return rank_fsp_cases(
            task_schema=task.target_schema,
            task_text=task_text,
            cases=self.cases,
            top_k=self.top_k if top_k is None else top_k,
        )
