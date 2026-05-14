from __future__ import annotations

from typing import Any, Protocol, Sequence

from gensie.aggregation.clustering import IdentityFieldDecision
from gensie.aggregation.schema_utils import (
    JsonDict,
    deref_item_schema,
    is_required,
    schema_type,
    unwrap_nullable_schema,
)
from gensie.schemas.inspect import deref


class DiagnosticAggregator(Protocol):
    config: Any
    array_selector: Any

    def select_identity_field(
        self, item_schema: JsonDict, root_schema: JsonDict
    ) -> IdentityFieldDecision:
        pass


def build_self_consistency_diagnostics(
    aggregator: DiagnosticAggregator,
    outputs: Sequence[JsonDict],
    schema: JsonDict,
    final_output: JsonDict,
) -> JsonDict:
    root_schema = schema
    resolved_schema, _ = unwrap_nullable_schema(schema, root_schema)
    resolved_schema = deref(resolved_schema, root_schema)
    return {
        "strategy": "schema_aware_self_consistency",
        "sample_count": len(outputs),
        "string_similarity": getattr(
            getattr(aggregator, "string_similarity", None), "name", "unknown"
        ),
        "array_selector": aggregator.array_selector.__class__.__name__,
        "identity_selector": getattr(
            getattr(aggregator, "identity_selector", None), "name", "unknown"
        ),
        "config": aggregator.config.__dict__,
        "fields": _diagnose_object(
            aggregator,
            list(outputs),
            resolved_schema,
            root_schema,
            final_output,
            root=True,
        )
        if resolved_schema.get("type") == "object"
        else {},
    }


def _diagnose_object(
    aggregator: DiagnosticAggregator,
    objects: Sequence[JsonDict],
    schema: JsonDict,
    root_schema: JsonDict,
    final_object: Any,
    *,
    root: bool = False,
) -> JsonDict:
    if not isinstance(final_object, dict):
        final_object = {}
    objects = [obj for obj in objects if isinstance(obj, dict)]
    props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    out: JsonDict = {}
    for name, child_schema in props.items():
        if not isinstance(child_schema, dict):
            continue
        present_values = [obj[name] for obj in objects if name in obj]
        out[name] = _diagnose_value(
            aggregator,
            present_values,
            child_schema,
            root_schema,
            final_object.get(name),
            required=is_required(schema, name) or root,
        )
    return out


def _diagnose_value(
    aggregator: DiagnosticAggregator,
    values: Sequence[Any],
    schema: JsonDict,
    root_schema: JsonDict,
    final_value: Any,
    *,
    required: bool,
) -> JsonDict:
    schema, nullable = unwrap_nullable_schema(schema, root_schema)
    schema = deref(schema, root_schema)
    current_type = schema_type(schema)
    non_null_values = [value for value in values if value is not None]
    base: JsonDict = {
        "schema_type": current_type or "any",
        "required": required,
        "nullable": nullable,
        "sample_count": len(values),
        "null_count": len(values) - len(non_null_values),
        "final_value": final_value,
    }

    if current_type == "array":
        arrays = [value for value in non_null_values if isinstance(value, list)]
        item_schema = deref_item_schema(schema, root_schema)
        identity_decision = aggregator.select_identity_field(item_schema, root_schema)
        base.update(
            {
                "strategy": f"itemwise_array_consensus_{aggregator.config.array_selector_mode}",
                "array_selector": aggregator.array_selector.__class__.__name__,
                "observed_lengths": [len(array) for array in arrays],
                "final_length": len(final_value if isinstance(final_value, list) else []),
                "cluster_similarity": (
                    "identity_field"
                    if identity_decision.field_name
                    else "schema_value"
                ),
                "identity_field_decision": _identity_decision_diagnostic(
                    identity_decision
                ),
            }
        )
        return base

    if current_type == "object":
        base["strategy"] = "recursive_object_consensus"
        base["fields"] = _diagnose_object(
            aggregator,
            [value for value in non_null_values if isinstance(value, dict)],
            schema,
            root_schema,
            final_value,
        )
        return base

    base["strategy"] = "scalar_cluster_medoid"
    return base


def _identity_decision_diagnostic(decision: IdentityFieldDecision) -> JsonDict:
    return {
        "field_name": decision.field_name,
        "score": round(decision.score, 6),
        "margin": round(decision.margin, 6),
        "confidence": decision.confidence,
        "candidates": [
            {
                "name": candidate.name,
                "score": round(candidate.score, 6),
                "reasons": list(candidate.reasons),
            }
            for candidate in decision.candidates
        ],
    }
