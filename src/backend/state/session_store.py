import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

ROOT_DIR = Path(__file__).resolve().parents[3]
DB_PATH = ROOT_DIR / "data" / "thesision.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

PIPELINE_STAGES = [
    "question",
    "hypothesis",
    "evidence",
    "perspectives",
    "judge",
    "confidence",
    "conclusion",
]


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            question TEXT NOT NULL,
            context TEXT,
            state_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.commit()
    return connection


def create_session(question: str, context: Optional[str] = None) -> Dict[str, Any]:
    session_id = str(uuid.uuid4())
    state = {
        "current_stage": "question",
        "status": "created",
        "iteration": 0,
        "nodes": [],
        "stages": ["question"],
        "metadata": {"context": context or ""},
        "pipeline": PIPELINE_STAGES,
        "summary": None,
    }
    created_at = datetime.now(timezone.utc).isoformat()

    connection = _connect()
    connection.execute(
        "INSERT INTO sessions (id, question, context, state_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, question, context, json.dumps(state), created_at),
    )
    connection.commit()
    connection.close()

    return {
        "session_id": session_id,
        "question": question,
        "context": context,
        "state": state,
        "created_at": created_at,
    }


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    connection = _connect()
    row = connection.execute(
        "SELECT id, question, context, state_json, created_at FROM sessions WHERE id = ?",
        (session_id,),
    ).fetchone()
    connection.close()

    if row is None:
        return None

    state = json.loads(row["state_json"])
    return {
        "session_id": row["id"],
        "question": row["question"],
        "context": row["context"],
        "state": state,
        "created_at": row["created_at"],
    }


def update_session_run(session_id: str) -> Optional[Dict[str, Any]]:
    session = get_session(session_id)
    if session is None:
        return None

    state = dict(session["state"])
    state["current_stage"] = "conclusion"
    state["status"] = "completed"
    state["iteration"] = state.get("iteration", 0) + 1
    state.setdefault("nodes", []).extend(
        [
            {"id": "question-node", "type": "question", "status": "completed"},
            {"id": "hypothesis-node", "type": "hypothesis", "status": "completed"},
            {"id": "conclusion-node", "type": "conclusion", "status": "completed"},
        ]
    )
    state["stages"] = [
        "question",
        "hypothesis",
        "evidence",
        "perspectives",
        "judge",
        "confidence",
        "conclusion",
    ]
    state["summary"] = {
        "question": session["question"],
        "conclusion": "Reasoning workflow prepared for Phase 2 orchestration.",
    }

    connection = _connect()
    connection.execute(
        "UPDATE sessions SET state_json = ? WHERE id = ?",
        (json.dumps(state), session_id),
    )
    connection.commit()
    connection.close()

    session["state"] = state
    return session
