"""The /run endpoint reports the agent's token tally in X-GenSIE-Token-Usage."""

import json
import shutil
from pathlib import Path

import gensie.server as server
from fastapi.testclient import TestClient
from gensie.agent import GenSIEAgent, Participant, ParticipantInfo, PipelineInfo
from gensie.usage import UsageTracker


class _FakeAgent(GenSIEAgent):
    def __init__(self):
        self.usage = UsageTracker()

    def run(self, task, model):
        self.usage.reset()
        self.usage.add({"prompt_tokens": 1234, "completion_tokens": 567})
        return {"answer": "ok"}


class _FakeParticipant(Participant):
    def __init__(self):
        self._agent = _FakeAgent()

    def get_info(self):
        return ParticipantInfo(
            team_name="Fake",
            institution="Fake",
            pipelines=[PipelineInfo(name="baseline", description="x")],
        )

    def get_agent(self, pipeline_name):
        return self._agent


_TASK = {
    "id": "t1",
    "input_text": "x",
    "instruction": "y",
    "target_schema": {"type": "object", "properties": {"answer": {"type": "string"}}},
    "output": {"answer": "ok"},
}


def test_run_sets_token_usage_header(monkeypatch):
    monkeypatch.setattr(server, "participant", _FakeParticipant())
    client = TestClient(server.app)
    resp = client.post("/run", params={"model": "demo"}, json=_TASK)
    assert resp.status_code == 200
    assert resp.json() == {"answer": "ok"}

    usage = json.loads(resp.headers["x-gensie-token-usage"])
    assert usage == {
        "input_tokens": 1234,
        "output_tokens": 567,
        "total_tokens": 1801,
        "calls": 1,
    }


def test_run_writes_pred_and_gold_trace_artifacts(monkeypatch):
    trace_dir = Path("test-artifacts/unit-server-tracing")
    shutil.rmtree(trace_dir, ignore_errors=True)
    try:
        monkeypatch.setattr(server, "participant", _FakeParticipant())
        client = TestClient(server.app)
        task = dict(_TASK)
        task["metadata"] = {"_trace_dir": str(trace_dir / "t1")}

        resp = client.post("/run", params={"model": "demo"}, json=task)

        assert resp.status_code == 200
        pred = json.loads((trace_dir / "t1" / "pred.json").read_text(encoding="utf-8"))
        gold = json.loads((trace_dir / "t1" / "gold.json").read_text(encoding="utf-8"))
        assert pred == {"answer": "ok"}
        assert gold == {"answer": "ok"}
    finally:
        shutil.rmtree(trace_dir, ignore_errors=True)
