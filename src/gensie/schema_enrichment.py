import json
from typing import Any

from gensie.prompting import clean_schema_for_prompt


def build_enriched_prompt(
    instruction: str, input_text: str, target_schema: dict[str, Any]
) -> str:
    """Compatibility prompt builder for the enriched-schema pipeline."""
    clean_schema, root_description = clean_schema_for_prompt(target_schema)
    schema_json = json.dumps(clean_schema, ensure_ascii=False, indent=2)
    return (
        f"{instruction}\n\n"
        f"SCHEMA DESCRIPTION:\n{root_description or ''}\n\n"
        f"READABLE SCHEMA:\n{schema_json}\n\n"
        f"TEXT:\n{input_text}"
    )
