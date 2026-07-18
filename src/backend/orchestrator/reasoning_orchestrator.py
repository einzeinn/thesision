import json
import os
import time
import logging
from typing import Any

from src.backend.agents.reasoning_agents import (
    ConclusionGenerator,
    EvidenceRetriever,
    HypothesisGenerator,
    Judge,
    MarkdownReportComposer,
    PerspectiveAnalyzer,
)
from src.backend.services.openai_client import LanguageModel, ReasoningProviderError
from src.backend.services.output_generator import build_json_export, build_markdown_report
from src.backend.state.session_store import update_session_state

logger = logging.getLogger("thesision")


class ReasoningOrchestrator:
    """The sole coordinator of reasoning agents and persisted session progress."""

    def __init__(self, model: LanguageModel, maximum_iterations: int = 3) -> None:
        self.model = model
        self.maximum_iterations = maximum_iterations
        self.hypotheses = HypothesisGenerator()
        self.evidence = EvidenceRetriever()
        self.perspectives = PerspectiveAnalyzer()
        self.judge = Judge()
        self.conclusion = ConclusionGenerator()
        self.markdown_reporter = MarkdownReportComposer()

    def run(self, session: dict[str, Any]) -> dict[str, Any]:
        deadline = time.monotonic() + float(os.getenv("REASONING_TIMEOUT_SECONDS", "180"))
        state = session["state"]
        provider = getattr(self.model, "provider", "custom")
        state["status"] = "running"
        state["errors"] = []
        self._persist(session["session_id"], state)
        context = state.get("metadata", {}).get("context", "")
        try:
            first_iteration = int(state.get("iteration", 0)) + 1
            for iteration in range(first_iteration, first_iteration + self.maximum_iterations):
                if time.monotonic() >= deadline:
                    raise ReasoningProviderError("Reasoning session timed out before completion.")
                state["iteration"] = iteration
                prior_round = self._prior_round_context(state)
                self._run_stage(session["session_id"], state, "hypothesis", self.hypotheses.run, session["question"], context, prior_round)
                self._run_stage(session["session_id"], state, "evidence", self.evidence.run, session["question"], state["hypothesis"], prior_round)
                self._run_stage(session["session_id"], state, "perspectives", self.perspectives.run, session["question"], state["evidence"])
                self._run_stage(session["session_id"], state, "judge", self.judge.run, self._reasoning_snapshot(state))
                confidence = self._evaluate_confidence(state)
                self._complete_stage(state, "confidence", confidence)
                self._persist(session["session_id"], state)
                if confidence["score"] >= 90 and not confidence["has_major_unresolved_conflict"]:
                    break

            self._run_stage(session["session_id"], state, "conclusion", self.conclusion.run, self._reasoning_snapshot(state))
            state["summary"] = state["conclusion"]
            state["status"] = "completed"
            logger.info('{"event":"reasoning_completed","session_id":"%s","provider":"%s","outcome":"completed"}', session["session_id"], provider)
        except ReasoningProviderError as error:
            state["status"] = "failed"
            state["errors"].append(str(error))
            logger.info('{"event":"reasoning_completed","session_id":"%s","provider":"%s","outcome":"provider_error"}', session["session_id"], provider)
        except Exception as error:
            state["status"] = "failed"
            state["errors"].append(f"Reasoning pipeline failed during {state['current_stage']}: {error}")
            logger.exception('{"event":"reasoning_completed","session_id":"%s","provider":"%s","outcome":"unexpected_error"}', session["session_id"], provider)
        return self._persist(session["session_id"], state) or session

    def build_markdown_report(self, session: dict[str, Any]) -> str:
        exported_session_json = build_json_export(session)
        try:
            exported_session = json.loads(exported_session_json)
            result = self.markdown_reporter.run(self.model, exported_session)
            markdown = result.get("markdown") if isinstance(result, dict) else None
            return build_markdown_report(exported_session_json, markdown)
        except (ReasoningProviderError, ValueError, TypeError) as error:
            logger.info('{"event":"markdown_export","session_id":"%s","outcome":"deterministic_fallback","reason":"%s"}', session["session_id"], type(error).__name__)
            return build_markdown_report(exported_session_json)

    def _run_stage(self, session_id: str, state: dict[str, Any], stage: str, action: Any, *args: Any) -> None:
        started_at = time.monotonic()
        state["current_stage"] = stage
        state.setdefault("stages", {})[stage] = {"status": "running"}
        self._persist(session_id, state)
        result = action(self.model, *args)
        self._complete_stage(state, stage, result)
        self._persist(session_id, state)
        logger.info('{"event":"reasoning_stage","session_id":"%s","stage":"%s","provider":"%s","outcome":"completed","duration_ms":%s}', session_id, stage, getattr(self.model, "provider", "custom"), round((time.monotonic() - started_at) * 1000))

    @staticmethod
    def _persist(session_id: str, state: dict[str, Any]) -> dict[str, Any] | None:
        return update_session_state(session_id, state)

    def _complete_stage(self, state: dict[str, Any], stage: str, result: dict[str, Any]) -> None:
        state[stage] = result
        state.setdefault("stages", {})[stage] = {"status": "completed"}
        node_type = {"perspectives": "perspective"}.get(stage, stage)
        node_round = state["iteration"] + 1 if stage == "conclusion" else state["iteration"]
        state.setdefault("nodes", []).append({"id": f"{node_type}-{node_round}", "type": node_type, "round": node_round, "status": "completed", "data": result})
        if stage == "judge":
            conflicts = result.get("unresolved_conflicts") or result.get("conflicts") or []
            state["nodes"].append(
                {
                    "id": f"conflict-{state['iteration']}",
                    "type": "conflict",
                    "round": state["iteration"],
                    "status": "completed",
                    # The Judge owns this explanation; orchestration must not fabricate a conflict result.
                    "data": {
                        "conflicts": conflicts,
                        "summary": result["conflict_summary"],
                    },
                }
            )

    def _evaluate_confidence(self, state: dict[str, Any]) -> dict[str, Any]:
        # Nodes preserve every completed round; current state fields hold only the latest one.
        evidence = self._unique_evidence(self._historical_records(state, "evidence", "evidence"))
        perspectives = self._unique_perspectives(self._historical_records(state, "perspective", "perspectives"))
        conflicts = state.get("judge", {}).get("unresolved_conflicts", [])
        quality = [self._quality_score(item.get("quality")) for item in evidence if isinstance(item, dict)]
        average_quality = sum(quality) / len(quality) if quality else 0
        score = min(100, round(45 + min(30, average_quality * 0.3) + min(20, len(perspectives) * 6) - min(40, len(conflicts) * 20)))
        evidence_round_count = len(
            {
                node.get("round")
                for node in state.get("nodes", [])
                if isinstance(node, dict) and node.get("type") == "evidence" and isinstance(node.get("round"), int)
            }
        )
        return {
            "score": score,
            "evidence_quality": average_quality,
            "evidence_count": len(evidence),
            "evidence_round_count": evidence_round_count or (1 if evidence else 0),
            "perspective_count": len(perspectives),
            "unresolved_conflicts": conflicts,
            "has_major_unresolved_conflict": bool(conflicts),
        }

    @staticmethod
    def _historical_records(state: dict[str, Any], node_type: str, data_key: str) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for node in state.get("nodes", []):
            if not isinstance(node, dict) or node.get("type") != node_type:
                continue
            data = node.get("data")
            if isinstance(data, dict):
                records.extend(item for item in data.get(data_key, []) if isinstance(item, dict))
        if records:
            return records
        latest_key = "perspectives" if node_type == "perspective" else node_type
        latest = state.get(latest_key)
        return [item for item in latest.get(data_key, []) if isinstance(item, dict)] if isinstance(latest, dict) else []

    @staticmethod
    def _unique_evidence(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        unique: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in records:
            url = item.get("url") if isinstance(item.get("url"), str) else ""
            claim = item.get("claim") if isinstance(item.get("claim"), str) else ""
            normalized_url = url.strip().lower().rstrip("/")
            normalized_claim = " ".join(claim.lower().split())
            if not normalized_url and not normalized_claim:
                continue
            key = f"url:{normalized_url}" if normalized_url else f"claim:{normalized_claim}"
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
        return unique

    @staticmethod
    def _unique_perspectives(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        unique: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in records:
            name = item.get("name") if isinstance(item.get("name"), str) else ""
            key = " ".join(name.lower().split())
            if not key or key in seen:
                continue
            seen.add(key)
            unique.append(item)
        return unique

    @staticmethod
    def _quality_score(value: Any) -> float:
        if isinstance(value, (int, float)):
            return max(0, min(100, float(value)))
        if isinstance(value, str):
            return {"high": 100, "medium": 60, "low": 30}.get(value.strip().lower(), 0)
        return 0

    @staticmethod
    def _reasoning_snapshot(state: dict[str, Any]) -> dict[str, Any]:
        return {key: state.get(key) for key in ("hypothesis", "evidence", "perspectives", "judge", "confidence")}

    @staticmethod
    def _prior_round_context(state: dict[str, Any]) -> dict[str, Any] | None:
        """Focus later rounds on a canonical gap without changing public session data."""
        judge = state.get("judge")
        if not isinstance(judge, dict):
            return None
        evidence_history: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for node in state.get("nodes", []):
            if not isinstance(node, dict) or node.get("type") != "evidence":
                continue
            data = node.get("data")
            if not isinstance(data, dict):
                continue
            for item in data.get("evidence", []):
                if not isinstance(item, dict):
                    continue
                url = item.get("url") if isinstance(item.get("url"), str) else ""
                claim = item.get("claim") if isinstance(item.get("claim"), str) else ""
                key = (url.strip(), claim.strip())
                if key in seen or not any(key):
                    continue
                seen.add(key)
                evidence_history.append(
                    {
                        key: item[key]
                        for key in ("claim", "source_title", "url", "quality")
                        if isinstance(item.get(key), (str, int, float))
                    }
                )
        return {
            "judge": judge,
            "confidence": state.get("confidence") if isinstance(state.get("confidence"), dict) else {},
            "previous_evidence": evidence_history[-20:],
            "refinement_target": ReasoningOrchestrator._select_refinement_target(state, judge),
        }

    @staticmethod
    def _select_refinement_target(state: dict[str, Any], judge: dict[str, Any]) -> dict[str, Any]:
        """Use deterministic artifact priority so later rounds investigate a real recorded gap."""
        prior_round = ReasoningOrchestrator._latest_artifact_round(state, "judge")
        conflicts = judge.get("unresolved_conflicts")
        if isinstance(conflicts, list):
            for conflict in conflicts:
                if isinstance(conflict, str) and conflict.strip():
                    return {"type": "conflict", "text": conflict.strip(), "round": ReasoningOrchestrator._latest_artifact_round(state, "conflict") or prior_round}

        evidence = state.get("evidence")
        items = evidence.get("evidence") if isinstance(evidence, dict) else []
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict):
                    continue
                quality = item.get("quality")
                normalized_quality = quality.strip().lower() if isinstance(quality, str) else ""
                url = item.get("url")
                claim = item.get("claim")
                if (not isinstance(url, str) or not url.strip()) or normalized_quality in {"", "low", "unverified"}:
                    text = claim.strip() if isinstance(claim, str) and claim.strip() else "Verify the missing or weak evidence."
                    return {"type": "evidence_gap", "text": text, "round": ReasoningOrchestrator._latest_artifact_round(state, "evidence") or prior_round}

        perspectives = state.get("perspectives")
        entries = perspectives.get("perspectives") if isinstance(perspectives, dict) else []
        if isinstance(entries, list):
            named_tradeoffs = [
                (item.get("name").strip(), item.get("tradeoffs"))
                for item in entries
                if isinstance(item, dict)
                and isinstance(item.get("name"), str)
                and item.get("name").strip()
                and isinstance(item.get("tradeoffs"), list)
                and any(isinstance(tradeoff, str) and tradeoff.strip() for tradeoff in item["tradeoffs"])
            ]
            if named_tradeoffs:
                name, tradeoffs = named_tradeoffs[0]
                first_tradeoff = next(tradeoff.strip() for tradeoff in tradeoffs if isinstance(tradeoff, str) and tradeoff.strip())
                return {"type": "perspective_tradeoff", "text": f"Evaluate the {name} trade-off: {first_tradeoff}", "round": ReasoningOrchestrator._latest_artifact_round(state, "perspective") or prior_round}

        synthesis = judge.get("synthesis")
        if isinstance(synthesis, str) and synthesis.strip():
            return {"type": "judge_synthesis", "text": synthesis.strip(), "round": prior_round}
        return {"type": "judge_synthesis", "text": "Refine the latest recorded decision gap.", "round": prior_round}

    @staticmethod
    def _latest_artifact_round(state: dict[str, Any], node_type: str) -> int | None:
        for node in reversed(state.get("nodes", [])):
            if isinstance(node, dict) and node.get("type") == node_type and isinstance(node.get("round"), int):
                return node["round"]
        iteration = state.get("iteration")
        return iteration - 1 if isinstance(iteration, int) and iteration > 0 else None
