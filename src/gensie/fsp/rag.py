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
from gensie.pipeline.specs import ExtractionSpec, FewShotMode, ReasoningMode


FSP_RETRIEVAL_TRACE_METADATA_KEY = "_fsp_retrieval_trace"
RAG_SELECTION_MODE_OPTION = "rag_selection_mode"
RAG_SELECTION_DEFAULT = "default"
RAG_SELECTION_FIELD_TOP2_INDEPENDENT = "field_top2_independent"
RAG_SELECTION_SAME_SCHEMA_FIRST = "same_schema_first"
RAG_SELECTION_SAME_SCHEMA_SECOND = "same_schema_second"
RAG_SELECTION_MODES = frozenset(
    {
        RAG_SELECTION_DEFAULT,
        RAG_SELECTION_FIELD_TOP2_INDEPENDENT,
        RAG_SELECTION_SAME_SCHEMA_FIRST,
        RAG_SELECTION_SAME_SCHEMA_SECOND,
    }
)
RAG_SKIP_MODE_OPTION = "rag_skip_mode"
RAG_SKIP_SAME_SCHEMA = "same_schema"
RAG_SKIP_NON_SAME_SCHEMA = "non_same_schema"


@dataclass(frozen=True)
class RagExtractionFspProvider(FSPProvider):
    cases: tuple[StructuredFspCase, ...] = field(
        default_factory=default_extraction_fsp_cases
    )
    top_k: int = 1
    labels: ReasoningSectionLabels = DEFAULT_REASONING_SECTION_LABELS
    max_prompt_chars: int | None = None
    selection_mode: str = RAG_SELECTION_DEFAULT

    def __init__(
        self,
        cases: Sequence[StructuredFspCase] | None = None,
        *,
        top_k: int = 1,
        labels: ReasoningSectionLabels = DEFAULT_REASONING_SECTION_LABELS,
        max_prompt_chars: int | None = None,
        selection_mode: str = RAG_SELECTION_DEFAULT,
    ):
        selection_mode = str(selection_mode or RAG_SELECTION_DEFAULT)
        if selection_mode not in RAG_SELECTION_MODES:
            raise ValueError(f"unsupported RAG selection mode: {selection_mode}")
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
        object.__setattr__(self, "selection_mode", selection_mode)

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
            diagnostics: dict[str, object] = {}
            selected = self._retrieve_with_selection_mode(
                context,
                task_text=task_text,
                top_k=top_k,
                diagnostics=diagnostics,
            )
        except Exception as exc:
            selected = ()
            context.metadata[FSP_RETRIEVAL_TRACE_METADATA_KEY] = {
                "method": "schema_lexical",
                "selection_method": f"{self.selection_mode}_error",
                "error": str(exc) or repr(exc),
            }
        if selected:
            if diagnostics:
                context.metadata[FSP_RETRIEVAL_TRACE_METADATA_KEY] = diagnostics
            return selected
        if self.selection_mode != RAG_SELECTION_DEFAULT:
            context.metadata.setdefault(
                FSP_RETRIEVAL_TRACE_METADATA_KEY,
                {
                    "method": "ablation_rag",
                    "selection_method": self.selection_mode,
                    "selected_case_ids": [],
                },
            )
            return ()
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

    def _retrieve_with_selection_mode(
        self,
        context: PipelineContext,
        *,
        task_text: str,
        top_k: int,
        diagnostics: dict[str, object],
    ) -> tuple[FspRetrievalResult, ...]:
        if self.selection_mode == RAG_SELECTION_SAME_SCHEMA_FIRST:
            return self._retrieve_same_schema_by_corpus_index(
                context, index=0, diagnostics=diagnostics
            )
        if self.selection_mode == RAG_SELECTION_SAME_SCHEMA_SECOND:
            return self._retrieve_same_schema_by_corpus_index(
                context, index=1, diagnostics=diagnostics
            )

        from gensie.fsp.field_rag import rank_fsp_cases_by_field_embeddings

        return rank_fsp_cases_by_field_embeddings(
            task_schema=context.task.target_schema,
            task_text=task_text,
            task_id=context.task.id,
            task_instruction=context.task.instruction,
            cases=self.cases,
            top_k=top_k,
            diagnostics=diagnostics,
            use_same_schema_phase=self.selection_mode == RAG_SELECTION_DEFAULT,
            field_selection=(
                "independent_topk"
                if self.selection_mode == RAG_SELECTION_FIELD_TOP2_INDEPENDENT
                else "diverse_pair"
            ),
        )

    def _retrieve_same_schema_by_corpus_index(
        self,
        context: PipelineContext,
        *,
        index: int,
        diagnostics: dict[str, object],
    ) -> tuple[FspRetrievalResult, ...]:
        from gensie.fsp.field_rag import (
            normalized_schema_fingerprint,
            same_schema_fsp_cases,
            task_field_specs,
        )

        candidates = same_schema_fsp_cases(context.task.target_schema, self.cases)
        task_fingerprint = normalized_schema_fingerprint(context.task.target_schema)
        query_specs = task_field_specs(context.task.target_schema)
        selected_case = candidates[index] if len(candidates) > index else None
        results = (
            (
                FspRetrievalResult(
                    case=selected_case,
                    score=1.0,
                    rank=1,
                    matched_tags=(),
                    matched_terms=(),
                    schema_match=True,
                    compatible_fields=tuple(spec.name for spec in query_specs),
                    method="same_schema_corpus_order",
                ),
            )
            if selected_case is not None
            else ()
        )
        diagnostics.update(
            {
                "method": "same_schema_corpus_order",
                "selection_method": self.selection_mode,
                "task_schema_fields": [spec.name for spec in query_specs],
                "same_schema_task_fingerprint": task_fingerprint,
                "same_schema_candidates": [
                    {
                        "case_id": case.id,
                        "domain": case.domain,
                        "corpus_index": candidate_index,
                        "selected": case is selected_case,
                        "schema_fingerprint": task_fingerprint,
                    }
                    for candidate_index, case in enumerate(candidates)
                ],
                "selected_case_ids": [result.case.id for result in results],
                "considered_cases": [],
            }
        )
        return results


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


def rag_ablation_skip_reason(
    context: PipelineContext,
    extraction: ExtractionSpec,
    *,
    cases: Sequence[StructuredFspCase] | None = None,
) -> str | None:
    if extraction.few_shot is not FewShotMode.RAG:
        return None
    skip_mode = str(extraction.options.get(RAG_SKIP_MODE_OPTION) or "")
    if not skip_mode:
        return None
    if skip_mode not in {RAG_SKIP_SAME_SCHEMA, RAG_SKIP_NON_SAME_SCHEMA}:
        raise ValueError(f"unsupported RAG skip mode: {skip_mode}")

    from gensie.fsp.field_rag import has_same_schema_fsp_cases

    case_list = tuple(cases) if cases is not None else default_extraction_fsp_cases()
    has_same_schema = has_same_schema_fsp_cases(
        context.task.target_schema,
        case_list,
        min_count=2,
    )
    if skip_mode == RAG_SKIP_SAME_SCHEMA and has_same_schema:
        return "Skipped RAG ablation task because same-schema FSP examples exist."
    if skip_mode == RAG_SKIP_NON_SAME_SCHEMA and not has_same_schema:
        return "Skipped RAG ablation task because same-schema FSP examples do not exist."
    return None


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
