from fastapi.testclient import TestClient

from src.backend.app.main import app


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
    assert "hypothesis" in state["stages"]
    assert "conclusion" in state["stages"]
