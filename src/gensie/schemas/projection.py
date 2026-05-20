from __future__ import annotations

import copy
from typing import Sequence

from gensie.schemas.inspect import JsonDict


def build_reduced_schema(schema: JsonDict, field_names: Sequence[str]) -> JsonDict:
    field_order = tuple(dict.fromkeys(str(name) for name in field_names))
    field_set = set(field_order)
    reduced = copy.deepcopy(schema)

    properties = reduced.get("properties")
    if isinstance(properties, dict):
        reduced["properties"] = {
            name: value for name, value in properties.items() if name in field_set
        }
    else:
        reduced["properties"] = {}

    required = reduced.get("required")
    if isinstance(required, list):
        reduced["required"] = [
            name for name in required if isinstance(name, str) and name in field_set
        ]
    else:
        reduced["required"] = [
            name for name in field_order if name in reduced["properties"]
        ]
    return reduced
