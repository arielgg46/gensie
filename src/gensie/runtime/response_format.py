from __future__ import annotations

from typing import Any

from gensie.schemas.reasoning import transform_schema_for_reasoning


def build_json_schema_response_format(
    schema: dict[str, Any], reasoning: Any, *, name: str = "extraction"
) -> dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "schema": transform_schema_for_reasoning(schema, reasoning),
            "strict": True,
        },
    }
