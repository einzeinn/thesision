import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

ROOT_DIR = Path(__file__).resolve().parents[3]
DB_PATH = Path(os.getenv("THESISION_DATA_DIR", str(ROOT_DIR / "data"))) / "thesision.db"
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


def storage_ready() -> bool:
    try:
        connection = _connect()
        connection.execute("SELECT 1")
        connection.close()
        return True
    except sqlite3.Error:
        return False


def create_session(question: str, context: Optional[str] = None) -> Dict[str, Any]:
    session_id = str(uuid.uuid4())
    state = {
        "current_stage": "question",
        "status": "created",
        "iteration": 0,
        "nodes": [],
        "edges": [],
        "stages": {"question": {"status": "completed"}},
        "metadata": {"context": context or ""},
        "pipeline": PIPELINE_STAGES,
        "summary": None,
        "errors": [],
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


def import_completed_session(exported: Dict[str, Any]) -> Dict[str, Any]:
    question = exported.get("question")
    state = exported.get("state")
    if not isinstance(question, str) or not question.strip() or len(question) > 4_000:
        raise ValueError("Imported session has an invalid question.")
    if not isinstance(state, dict) or state.get("status") != "completed":
        raise ValueError("Only a completed Thesision JSON export can be imported.")
    if not isinstance(state.get("nodes"), list) or not isinstance(state.get("stages"), dict):
        raise ValueError("Imported session is missing required reasoning state.")

    session_id = str(uuid.uuid4())
    context = exported.get("context")
    context_value = context if isinstance(context, str) else None
    created_at = datetime.now(timezone.utc).isoformat()
    connection = _connect()
    connection.execute(
        "INSERT INTO sessions (id, question, context, state_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, question, context_value, json.dumps(state), created_at),
    )
    connection.commit()
    connection.close()
    return {"session_id": session_id, "question": question, "context": context_value, "state": state, "created_at": created_at}


def create_continuation_session(parent: Dict[str, Any]) -> Dict[str, Any]:
    source_state = parent.get("state")
    if not isinstance(source_state, dict) or source_state.get("status") != "completed":
        raise ValueError("Only a completed session can be continued.")
    state = json.loads(json.dumps(source_state))
    state["status"] = "created"
    state["errors"] = []
    state["summary"] = None
    state.pop("conclusion", None)
    state["nodes"] = [node for node in state.get("nodes", []) if isinstance(node, dict) and node.get("type") != "conclusion"]
    state.setdefault("stages", {})["conclusion"] = {"status": "pending"}
    state.setdefault("metadata", {})["parent_session_id"] = parent["session_id"]

    session_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    connection = _connect()
    connection.execute(
        "INSERT INTO sessions (id, question, context, state_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, parent["question"], parent.get("context"), json.dumps(state), created_at),
    )
    connection.commit()
    connection.close()
    return {"session_id": session_id, "question": parent["question"], "context": parent.get("context"), "state": state, "created_at": created_at}


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


def update_session_state(session_id: str, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    session = get_session(session_id)
    if session is None:
        return None

    connection = _connect()
    connection.execute(
        "UPDATE sessions SET state_json = ? WHERE id = ?",
        (json.dumps(state), session_id),
    )
    connection.commit()
    connection.close()

    session["state"] = state
    return session
