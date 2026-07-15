import json
from typing import Any


def build_json_export(session: dict[str, Any]) -> str:
    """Preserve the complete persisted payload for portable session continuation."""
    return json.dumps(session, indent=2, ensure_ascii=False)


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _records(value: Any) -> list[dict[str, Any]]:
    return [record for record in value if isinstance(record, dict)] if isinstance(value, list) else []


def _text(value: Any, fallback: str) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else fallback


def _deterministic_markdown(exported_session_json: str) -> str:
    """Keep exports available without asking a provider to reinterpret the session."""
    session = _mapping(json.loads(exported_session_json))
    state = _mapping(session.get("state"))
    confidence = _mapping(state.get("confidence"))
    conclusion = _mapping(state.get("conclusion"))
    evidence = _records(_mapping(state.get("evidence")).get("evidence"))
    perspectives = _records(_mapping(state.get("perspectives")).get("perspectives"))
    lines = [
        "# Thesision Reasoning Report",
        "",
        "## Question",
        _text(session.get("question"), "No question recorded."),
        "",
        "## Conclusion",
        _text(conclusion.get("conclusion"), "No conclusion was generated."),
        "",
        "## Confidence",
        f"- Score: {confidence.get('score', 'Not evaluated')}%",
        f"- Debate rounds: {state.get('iteration', 0)}",
    ]
    if evidence:
        lines.extend(["", "## Key Evidence"])
        for item in evidence[:5]:
            claim = _text(item.get("claim"), "Untitled evidence")
            source = _text(item.get("source_title"), "Unspecified source")
            url = item.get("url")
            lines.append(f"- {claim} ([{source}]({url}))" if isinstance(url, str) and url else f"- {claim} ({source})")
    if perspectives:
        lines.extend(["", "## Trade-offs"])
        for item in perspectives[:3]:
            lines.append(f"- {_text(item.get('name'), 'Perspective')}: {_text(item.get('analysis'), 'No analysis recorded.')}")
    caveats = [item for item in conclusion.get("caveats", []) if isinstance(item, str) and item.strip()] if isinstance(conclusion.get("caveats"), list) else []
    if caveats:
        lines.extend(["", "## Caveats", *[f"- {item}" for item in caveats]])
    next_steps = [item for item in conclusion.get("next_steps", []) if isinstance(item, str) and item.strip()] if isinstance(conclusion.get("next_steps"), list) else []
    if next_steps:
        lines.extend(["", "## Next Steps", *[f"- {item}" for item in next_steps]])
    return "\n".join(lines) + "\n"


def build_markdown_report(exported_session_json: str, compressed_markdown: str | None = None) -> str:
    """Return model-compressed Markdown, or a concise deterministic JSON-derived fallback."""
    if isinstance(compressed_markdown, str) and compressed_markdown.strip():
        return compressed_markdown.strip() + "\n"
    return _deterministic_markdown(exported_session_json)
