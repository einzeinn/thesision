from typing import Any

from src.backend.agents.reasoning_agents import (
    ConclusionGenerator,
    EvidenceRetriever,
    HypothesisGenerator,
    Judge,
    PerspectiveAnalyzer,
)
from src.backend.services.openai_client import LanguageModel, ReasoningProviderError
from src.backend.state.session_store import update_session_state


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

    def run(self, session: dict[str, Any]) -> dict[str, Any]:
        state = session["state"]
        state["status"] = "running"
        state["errors"] = []
        self._persist(session["session_id"], state)
        context = state.get("metadata", {}).get("context", "")
        try:
            for iteration in range(1, self.maximum_iterations + 1):
                state["iteration"] = iteration
                self._run_stage(session["session_id"], state, "hypothesis", self.hypotheses.run, session["question"], context)
                self._run_stage(session["session_id"], state, "evidence", self.evidence.run, session["question"], state["hypothesis"])
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
        except ReasoningProviderError as error:
            state["status"] = "failed"
            state["errors"].append(str(error))
        except Exception as error:
            state["status"] = "failed"
            state["errors"].append(f"Reasoning pipeline failed during {state['current_stage']}: {error}")
        return self._persist(session["session_id"], state) or session

    def _run_stage(self, session_id: str, state: dict[str, Any], stage: str, action: Any, *args: Any) -> None:
        state["current_stage"] = stage
        state.setdefault("stages", {})[stage] = {"status": "running"}
        self._persist(session_id, state)
        result = action(self.model, *args)
        self._complete_stage(state, stage, result)
        self._persist(session_id, state)

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
                    "data": {"conflicts": conflicts, "summary": "No unresolved conflict detected." if not conflicts else "Conflicts require inspection."},
                }
            )

    def _evaluate_confidence(self, state: dict[str, Any]) -> dict[str, Any]:
        evidence = state.get("evidence", {}).get("evidence", [])
        perspectives = state.get("perspectives", {}).get("perspectives", [])
        conflicts = state.get("judge", {}).get("unresolved_conflicts", [])
        quality = [self._quality_score(item.get("quality")) for item in evidence if isinstance(item, dict)]
        average_quality = sum(quality) / len(quality) if quality else 0
        score = min(100, round(45 + min(30, average_quality * 0.3) + min(20, len(perspectives) * 6) - min(40, len(conflicts) * 20)))
        return {"score": score, "evidence_quality": average_quality, "perspective_count": len(perspectives), "unresolved_conflicts": conflicts, "has_major_unresolved_conflict": bool(conflicts)}

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
