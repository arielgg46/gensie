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
from gensie.fsp.selection import FspSelection, SelectedFspCase
from gensie.fsp.render_extraction import render_extraction_fsp_example
from gensie.pipeline.context import PipelineContext
from gensie.pipeline.specs import ExtractionSpec, ReasoningMode


FSP_RETRIEVAL_TRACE_METADATA_KEY = "_fsp_retrieval_trace"


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
        selection = self.select(context, extraction)
        examples: list[FSPExample] = []
        for selected in selection.cases:
            prompt = render_extraction_fsp_example(
                selected.case,
                extraction,
                labels=self.labels,
            )
            examples.append(
                FSPExample(
                    name=selected.case.id,
                    prompt=prompt,
                    output={},
                    metadata=selected.metadata,
                )
            )
        return tuple(examples)

    def select(
        self, context: PipelineContext, extraction: ExtractionSpec
    ) -> FspSelection:
        if extraction.reasoning is ReasoningMode.DEEP:
            return FspSelection(labels=self.labels)

        candidate_limit = (
            len(self.cases) if self.max_prompt_chars is not None else self.top_k
        )
        selected = self.retrieve(context, top_k=candidate_limit)
        cases: list[SelectedFspCase] = []
        for result in selected:
            prompt = render_extraction_fsp_example(
                result.case,
                extraction,
                labels=self.labels,
            )
            prompt_chars = len(prompt)
            if (
                self.max_prompt_chars is not None
                and prompt_chars > self.max_prompt_chars
            ):
                continue
            cases.append(
                SelectedFspCase(
                    case=result.case,
                    metadata=_metadata_for_result(
                        result,
                        extraction=extraction,
                        prompt_chars=prompt_chars,
                    ),
                )
            )
            if len(cases) >= self.top_k:
                break
        return FspSelection(cases=tuple(cases), labels=self.labels)

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
        top_k = self.top_k if top_k is None else top_k
        try:
            from gensie.fsp.field_rag import rank_fsp_cases_by_field_embeddings

            diagnostics: dict[str, object] = {}
            selected = rank_fsp_cases_by_field_embeddings(
                task_schema=task.target_schema,
                task_text=task_text,
                task_id=task.id,
                task_instruction=task.instruction,
                cases=self.cases,
                top_k=top_k,
                diagnostics=diagnostics,
            )
        except Exception as exc:
            selected = ()
            context.metadata[FSP_RETRIEVAL_TRACE_METADATA_KEY] = {
                "method": "schema_lexical",
                "selection_method": "schema_lexical_fallback",
                "error": str(exc) or repr(exc),
            }
        if selected:
            if diagnostics:
                context.metadata[FSP_RETRIEVAL_TRACE_METADATA_KEY] = diagnostics
            return selected
        selected = _mark_results_not_same_schema(
            rank_fsp_cases(
                task_schema=task.target_schema,
                task_text=task_text,
                cases=self.cases,
                top_k=top_k,
            )
        )
        if FSP_RETRIEVAL_TRACE_METADATA_KEY not in context.metadata:
            context.metadata[FSP_RETRIEVAL_TRACE_METADATA_KEY] = {
                "method": "schema_lexical",
                "selection_method": "schema_lexical_fallback",
                "selected_case_ids": [result.case.id for result in selected],
            }
        return selected


def _mark_results_not_same_schema(
    results: Sequence[FspRetrievalResult],
) -> tuple[FspRetrievalResult, ...]:
    return tuple(
        FspRetrievalResult(
            case=result.case,
            score=result.score,
            rank=result.rank,
            matched_tags=result.matched_tags,
            matched_terms=result.matched_terms,
            schema_match=False,
            compatible_fields=result.compatible_fields,
            method=result.method,
        )
        for result in results
    )


def _metadata_for_result(
    result: FspRetrievalResult,
    *,
    extraction: ExtractionSpec,
    prompt_chars: int,
) -> dict[str, object]:
    return {
        "format": "structured-rag",
        "case_id": result.case.id,
        "reasoning": extraction.reasoning.value,
        "retrieval": result.metadata(),
        "prompt_chars": prompt_chars,
    }
