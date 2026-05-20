from __future__ import annotations

import json
from typing import Sequence

from gensie.fsp.examples import (
    CandidateOrder,
    JudgeExample,
    JudgeFieldExample,
    ordered_candidates,
)


def render_judge_candidate_summary(
    judge: JudgeExample,
    field_names: Sequence[str] | None = None,
    *,
    include_support_counts: bool = True,
    candidate_order: CandidateOrder = CandidateOrder.RESOURCE,
) -> str:
    selected = tuple(judge.fields.keys() if field_names is None else field_names)
    lines = [f"Trials válidos: {judge.total_trials}"] if include_support_counts else []
    for field_name in selected:
        field = judge.fields.get(field_name)
        if field is None:
            continue
        lines.extend(
            _render_field(
                field_name,
                field,
                judge.total_trials,
                include_support_counts=include_support_counts,
                candidate_order=candidate_order,
            )
        )
    return "\n".join(lines).rstrip()


def _render_field(
    field_name: str,
    field: JudgeFieldExample,
    total_trials: int,
    *,
    include_support_counts: bool,
    candidate_order: CandidateOrder,
) -> list[str]:
    label = f"CAMPO `{field_name}` (lista)" if field.kind == "array" else f"CAMPO `{field_name}`"
    candidate_label = "Elementos candidatos:" if field.kind == "array" else "Valores candidatos:"
    lines = ["", label, candidate_label]
    for candidate in ordered_candidates(field.candidates, candidate_order):
        value = json.dumps(candidate.value, ensure_ascii=False, sort_keys=True)
        if include_support_counts:
            lines.append(f"- {candidate.support}/{total_trials}: {value}")
        else:
            lines.append(f"- {value}")

    if field.kind == "array":
        if field.empty_trial_count:
            lines.append(
                f"- Lista vacía en {field.empty_trial_count}/{total_trials} trials."
                if include_support_counts
                else "- Lista vacía."
            )
        if field.null_trial_count:
            lines.append(
                f"- Valor null en {field.null_trial_count}/{total_trials} trials."
                if include_support_counts
                else "- Valor null."
            )
        if field.invalid_value_count:
            lines.append(
                f"- Valor no-lista inválido en {field.invalid_value_count}/{total_trials} trials."
                if include_support_counts
                else "- Valor no-lista inválido."
            )
    return lines
