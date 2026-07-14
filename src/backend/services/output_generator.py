import json
from typing import Any


def build_markdown_report(session: dict[str, Any]) -> str:
    """Render the persisted reasoning state without adding new interpretation."""
    state = session["state"]
    confidence = state.get("confidence", {})
    evidence = state.get("evidence", {}).get("evidence", [])
    perspectives = state.get("perspectives", {}).get("perspectives", [])
    judge = state.get("judge", {})
    conclusion = state.get("conclusion", {})

    lines = [
        "# Thesision Reasoning Report",
        "",
        "## Question",
        session["question"],
        "",
        "## Confidence",
        f"- Score: {confidence.get('score', 'Not evaluated')}%",
        f"- Iterations: {state.get('iteration', 0)}",
        f"- Unresolved conflicts: {len(confidence.get('unresolved_conflicts', []))}",
        "",
        "## Hypotheses",
    ]
    for hypothesis in state.get("hypothesis", {}).get("hypotheses", []):
        lines.append(f"- {hypothesis.get('claim', 'Untitled hypothesis')}")
    lines.extend(["", "## Evidence"])
    for item in evidence:
        source = item.get("source_title") or "Unspecified source"
        url = item.get("url")
        reference = f" ([{source}]({url}))" if url else f" ({source})"
        lines.append(f"- {item.get('claim', 'Untitled evidence')}{reference}")
    lines.extend(["", "## Perspectives"])
    for perspective in perspectives:
        lines.append(f"### {perspective.get('name', 'Perspective')}")
        lines.append(perspective.get("analysis", "No analysis recorded."))
        tradeoffs = perspective.get("tradeoffs", [])
        if tradeoffs:
            lines.append(f"Trade-offs: {', '.join(tradeoffs)}")
    lines.extend(["", "## Judge", judge.get("synthesis", "No synthesis recorded."), "", "## Conclusion"])
    lines.append(conclusion.get("conclusion", "No conclusion was generated."))
    if conclusion.get("rationale"):
        lines.extend(["", "### Rationale", conclusion["rationale"]])
    if conclusion.get("caveats"):
        lines.extend(["", "### Caveats", *[f"- {item}" for item in conclusion["caveats"]]])
    lines.extend(["", "_Thesision supports engineering judgment; the final decision remains human._", ""])
    return "\n".join(lines)


def build_json_export(session: dict[str, Any]) -> str:
    """Preserve the complete persisted payload for portable session continuation."""
    return json.dumps(session, indent=2, ensure_ascii=False)
