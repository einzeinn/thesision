from typing import Any

from src.backend.services.openai_client import LanguageModel


class HypothesisGenerator:
    def run(self, model: LanguageModel, question: str, context: str) -> dict[str, Any]:
        return model.generate_json(
            "Generate engineering hypotheses. Return JSON with hypotheses (list of {claim, assumptions, unknowns}). Do not make a final recommendation.",
            {"question": question, "context": context},
        )


class EvidenceRetriever:
    def run(self, model: LanguageModel, question: str, hypotheses: dict[str, Any]) -> dict[str, Any]:
        return model.generate_json(
            "Identify evidence relevant to the engineering hypotheses. Return JSON with evidence (list of {claim, source_title, url, relevance, quality}). Only supply a URL when it is known; mark uncertain items clearly. Do not invent a source.",
            {"question": question, "hypotheses": hypotheses},
        )


class PerspectiveAnalyzer:
    def run(self, model: LanguageModel, question: str, evidence: dict[str, Any]) -> dict[str, Any]:
        return model.generate_json(
            "Analyze the engineering decision from maintainability, performance, and scalability perspectives. Return JSON with perspectives (list of {name, analysis, tradeoffs}).",
            {"question": question, "evidence": evidence},
        )


class Judge:
    def run(self, model: LanguageModel, state: dict[str, Any]) -> dict[str, Any]:
        return model.generate_json(
            "Judge the supplied reasoning. Return JSON with validated_claims, conflicts, unresolved_conflicts, and synthesis. Reject unsupported claims rather than filling gaps.",
            state,
        )


class ConclusionGenerator:
    def run(self, model: LanguageModel, state: dict[str, Any]) -> dict[str, Any]:
        return model.generate_json(
            "Write a transparent engineering conclusion from the judged reasoning. Return JSON with conclusion, rationale, caveats, and next_steps. State that the human makes the final decision.",
            state,
        )
