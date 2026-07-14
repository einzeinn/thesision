from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.backend.state.session_store import create_session, get_session, update_session_run

ROOT_DIR = Path(__file__).resolve().parents[3]
FRONTEND_DIR = ROOT_DIR / "src" / "frontend" / "app"
INDEX_HTML = FRONTEND_DIR / "index.html"

app = FastAPI(title="Thesision", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


class SessionCreateRequest(BaseModel):
    question: str
    context: Optional[str] = None


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
    session = update_session_run(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "completed", "session": session}
