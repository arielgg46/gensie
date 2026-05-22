import json
import shutil
from pathlib import Path

from gensie.phases import (
    VERBATIM_ENTITY_SCHEMA_NAME,
    VerbatimEntitiesPhase,
    build_verbatim_entity_prompt,
    build_verbatim_entity_response_format,
    build_verbatim_entity_schema,
    flatten_verbatim_entities,
    normalize_verbatim_entities,
    parse_verbatim_entity_response,
)
from gensie.pipeline import PipelineContext
from gensie.runtime import ChatResponse
from gensie.usage import UsageTracker
from gensie.task import Task


class FakeChatClient:
    def __init__(self, content: str):
        self.content = content
        self.requests = []

    def complete(self, request):
        self.requests.append(request)
        return ChatResponse(
            content=self.content,
            usage={"prompt_tokens": 5, "completion_tokens": 3},
        )


def _task() -> Task:
    return Task(
        id="entity-sample",
        input_text="Madrid, 14 de abril de 2026. Lucía Ferrer presentó Atlas-IE.",
        instruction="Extract something.",
        target_schema={
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"],
        },
    )


def test_verbatim_entity_schema_and_prompt_match_reference_contract():
    schema = build_verbatim_entity_schema()
    prompt = build_verbatim_entity_prompt(_task().input_text)

    assert schema["required"] == [
        "personas",
        "organizaciones",
        "fechas",
        "lugares",
        "otros",
    ]
    assert build_verbatim_entity_response_format()["json_schema"]["name"] == (
        VERBATIM_ENTITY_SCHEMA_NAME
    )
    assert "Extrae entidades verbatim" in prompt
    assert "CATEGORÍAS:" in prompt
    assert "títulos" in prompt
    assert "Lucía Ferrer" in prompt


def test_parse_normalize_and_flatten_verbatim_entities():
    parsed = parse_verbatim_entity_response(
        '{"personas":[" Lucía Ferrer ","Lucía Ferrer",42],'
        '"organizaciones":["Instituto Ibérico"],'
        '"fechas":["14 de abril de 2026"],'
        '"lugares":["Madrid"],'
        '"otros":["Atlas-IE","Atlas-IE"]}'
    )

    assert parsed == {
        "personas": ["Lucía Ferrer"],
        "organizaciones": ["Instituto Ibérico"],
        "fechas": ["14 de abril de 2026"],
        "lugares": ["Madrid"],
        "otros": ["Atlas-IE"],
    }
    assert flatten_verbatim_entities(parsed) == [
        "Lucía Ferrer",
        "Instituto Ibérico",
        "14 de abril de 2026",
        "Madrid",
        "Atlas-IE",
    ]
    assert normalize_verbatim_entities({}) == {
        "personas": [],
        "organizaciones": [],
        "fechas": [],
        "lugares": [],
        "otros": [],
    }


def test_verbatim_entities_phase_calls_model_with_strict_schema_and_tracks_usage():
    fake = FakeChatClient(
        '{"personas":["Lucía Ferrer"],'
        '"organizaciones":[],'
        '"fechas":["14 de abril de 2026"],'
        '"lugares":["Madrid"],'
        '"otros":["Atlas-IE"]}'
    )
    context = PipelineContext(task=_task(), model="demo", usage=UsageTracker())
    phase = VerbatimEntitiesPhase(chat_client=fake)

    result = phase.run(context)

    assert result.data["verbatim_entity_list"] == [
        "Lucía Ferrer",
        "14 de abril de 2026",
        "Madrid",
        "Atlas-IE",
    ]
    request = fake.requests[0]
    assert request.temperature == 0.0
    assert request.response_format == build_verbatim_entity_response_format()
    assert "Extrae entidades verbatim" in request.messages[1].content
    assert context.usage.snapshot() == {
        "input_tokens": 5,
        "output_tokens": 3,
        "total_tokens": 8,
        "calls": 1,
    }


def test_verbatim_entities_phase_traces_its_own_step():
    fake = FakeChatClient(
        '{"personas":["Lucía Ferrer"],'
        '"organizaciones":[],'
        '"fechas":["14 de abril de 2026"],'
        '"lugares":["Madrid"],'
        '"otros":["Atlas-IE"]}'
    )
    trace_dir = Path(".test-verbatim-tracing")
    shutil.rmtree(trace_dir, ignore_errors=True)
    task = _task()
    task.metadata["_trace_dir"] = str(trace_dir / "entity-sample")
    context = PipelineContext(task=task, model="demo", usage=UsageTracker())

    try:
        VerbatimEntitiesPhase(chat_client=fake).run(context)

        step_dir = trace_dir / "entity-sample" / "steps" / "01-extract_verbatim_entities"
        assert (step_dir / "system_prompt.txt").exists()
        assert (step_dir / "user_prompt.txt").exists()
        assert not (step_dir / "prompt.txt").exists()
        request = json.loads((step_dir / "request.json").read_text(encoding="utf-8"))
        response = json.loads((step_dir / "response.json").read_text(encoding="utf-8"))
        assert request["temperature"] == 0.0
        assert response["verbatim_entity_list"] == [
            "Lucía Ferrer",
            "14 de abril de 2026",
            "Madrid",
            "Atlas-IE",
        ]
    finally:
        shutil.rmtree(trace_dir, ignore_errors=True)


def test_verbatim_entities_phase_falls_back_to_empty_entities_on_failure():
    class FailingClient:
        def complete(self, request):
            raise RuntimeError("phase failed")

    context = PipelineContext(task=_task(), model="demo", usage=UsageTracker())
    result = VerbatimEntitiesPhase(chat_client=FailingClient()).run(context)

    assert result.data["verbatim_entity_list"] == []
    assert result.metadata["error"] == "phase failed"
    assert context.usage.snapshot()["calls"] == 0
