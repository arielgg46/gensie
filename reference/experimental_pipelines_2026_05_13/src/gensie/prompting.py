import copy
import json
from typing import Any

from gensie.task import Task


PROMPT_SCHEMA_DROP_KEYS = {"additionalProperties", "default", "required", "title"}


SIMPLE_CLEAN_SCHEMA_SYSTEM_PROMPT = (
    "You are an expert Spanish information extraction engine.\n"
    "Return the full JSON object required by the provided schema.\n"
    "Use only evidence from the source text.\n"
)


def clean_schema_for_prompt(schema: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    """Return a prompt-friendly schema copy and the original root description."""
    schema_copy = copy.deepcopy(schema)
    root_description = schema_copy.get("description")
    clean_schema = _clean_schema_node(schema_copy, is_root=True)
    return clean_schema, root_description


def _clean_schema_node(value: Any, *, is_root: bool = False) -> Any:
    if isinstance(value, dict):
        cleaned = {}
        for key, child in value.items():
            if key in PROMPT_SCHEMA_DROP_KEYS:
                continue
            if is_root and key == "description":
                continue
            cleaned[key] = _clean_schema_node(child)
        return cleaned

    if isinstance(value, list):
        return [_clean_schema_node(item) for item in value]

    return value


def build_simple_clean_schema_prompt(task: Task) -> str:
    clean_schema, root_description = clean_schema_for_prompt(task.target_schema)
    schema_json = json.dumps(clean_schema, ensure_ascii=False, indent=2)
    schema_description = root_description or "No root schema description provided."

    return (
        "TASK:\n"
        "Extract the requested structured information from the Spanish SOURCE TEXT.\n"
        "The instruction describes the goal, but the final JSON must cover the full schema.\n\n"
        "INSTRUCTION:\n"
        f"{task.instruction}\n"
        f"{schema_description}\n\n"
        # "RULES:\n"
        # "- Always extract the fullest verbatim span for the answers, preserve the exact wording from the source text.\n"
        # "- Do not repeat elements in arrays.\n"
        # "- Fill all the schema fields, using null ONLY when there is no grounded evidence for the answer in the source text.\n\n"
        # "- Ground every non-null value in the text. Do not fill known facts unless the text states them.\n"
        # "- Use null for missing scalar/object values when null is allowed by the schema.\n"
        # "- Use [] for arrays when no supported items are found.\n"
        # "- For date fields, follow the field description. If it requests a format and the text provides enough information, normalize; otherwise use the verbatim date if allowed by the description.\n"
        # "- Prefer concise, evidence-backed lists. Avoid adding plausible but unstated items.\n"
        # "- Preserve verbatim names, titles, percentages, doses, organizations and quoted labels when the field asks for names or exact values.\n"
        # "- Summaries and verdicts may be concise paraphrases, but must not add external facts.\n\n"
        "SCHEMA:\n"
        f"{schema_json}\n\n"
        "SOURCE TEXT:\n"
        f"{task.input_text}"
    )
