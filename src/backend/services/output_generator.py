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


def _text_list(value: Any) -> list[str]:
    return [item.strip() for item in value if isinstance(item, str) and item.strip()] if isinstance(value, list) else []


def _word_limit(value: Any, limit: int, fallback: str = "Unknown") -> str:
    words = _text(value, fallback).split()
    return " ".join(words[:limit]) + ("..." if len(words) > limit else "")


def _markdown_source(item: dict[str, Any]) -> str:
    source = _text(item.get("source_title"), "Unknown")
    url = item.get("url")
    return f"[{source}]({url})" if isinstance(url, str) and url.strip() else source


def _claim_key(value: Any) -> str:
    return " ".join(_text(value, "").lower().split())


def _latest_node_data(state: dict[str, Any], node_type: str) -> dict[str, Any]:
    for node in reversed(_records(state.get("nodes"))):
        if node.get("type") == node_type:
            return _mapping(node.get("data"))
    return {}


def _historical_records(state: dict[str, Any], node_type: str, data_key: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for node in _records(state.get("nodes")):
        if node.get("type") != node_type:
            continue
        records.extend(_records(_mapping(node.get("data")).get(data_key)))
    if records:
        return records
    latest_key = "perspectives" if node_type == "perspective" else node_type
    return _records(_mapping(state.get(latest_key)).get(data_key))


def _unique_evidence(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in records:
        url = _text(item.get("url"), "").lower().rstrip("/")
        claim = _claim_key(item.get("claim"))
        if not url and not claim:
            continue
        key = f"url:{url}" if url else f"claim:{claim}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _evidence_round_count(state: dict[str, Any]) -> int:
    rounds = {
        node.get("round")
        for node in _records(state.get("nodes"))
        if node.get("type") == "evidence" and isinstance(node.get("round"), int)
    }
    return len(rounds)


def _confidence_lines(confidence: dict[str, Any]) -> list[str]:
    score = confidence.get("score")
    quality = confidence.get("evidence_quality")
    evidence_count = confidence.get("evidence_count")
    evidence_round_count = confidence.get("evidence_round_count")
    perspectives = confidence.get("perspective_count")
    conflicts = _text_list(confidence.get("unresolved_conflicts"))
    if isinstance(score, (int, float)):
        rounded_score = max(0, min(100, round(float(score))))
        completed_cells = round(rounded_score / 10)
        confidence_bar = "█" * completed_cells + "░" * (10 - completed_cells)
        lines = [f"**Overall Confidence:** {confidence_bar} {rounded_score}%"]
    else:
        lines = ["**Overall Confidence:** Unknown"]
    lines.extend(["", "### Reason"])
    if isinstance(quality, (int, float)):
        rounded_quality = round(float(quality))
        scope = ""
        if isinstance(evidence_count, int):
            scope = f" across {evidence_count} unique source(s)"
            if isinstance(evidence_round_count, int) and evidence_round_count > 1:
                scope += f" from {evidence_round_count} rounds"
        lines.append(f"- Evidence quality {'✔' if rounded_quality >= 50 else '✖'} — {rounded_quality} / 100{scope}")
    else:
        lines.append("- Evidence quality — unavailable")
    lines.append(f"- Unresolved conflicts {'✔' if not conflicts else '✖'} — {len(conflicts)} recorded")
    if isinstance(perspectives, int):
        lines.append(f"- Perspective coverage {'✔' if perspectives >= 3 else '✖'} — {perspectives} recorded")
    else:
        lines.append("- Perspective coverage — unavailable")
    lines.extend([
        "",
        "### Explanation",
        "The bar is the persisted overall score. The reason signals are recorded context, not component scores that add up to it.",
    ])
    return lines


def _deterministic_markdown(exported_session_json: str) -> str:
    """Keep exports available without asking a provider to reinterpret the session."""
    session = _mapping(json.loads(exported_session_json))
    state = _mapping(session.get("state"))
    confidence = _mapping(state.get("confidence"))
    conclusion = {**_latest_node_data(state, "conclusion"), **_mapping(state.get("conclusion"))}
    evidence = _unique_evidence(_historical_records(state, "evidence", "evidence"))
    evidence_round_count = _evidence_round_count(state) or (1 if evidence else 0)
    perspectives = _records(_mapping(state.get("perspectives")).get("perspectives"))
    hypotheses = _records(_mapping(state.get("hypothesis")).get("hypotheses"))
    judge = {**_latest_node_data(state, "judge"), **_mapping(state.get("judge"))}
    conflicts = _text_list(judge.get("unresolved_conflicts") or judge.get("conflicts"))
    assumptions = [entry for hypothesis in hypotheses for entry in _text_list(hypothesis.get("assumptions"))]
    unknowns = [entry for hypothesis in hypotheses for entry in _text_list(hypothesis.get("unknowns"))]
    caveats = _text_list(conclusion.get("caveats"))
    next_steps = _text_list(conclusion.get("next_steps"))
    validated_claims = _text_list(judge.get("validated_claims"))
    judge_summary = _text(judge.get("synthesis"), validated_claims[0] if validated_claims else "No Judge synthesis was recorded.")
    lines = [
        "# Thesision Reasoning Report",
        "",
        "## Question",
        _text(session.get("question"), "No question recorded."),
        "",
        "## Confidence",
        *_confidence_lines(confidence),
        f"\n**Debate rounds:** {state.get('iteration', 0)}",
    ]
    lines.extend(["", "## Evidence Assessment"])
    if not evidence:
        lines.append("No evidence was recorded.")
    else:
        lines.extend([
            f"{len(evidence)} unique source(s) were recorded across {evidence_round_count} reasoning round(s). The table shows up to eight most recent sources; JSON retains the complete session.",
            "",
            "| # | Finding | Source focus | Strength |",
            "| --- | --- | --- | --- |",
        ])
    for index, item in enumerate(evidence[-8:], start=max(1, len(evidence) - 7)):
        summary = _word_limit(item.get("claim"), 24, "No source summary was returned.")
        lines.append(f"| {index} | {summary} | {_markdown_source(item)} | {_text(item.get('quality'), 'Not recorded')} |")
    lines.extend(["", "## Reasoning Trace", f"1. **Question:** {_word_limit(session.get('question'), 28, 'Unknown')}"])
    for index, hypothesis in enumerate(hypotheses[:3], start=1):
        lines.append(f"2.{index}. **Hypothesis:** {_word_limit(hypothesis.get('claim'), 35, 'Unknown')}")
    lines.append(f"3. **Evidence:** {len(evidence)} recorded item(s) were considered.")
    if perspectives:
        lines.append("4. **Perspectives:** " + ", ".join(_text(item.get("name"), "Unknown") for item in perspectives[:3]) + ".")
    if conflicts:
        lines.append("5. **Conflicts:** " + "; ".join(_word_limit(item, 24) for item in conflicts[:3]))
    else:
        lines.append("5. **Conflicts:** No unresolved conflicts were recorded by the Judge.")
    lines.extend([
        f"6. **Judge:** {_word_limit(judge_summary, 32, 'No Judge synthesis was recorded.')}",
        "7. **Final conclusion:** See the recommendation below.",
        "",
        "## Trade-offs",
    ])
    if perspectives:
        for item in perspectives[:5]:
            tradeoffs = _text_list(item.get("tradeoffs"))
            recorded_view = "; ".join(tradeoffs) if tradeoffs else _text(item.get("analysis"), "No recorded trade-off.")
            lines.append(f"- **{_text(item.get('name'), 'Perspective')}:** {_word_limit(recorded_view, 32)}")
    else:
        lines.append("No perspectives were recorded.")
    lines.extend(["", "## Caveats"])
    if caveats:
        for caveat in caveats[:4]:
            lines.append(f"- {_word_limit(caveat, 32)}")
    else:
        lines.append("No caveats were recorded.")
    lines.extend(["", "## Decision Would Change If"])
    conditions = [f"A key unknown resolves differently: {item}" for item in unknowns[:3]]
    conditions += [f"An unresolved conflict resolves differently: {item}" for item in conflicts[:2]]
    conditions += [f"A planned validation changes the result: {item}" for item in next_steps[:3]]
    conditions += [f"A core assumption is disproved: {item}" for item in assumptions[:2]]
    lines.extend([
        "<details>",
        f"<summary>{len(conditions)} key conditions — select to expand</summary>",
        "",
        *([f"- {item}" for item in conditions] or ["- No decision-change conditions were recorded."]),
        "",
        "</details>",
    ])
    recorded_rationale = _text(conclusion.get("rationale"), "")
    recorded_judge_synthesis = _text(judge.get("synthesis"), "")
    if recorded_rationale:
        why = recorded_rationale
    elif recorded_judge_synthesis:
        why = recorded_judge_synthesis
    elif validated_claims:
        why = "; ".join(validated_claims)
    else:
        score = confidence.get("score")
        confidence_context = f" Overall confidence is {score} / 100." if isinstance(score, (int, float)) else ""
        why = (
            f"The session considered {len(evidence)} evidence item(s) across {len(perspectives)} perspective(s) "
            f"and recorded {len(conflicts)} unresolved conflict(s)." + confidence_context
        )
    lines.extend([
        "",
        "## Conclusion",
        f"**Recommendation:** {_word_limit(conclusion.get('conclusion'), 50, 'No conclusion was generated.')}",
        f"**Why:** {_word_limit(why, 42, 'No canonical rationale was recorded.')}",
        "**Would change if:** See **Decision Would Change If** above.",
    ])
    return "\n".join(lines) + "\n"


def build_markdown_report(exported_session_json: str, compressed_markdown: str | None = None) -> str:
    """Return model-compressed Markdown, or a concise deterministic JSON-derived fallback."""
    required_sections = ("## Confidence", "█", "### Reason", "## Evidence", "| # | Finding | Source focus | Strength |", "## Reasoning Trace", "## Caveats", "## Decision Would Change If", "<details>", "## Conclusion")
    # A report that omits cumulative scope would make later-round sources look ignored.
    has_cumulative_evidence_scope = isinstance(compressed_markdown, str) and "unique source" in compressed_markdown.lower() and "round" in compressed_markdown.lower()
    if isinstance(compressed_markdown, str) and compressed_markdown.strip() and has_cumulative_evidence_scope and all(section in compressed_markdown for section in required_sections):
        return compressed_markdown.strip() + "\n"
    return _deterministic_markdown(exported_session_json)
