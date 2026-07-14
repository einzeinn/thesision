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
        context = state.get("metadata", {}).get("context", "")
        try:
            for iteration in range(1, self.maximum_iterations + 1):
                state["iteration"] = iteration
                self._run_stage(state, "hypothesis", self.hypotheses.run, session["question"], context)
                self._run_stage(state, "evidence", self.evidence.run, session["question"], state["hypothesis"])
                self._run_stage(state, "perspectives", self.perspectives.run, session["question"], state["evidence"])
                self._run_stage(state, "judge", self.judge.run, self._reasoning_snapshot(state))
                confidence = self._evaluate_confidence(state)
                self._complete_stage(state, "confidence", confidence)
                if confidence["score"] >= 90 and not confidence["has_major_unresolved_conflict"]:
                    break

            self._run_stage(state, "conclusion", self.conclusion.run, self._reasoning_snapshot(state))
            state["summary"] = state["conclusion"]
            state["status"] = "completed"
        except ReasoningProviderError as error:
            state["status"] = "failed"
            state["errors"].append(str(error))
        return update_session_state(session["session_id"], state) or session

    def _run_stage(self, state: dict[str, Any], stage: str, action: Any, *args: Any) -> None:
        state["current_stage"] = stage
        state.setdefault("stages", {})[stage] = {"status": "running"}
        result = action(self.model, *args)
        self._complete_stage(state, stage, result)

    def _complete_stage(self, state: dict[str, Any], stage: str, result: dict[str, Any]) -> None:
        state[stage] = result
        state.setdefault("stages", {})[stage] = {"status": "completed"}
        state.setdefault("nodes", []).append({"id": f"{stage}-{state['iteration']}", "type": stage, "status": "completed", "data": result})

    def _evaluate_confidence(self, state: dict[str, Any]) -> dict[str, Any]:
        evidence = state.get("evidence", {}).get("evidence", [])
        perspectives = state.get("perspectives", {}).get("perspectives", [])
        conflicts = state.get("judge", {}).get("unresolved_conflicts", [])
        quality = [item.get("quality", 0) for item in evidence if isinstance(item, dict)]
        average_quality = sum(quality) / len(quality) if quality else 0
        score = min(100, round(45 + min(30, average_quality * 0.3) + min(20, len(perspectives) * 6) - min(40, len(conflicts) * 20)))
        return {"score": score, "evidence_quality": average_quality, "perspective_count": len(perspectives), "unresolved_conflicts": conflicts, "has_major_unresolved_conflict": bool(conflicts)}

    @staticmethod
    def _reasoning_snapshot(state: dict[str, Any]) -> dict[str, Any]:
        return {key: state.get(key) for key in ("hypothesis", "evidence", "perspectives", "judge", "confidence")}
