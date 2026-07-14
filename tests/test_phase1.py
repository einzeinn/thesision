from fastapi.testclient import TestClient
import pytest

from src.backend.app.main import app
from src.backend.orchestrator.reasoning_orchestrator import ReasoningOrchestrator


class FakeReasoningModel:
    def generate_json(self, instruction, payload):
        if instruction.startswith("Identify evidence"):
            return {"evidence": [{"claim": "FastAPI is suitable for I/O workloads.", "source_title": "FastAPI docs", "url": "https://fastapi.tiangolo.com/", "relevance": "high", "quality": "high"}]}
        if instruction.startswith("Generate engineering hypotheses"):
            return {"hypotheses": [{"claim": "The migration depends on workload.", "assumptions": [], "unknowns": []}]}
        if instruction.startswith("Analyze the engineering"):
            return {"perspectives": [{"name": "maintainability", "analysis": "Retain team familiarity.", "tradeoffs": ["runtime performance"]}, {"name": "performance", "analysis": "Measure bottlenecks.", "tradeoffs": ["implementation cost"]}, {"name": "scalability", "analysis": "Scale current service first.", "tradeoffs": ["operational complexity"]}]}
        if instruction.startswith("Judge"):
            return {"validated_claims": ["Measure first"], "conflicts": [], "unresolved_conflicts": [], "synthesis": "Evidence supports a measured decision."}
        return {"conclusion": "Measure before migrating.", "rationale": "Current evidence is sufficient.", "caveats": [], "next_steps": ["Profile the workload." ]}


client = TestClient(app)


def test_create_session_and_fetch_it():
    response = client.post(
        "/api/sessions",
        json={"question": "Should I migrate from FastAPI to Go?", "context": "backend migration"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "created"
    assert payload["session_id"]

    session_response = client.get(f"/api/sessions/{payload['session_id']}")
    assert session_response.status_code == 200
    session_payload = session_response.json()
    assert session_payload["question"] == "Should I migrate from FastAPI to Go?"
    assert session_payload["state"]["current_stage"] == "question"


def test_run_pipeline_advances_stage_and_persists_state():
    app.state.orchestrator = ReasoningOrchestrator(FakeReasoningModel())
    response = client.post(
        "/api/sessions",
        json={"question": "Should I migrate from FastAPI to Go?", "context": "backend migration"},
    )

    session_id = response.json()["session_id"]
    run_response = client.post(f"/api/sessions/{session_id}/run")

    assert run_response.status_code == 200
    payload = run_response.json()
    state = payload["session"]["state"]
    assert payload["status"] == "completed"
    assert state["status"] == "completed"
    assert state["current_stage"] == "conclusion"
    assert state["stages"]["hypothesis"]["status"] == "completed"
    assert state["stages"]["conclusion"]["status"] == "completed"
    assert state["confidence"]["score"] >= 90
    assert state["conclusion"]["conclusion"] == "Measure before migrating."
    assert {node["type"] for node in state["nodes"]} >= {"hypothesis", "evidence", "perspective", "conflict", "judge", "conclusion"}
    assert all("round" in node for node in state["nodes"])


def test_run_fails_explicitly_without_an_openai_key():
    from src.backend.services.openai_client import ConfiguredReasoningClient

    app.state.orchestrator = ReasoningOrchestrator(ConfiguredReasoningClient(api_key="", provider="openai"))
    response = client.post("/api/sessions", json={"question": "Should I optimize this service?"})
    run_response = client.post(f"/api/sessions/{response.json()['session_id']}/run")

    assert run_response.status_code == 503
    assert "OPENAI_API_KEY" in run_response.json()["detail"]


def test_aimlapi_uses_its_openai_compatible_chat_endpoint(monkeypatch):
    from src.backend.services.openai_client import ConfiguredReasoningClient

    calls = []

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": '{"hypotheses": []}'}}]}

    def fake_post(*args, **kwargs):
        calls.append((args, kwargs))
        return Response()

    monkeypatch.setattr("src.backend.services.openai_client.httpx.post", fake_post)
    result = ConfiguredReasoningClient(api_key="test-key", model="gpt-4o", provider="aimlapi").generate_json("Return JSON", {"question": "Test"})

    assert result == {"hypotheses": []}
    assert calls[0][0][0] == "https://api.aimlapi.com/v1/chat/completions"
    assert calls[0][1]["headers"]["Authorization"] == "Bearer test-key"
    assert calls[0][1]["json"]["model"] == "gpt-4o"


def test_aimlapi_non_json_response_is_an_explicit_provider_error(monkeypatch):
    from src.backend.services.openai_client import ConfiguredReasoningClient, ReasoningProviderError

    class Response:
        text = "Internal Server Error"

        def raise_for_status(self):
            return None

        def json(self):
            raise ValueError("not JSON")

    monkeypatch.setattr("src.backend.services.openai_client.httpx.post", lambda *args, **kwargs: Response())

    with pytest.raises(ReasoningProviderError, match="AI/ML API returned a non-JSON response"):
        ConfiguredReasoningClient(api_key="test-key", provider="aimlapi").generate_json("Return JSON", {})


def test_reasoning_workspace_serves_an_interactive_graph_shell():
    response = client.get("/")

    assert response.status_code == 200
    assert 'id="graph"' in response.text
    assert "d3@7" in response.text
    assert "animejs" in response.text
    assert 'id="replay-button"' in response.text
    assert 'id="progress-list"' in response.text


def test_start_endpoint_accepts_a_persisted_session():
    app.state.orchestrator = ReasoningOrchestrator(FakeReasoningModel())
    created = client.post("/api/sessions", json={"question": "Should we keep the current stack?"}).json()

    response = client.post(f"/api/sessions/{created['session_id']}/start")

    assert response.status_code == 202
    assert response.json()["status"] == "started"


def test_exports_match_the_persisted_reasoning_session():
    app.state.orchestrator = ReasoningOrchestrator(FakeReasoningModel())
    created = client.post("/api/sessions", json={"question": "Should we migrate?"}).json()
    session_id = created["session_id"]
    client.post(f"/api/sessions/{session_id}/run")

    json_export = client.get(f"/api/sessions/{session_id}/exports/json")
    markdown_export = client.get(f"/api/sessions/{session_id}/exports/markdown")

    assert json_export.status_code == 200
    assert json_export.json() == client.get(f"/api/sessions/{session_id}").json()
    assert markdown_export.status_code == 200
    assert "# Thesision Reasoning Report" in markdown_export.text
    assert "Should we migrate?" in markdown_export.text


def test_exports_reject_missing_or_incomplete_sessions():
    missing = client.get("/api/sessions/missing/exports/json")
    created = client.post("/api/sessions", json={"question": "Should we defer this migration?"}).json()
    incomplete = client.get(f"/api/sessions/{created['session_id']}/exports/markdown")

    assert missing.status_code == 404
    assert incomplete.status_code == 409


def test_session_input_has_documented_size_limits():
    response = client.post("/api/sessions", json={"question": "x" * 4_001})

    assert response.status_code == 422
