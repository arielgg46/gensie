from __future__ import annotations

from gensie.fsp.examples import JudgeExample, StructuredFspCase
from gensie.schemas.projection import build_reduced_schema


def project_structured_fsp_case(
    case: StructuredFspCase,
    field_names: tuple[str, ...] | list[str],
    *,
    include_stable_fields: bool = True,
) -> StructuredFspCase:
    field_order = tuple(dict.fromkeys(str(name) for name in field_names))
    field_set = set(field_order)
    projected_judge = None
    if case.judge is not None:
        projected_judge = JudgeExample(
            total_trials=case.judge.total_trials,
            stable_fields=case.judge.stable_fields if include_stable_fields else {},
            fields={
                name: case.judge.fields[name]
                for name in field_order
                if name in case.judge.fields
            },
        )

    return StructuredFspCase(
        id=case.id,
        domain=case.domain,
        language=case.language,
        source_text=case.source_text,
        instruction=case.instruction,
        schema=build_reduced_schema(case.schema, field_order),
        field_examples={
            name: case.field_examples[name]
            for name in field_order
            if name in case.field_examples and name in field_set
        },
        enriched_field_descriptions={
            path: description
            for path, description in case.enriched_field_descriptions.items()
            if _top_level_field_path(path) in field_set
        },
        tags=case.tags,
        judge=projected_judge,
    )


def _top_level_field_path(path: str) -> str:
    top_level = path.split(".", 1)[0]
    return top_level.removesuffix("[]")
