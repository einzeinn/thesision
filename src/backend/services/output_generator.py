import json
from typing import Any


def build_json_export(session: dict[str, Any]) -> str:
    """Preserve the complete persisted payload for portable session continuation."""
    return json.dumps(session, indent=2, ensure_ascii=False)


def build_markdown_report(exported_session_json: str) -> str:
    """Render the canonical JSON export without reinterpreting its reasoning."""
    return "# Thesision Reasoning Report\n\n## Canonical Session State\n\n```json\n" + exported_session_json + "\n```\n"
