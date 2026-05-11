from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping

from openai import OpenAI


JsonDict = dict[str, Any]
EntityExtractor = Callable[[str], Mapping[str, Any]]

VERBATIM_ENTITY_FIELDS: tuple[str, ...] = (
    "personas",
    "organizaciones",
    "fechas",
    "lugares",
    "otros",
)

VERBATIM_ENTITY_SYSTEM_PROMPT = (
    "Eres un extractor de entidades verbatim para textos en español. "
    "Usa solo evidencia literal del texto fuente."
)

VERBATIM_ENTITY_SCHEMA_NAME = "verbatim_entity_extraction"

_VERBATIM_ENTITY_SCHEMA: JsonDict = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "personas": {
            "type": "array",
            "description": (
                "Person names, fictional characters, or named human groups copied "
                "verbatim from the source text."
            ),
            "items": {"type": "string"},
        },
        "organizaciones": {
            "type": "array",
            "description": (
                "Organizations, institutions, companies, agencies, parties, teams, "
                "or named collectives copied verbatim from the source text."
            ),
            "items": {"type": "string"},
        },
        "fechas": {
            "type": "array",
            "description": (
                "Dates, years, and periods copied verbatim "
                "from the source text; do not normalize them."
            ),
            "items": {"type": "string"},
        },
        "lugares": {
            "type": "array",
            "description": (
                "Places, cities, countries, regions, facilities, geographic names, "
                "or location mentions copied verbatim from the source text."
            ),
            "items": {"type": "string"},
        },
        "otros": {
            "type": "array",
            "description": (
                "Other named or salient entities copied verbatim from the source "
                "text that are not persons, organizations, dates, or places."
            ),
            "items": {"type": "string"},
        },
    },
    "required": list(VERBATIM_ENTITY_FIELDS),
}


def build_verbatim_entity_schema() -> JsonDict:
    """Return the strict JSON schema used for the SLM entity extraction call."""

    return copy.deepcopy(_VERBATIM_ENTITY_SCHEMA)


def build_verbatim_entity_prompt(input_text: str) -> str:
    """Build the user prompt for extracting verbatim entity spans."""

    return (
        "TAREA:\n"
        "Extrae entidades verbatim del TEXTO FUENTE y clasifícalas.\n\n"
        "REGLAS:\n"
        "- Copia cada entidad exactamente como aparece en el texto fuente.\n"
        "- No normalices fechas, nombres, siglas, títulos ni lugares.\n"
        "- No traduzcas, no reformules y no completes con conocimiento externo.\n"
        "- No inventes entidades implícitas.\n"
        "- Si una categoría no tiene evidencia, devuelve una lista vacía [].\n"
        "- No repitas el mismo string dentro de una categoría.\n"
        "- Usa 'otros' solo para entidades que no sean personas, organizaciones, "
        "fechas o lugares.\n\n"
        "CATEGORIAS:\n"
        "- personas: nombres de personas o personajes.\n"
        "- organizaciones: instituciones, empresas, organismos, partidos, equipos "
        "o colectivos nombrados.\n"
        "- fechas: fechas o años concretos (NO expresiones inconcretas como 'el año pasado', SÍ '2001').\n"
        "- lugares: ciudades, países, regiones, instalaciones o ubicaciones.\n"
        "- otros: obras, productos, medicamentos, eventos, leyes, sistemas, "
        "títulos u otras entidades nombradas.\n\n"
        "TEXTO FUENTE:\n"
        f"{input_text}"
    )


def build_verbatim_entity_response_format() -> JsonDict:
    """Return the OpenAI-compatible strict structured-output response format."""

    return {
        "type": "json_schema",
        "json_schema": {
            "name": VERBATIM_ENTITY_SCHEMA_NAME,
            "schema": build_verbatim_entity_schema(),
            "strict": True,
        },
    }


def parse_verbatim_entity_response(content: str | Mapping[str, Any]) -> JsonDict:
    """Parse and normalize a model response into the fixed entity schema shape."""

    raw = json.loads(content) if isinstance(content, str) else dict(content)
    return normalize_verbatim_entities(raw)


def normalize_verbatim_entities(value: Mapping[str, Any]) -> JsonDict:
    """Keep only string lists from known fields and dedupe while preserving order."""

    normalized: JsonDict = {}
    for field_name in VERBATIM_ENTITY_FIELDS:
        items = value.get(field_name, [])
        if not isinstance(items, list):
            items = []

        seen: set[str] = set()
        cleaned: list[str] = []
        for item in items:
            if not isinstance(item, str):
                continue
            text = item.strip()
            if not text or text in seen:
                continue
            seen.add(text)
            cleaned.append(text)
        normalized[field_name] = cleaned
    return normalized


def flatten_verbatim_entities(value: Mapping[str, Any]) -> list[str]:
    """Return all verbatim entities as one deduped list without category labels."""

    normalized = normalize_verbatim_entities(value)
    seen: set[str] = set()
    flattened: list[str] = []
    for field_name in VERBATIM_ENTITY_FIELDS:
        for item in normalized[field_name]:
            if item in seen:
                continue
            seen.add(item)
            flattened.append(item)
    return flattened


def extract_verbatim_entities(
    input_text: str,
    model: str,
    *,
    client: OpenAI | None = None,
    temperature: float = 0.0,
) -> JsonDict:
    """Call an OpenAI-compatible SLM once and return verbatim entity lists."""

    client = client or _build_default_client()
    messages = [
        {"role": "system", "content": VERBATIM_ENTITY_SYSTEM_PROMPT},
        {"role": "user", "content": build_verbatim_entity_prompt(input_text)},
    ]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format=build_verbatim_entity_response_format(),
        temperature=temperature,
    )
    content = response.choices[0].message.content
    return parse_verbatim_entity_response(content)


def score_verbatim_entities(
    predicted: Mapping[str, Any],
    expected: Mapping[str, Any],
) -> JsonDict:
    """Score exact verbatim entity extraction by category."""

    predicted = normalize_verbatim_entities(predicted)
    expected = normalize_verbatim_entities(expected)
    fields: JsonDict = {}
    total_tp = total_fp = total_fn = 0
    active_field_f1s: list[float] = []

    for field_name in VERBATIM_ENTITY_FIELDS:
        pred_set = set(predicted[field_name])
        gold_set = set(expected[field_name])
        true_positives = pred_set & gold_set
        false_positives = pred_set - gold_set
        false_negatives = gold_set - pred_set
        metrics = _prf_counts(
            len(true_positives),
            len(false_positives),
            len(false_negatives),
        )

        total_tp += metrics["true_positives"]
        total_fp += metrics["false_positives"]
        total_fn += metrics["false_negatives"]
        if pred_set or gold_set:
            active_field_f1s.append(metrics["f1"])

        fields[field_name] = {
            **metrics,
            "exact_match": pred_set == gold_set,
            "missing": sorted(false_negatives),
            "extra": sorted(false_positives),
        }

    micro = _prf_counts(total_tp, total_fp, total_fn)
    return {
        "exact_match": all(fields[field_name]["exact_match"] for field_name in fields),
        "micro": micro,
        "macro": {
            "f1": (
                sum(active_field_f1s) / len(active_field_f1s)
                if active_field_f1s
                else 1.0
            ),
            "active_fields": len(active_field_f1s),
        },
        "fields": fields,
    }


def evaluate_verbatim_entity_tasks(
    data_dir: str | Path,
    model: str,
    *,
    client: OpenAI | None = None,
    extractor: EntityExtractor | None = None,
    temperature: float = 0.0,
    output_path: str | Path | None = None,
    artifacts_dir: str | Path | None = None,
) -> JsonDict:
    """
    Run the verbatim entity extractor over a folder of entity tasks and score it.

    The folder is expected to contain JSON files with:
    - input_text: source text
    - output: gold entity lists using VERBATIM_ENTITY_FIELDS
    """

    data_path = Path(data_dir)
    task_files = sorted(data_path.glob("*.json"))
    artifacts_path = Path(artifacts_dir) if artifacts_dir is not None else None
    task_results: list[JsonDict] = []
    field_totals: dict[str, dict[str, int]] = {
        field_name: {"tp": 0, "fp": 0, "fn": 0}
        for field_name in VERBATIM_ENTITY_FIELDS
    }
    total_tp = total_fp = total_fn = 0
    exact_matches = 0

    for task_file in task_files:
        task_data = json.loads(task_file.read_text(encoding="utf-8"))
        input_text = str(task_data.get("input_text") or "")
        prompt = build_verbatim_entity_prompt(input_text)
        expected = normalize_verbatim_entities(task_data.get("output") or {})
        error = None

        try:
            if extractor is None:
                predicted = extract_verbatim_entities(
                    input_text,
                    model,
                    client=client,
                    temperature=temperature,
                )
            else:
                predicted = normalize_verbatim_entities(extractor(input_text))
        except Exception as exc:
            error = str(exc) or repr(exc)
            predicted = normalize_verbatim_entities({})

        metrics = score_verbatim_entities(predicted, expected)
        if metrics["exact_match"]:
            exact_matches += 1

        for field_name in VERBATIM_ENTITY_FIELDS:
            field_metrics = metrics["fields"][field_name]
            tp = field_metrics["true_positives"]
            fp = field_metrics["false_positives"]
            fn = field_metrics["false_negatives"]
            field_totals[field_name]["tp"] += tp
            field_totals[field_name]["fp"] += fp
            field_totals[field_name]["fn"] += fn
            total_tp += tp
            total_fp += fp
            total_fn += fn

        if artifacts_path is not None:
            _write_verbatim_entity_task_artifacts(
                artifacts_path / task_file.stem,
                prompt=prompt,
                prediction=predicted,
                gold=expected,
                metrics=metrics,
                error=error,
            )

        task_results.append(
            {
                "id": task_file.stem,
                "path": str(task_file),
                "artifact_dir": (
                    str(artifacts_path / task_file.stem)
                    if artifacts_path is not None
                    else None
                ),
                "gold": expected,
                "prediction": predicted,
                "metrics": metrics,
                "error": error,
            }
        )

    field_metrics = {
        field_name: _prf_counts(
            counts["tp"],
            counts["fp"],
            counts["fn"],
        )
        for field_name, counts in field_totals.items()
    }
    active_field_f1s = [
        metrics["f1"]
        for field_name, metrics in field_metrics.items()
        if field_totals[field_name]["tp"]
        or field_totals[field_name]["fp"]
        or field_totals[field_name]["fn"]
    ]
    report: JsonDict = {
        "data_dir": str(data_path),
        "model": model,
        "task_count": len(task_results),
        "exact_match_rate": (
            exact_matches / len(task_results) if task_results else 1.0
        ),
        "micro": _prf_counts(total_tp, total_fp, total_fn),
        "macro": {
            "f1": (
                sum(active_field_f1s) / len(active_field_f1s)
                if active_field_f1s
                else 1.0
            ),
            "active_fields": len(active_field_f1s),
        },
        "fields": field_metrics,
        "tasks": task_results,
    }

    if output_path is not None:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return report


def _write_verbatim_entity_task_artifacts(
    task_dir: Path,
    *,
    prompt: str,
    prediction: Mapping[str, Any],
    gold: Mapping[str, Any],
    metrics: Mapping[str, Any],
    error: str | None,
) -> None:
    task_dir.mkdir(parents=True, exist_ok=True)
    prompt_text = (
        "SYSTEM:\n"
        f"{VERBATIM_ENTITY_SYSTEM_PROMPT}\n\n"
        "USER:\n"
        f"{prompt}\n"
    )
    task_dir.joinpath("prompt.txt").write_text(prompt_text, encoding="utf-8")
    task_dir.joinpath("output.json").write_text(
        json.dumps(normalize_verbatim_entities(prediction), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    task_dir.joinpath("gold.json").write_text(
        json.dumps(normalize_verbatim_entities(gold), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    task_dir.joinpath("metrics.json").write_text(
        json.dumps({"metrics": metrics, "error": error}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _build_default_client() -> OpenAI:
    timeout_s = float(os.getenv("OPENAI_TIMEOUT_S", "120"))
    return OpenAI(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY", "sk-dummy"),
        timeout=timeout_s,
    )


def _prf_counts(true_positives: int, false_positives: int, false_negatives: int) -> JsonDict:
    precision = _safe_div(true_positives, true_positives + false_positives)
    recall = _safe_div(true_positives, true_positives + false_negatives)
    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall,
        "f1": _f1(precision, recall),
    }


def _safe_div(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 1.0


def _f1(precision: float, recall: float) -> float:
    return (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
