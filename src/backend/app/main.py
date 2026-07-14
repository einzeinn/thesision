from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.backend.orchestrator.reasoning_orchestrator import ReasoningOrchestrator
from src.backend.services.openai_client import ConfiguredReasoningClient
from src.backend.services.output_generator import build_json_export, build_markdown_report
from src.backend.state.session_store import create_session, get_session

ROOT_DIR = Path(__file__).resolve().parents[3]
FRONTEND_DIR = ROOT_DIR / "src" / "frontend" / "app"
INDEX_HTML = FRONTEND_DIR / "index.html"

app = FastAPI(title="Thesision", version="0.1.0")
app.state.orchestrator = ReasoningOrchestrator(ConfiguredReasoningClient())

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


class SessionCreateRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4_000)
    context: Optional[str] = Field(default=None, max_length=8_000)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/")
def root() -> FileResponse:
    return FileResponse(INDEX_HTML)


@app.post("/api/sessions")
def create_session_endpoint(payload: SessionCreateRequest) -> dict:
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    session = create_session(payload.question, payload.context)
    return {"status": "created", "session_id": session["session_id"], "session": session}


@app.get("/api/sessions/{session_id}")
def get_session_endpoint(session_id: str) -> dict:
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.post("/api/sessions/{session_id}/run")
def run_session(session_id: str) -> dict:
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    completed_session = app.state.orchestrator.run(session)
    if completed_session["state"]["status"] == "failed":
        raise HTTPException(status_code=503, detail=completed_session["state"]["errors"][-1])
    return {"status": "completed", "session": completed_session}


def _run_session_in_background(session_id: str) -> None:
    session = get_session(session_id)
    if session is not None:
        app.state.orchestrator.run(session)


@app.post("/api/sessions/{session_id}/start", status_code=202)
def start_session(session_id: str, background_tasks: BackgroundTasks) -> dict:
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["state"].get("status") == "running":
        raise HTTPException(status_code=409, detail="Reasoning is already running")
    background_tasks.add_task(_run_session_in_background, session_id)
    return {"status": "started", "session_id": session_id}


def _require_session(session_id: str) -> dict:
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def _require_completed_session(session_id: str) -> dict:
    session = _require_session(session_id)
    if session["state"].get("status") != "completed":
        raise HTTPException(status_code=409, detail="Reasoning must complete before it can be exported")
    return session


@app.get("/api/sessions/{session_id}/exports/markdown")
def export_markdown(session_id: str) -> PlainTextResponse:
    report = build_markdown_report(_require_completed_session(session_id))
    return PlainTextResponse(
        report,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="thesision-{session_id}.md"'},
    )


@app.get("/api/sessions/{session_id}/exports/json")
def export_json(session_id: str) -> PlainTextResponse:
    payload = build_json_export(_require_completed_session(session_id))
    return PlainTextResponse(
        payload,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="thesision-{session_id}.json"'},
    )
