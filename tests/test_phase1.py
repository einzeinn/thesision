from fastapi.testclient import TestClient

from src.backend.app.main import app
from src.backend.orchestrator.reasoning_orchestrator import ReasoningOrchestrator


class FakeReasoningModel:
    def generate_json(self, instruction, payload):
        if instruction.startswith("Identify evidence"):
            return {"evidence": [{"claim": "FastAPI is suitable for I/O workloads.", "source_title": "FastAPI docs", "url": "https://fastapi.tiangolo.com/", "relevance": "high", "quality": 100}]}
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


def test_run_fails_explicitly_without_an_openai_key():
    from src.backend.services.openai_client import OpenAIResponsesClient

    app.state.orchestrator = ReasoningOrchestrator(OpenAIResponsesClient(api_key=""))
    response = client.post("/api/sessions", json={"question": "Should I optimize this service?"})
    run_response = client.post(f"/api/sessions/{response.json()['session_id']}/run")

    assert run_response.status_code == 503
    assert "OPENAI_API_KEY" in run_response.json()["detail"]


def test_reasoning_workspace_serves_an_interactive_graph_shell():
    response = client.get("/")

    assert response.status_code == 200
    assert 'id="graph"' in response.text
    assert "Node inspection" in response.text
