from __future__ import annotations

from dataclasses import dataclass
from math import floor

from gensie.pipeline.specs import ExtractionSpec, SamplingSpec


@dataclass(frozen=True)
class TrialPlanItem:
    index: int
    group_index: int
    group_trial_index: int
    group_name: str
    extraction: ExtractionSpec


def resolve_group_counts(sampling: SamplingSpec) -> tuple[int, ...]:
    if not sampling.groups:
        return (sampling.total_trials,)

    counts = [0 for _ in sampling.groups]
    fixed_total = 0
    flexible_indices: list[int] = []

    for index, group in enumerate(sampling.groups):
        if group.count is None:
            flexible_indices.append(index)
            continue
        counts[index] = group.count
        fixed_total += group.count

    if fixed_total > sampling.total_trials:
        raise ValueError("fixed trial counts exceed total_trials")

    remaining = sampling.total_trials - fixed_total
    if not flexible_indices:
        if remaining:
            raise ValueError("trial groups leave unassigned trials")
        return tuple(counts)

    minimum_required = sum(sampling.groups[index].min_count for index in flexible_indices)
    if minimum_required > remaining:
        raise ValueError("trial group minimums exceed remaining trials")

    for index in flexible_indices:
        counts[index] = sampling.groups[index].min_count

    extra_total = remaining - minimum_required
    capacities: list[int] = []
    weights: list[float] = []
    for index in flexible_indices:
        group = sampling.groups[index]
        max_count = group.max_count if group.max_count is not None else remaining
        capacities.append(max_count - group.min_count)
        weights.append(group.ratio if group.ratio is not None else 1.0)

    extras = _allocate_weighted(extra_total, weights, capacities)
    for index, extra in zip(flexible_indices, extras, strict=True):
        counts[index] += extra

    if sum(counts) != sampling.total_trials:
        raise ValueError("resolved trial counts do not match total_trials")
    return tuple(counts)


def resolve_trial_plan(
    sampling: SamplingSpec, default_extraction: ExtractionSpec
) -> tuple[TrialPlanItem, ...]:
    if not sampling.groups:
        return tuple(
            TrialPlanItem(
                index=index,
                group_index=0,
                group_trial_index=index,
                group_name=default_extraction.name,
                extraction=default_extraction,
            )
            for index in range(sampling.total_trials)
        )

    counts = resolve_group_counts(sampling)
    if sampling.interleave:
        return _interleaved_plan(sampling, counts)
    return _grouped_plan(sampling, counts)


def _grouped_plan(
    sampling: SamplingSpec, counts: tuple[int, ...]
) -> tuple[TrialPlanItem, ...]:
    items: list[TrialPlanItem] = []
    for group_index, (group, count) in enumerate(zip(sampling.groups, counts, strict=True)):
        for group_trial_index in range(count):
            items.append(
                TrialPlanItem(
                    index=len(items),
                    group_index=group_index,
                    group_trial_index=group_trial_index,
                    group_name=group.name,
                    extraction=group.extraction,
                )
            )
    return tuple(items)


def _interleaved_plan(
    sampling: SamplingSpec, counts: tuple[int, ...]
) -> tuple[TrialPlanItem, ...]:
    items: list[TrialPlanItem] = []
    seen = [0 for _ in sampling.groups]
    while len(items) < sampling.total_trials:
        progressed = False
        for group_index, group in enumerate(sampling.groups):
            if seen[group_index] >= counts[group_index]:
                continue
            items.append(
                TrialPlanItem(
                    index=len(items),
                    group_index=group_index,
                    group_trial_index=seen[group_index],
                    group_name=group.name,
                    extraction=group.extraction,
                )
            )
            seen[group_index] += 1
            progressed = True
        if not progressed:
            raise ValueError("could not build trial plan from resolved counts")
    return tuple(items)


def _allocate_weighted(
    total: int, weights: list[float], capacities: list[int]
) -> list[int]:
    if total < 0:
        raise ValueError("allocation total must be non-negative")
    if len(weights) != len(capacities):
        raise ValueError("weights and capacities must have the same length")
    if sum(capacities) < total:
        raise ValueError("trial group maximums cannot fit total_trials")
    if total == 0:
        return [0 for _ in weights]

    allocations = [0 for _ in weights]
    remaining = total
    while remaining:
        active = [
            index
            for index, capacity in enumerate(capacities)
            if allocations[index] < capacity
        ]
        if not active:
            raise ValueError("no trial group capacity remains")

        total_weight = sum(weights[index] for index in active)
        if total_weight <= 0:
            total_weight = float(len(active))
            effective_weights = {index: 1.0 for index in active}
        else:
            effective_weights = {index: weights[index] for index in active}

        shares: list[tuple[int, float, int]] = []
        floor_total = 0
        for index in active:
            share = remaining * effective_weights[index] / total_weight
            available = capacities[index] - allocations[index]
            add = min(floor(share), available)
            shares.append((index, share, add))
            floor_total += add

        if floor_total:
            for index, _, add in shares:
                allocations[index] += add
            remaining -= floor_total
            continue

        shares.sort(
            key=lambda item: (-(item[1] - floor(item[1])), -weights[item[0]], item[0])
        )
        for index, _, _ in shares:
            if remaining == 0:
                break
            if allocations[index] >= capacities[index]:
                continue
            allocations[index] += 1
            remaining -= 1

    return allocations
