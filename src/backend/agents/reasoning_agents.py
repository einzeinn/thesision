from typing import Any

from src.backend.services.openai_client import LanguageModel, ReasoningProviderError


class HypothesisGenerator:
    def run(self, model: LanguageModel, question: str, context: str) -> dict[str, Any]:
        return model.generate_json(
            "Generate engineering hypotheses. Return JSON with hypotheses (list of {claim, assumptions, unknowns}). Do not make a final recommendation.",
            {"question": question, "context": context},
        )


class EvidenceRetriever:
    def run(self, model: LanguageModel, question: str, hypotheses: dict[str, Any]) -> dict[str, Any]:
        try:
            return model.generate_json(
                "Use the web search tool to retrieve sources for the engineering hypotheses; do not rely on recalled citations. Return JSON with evidence (list of {claim, source_title, url, relevance, quality}). Include a URL only when it was returned by the web search tool and directly supports the attached claim. If no relevant result exists, return an item with url null, source_title 'No verified web source found', and relevance and quality 'unverified'. Never invent a source, title, or URL.",
                {"question": question, "hypotheses": hypotheses},
                tools=[{"type": "web_search"}],
            )
        except ReasoningProviderError as error:
            if "hosted web search" not in str(error):
                raise
            considerations = model.generate_json(
                "The configured provider cannot browse the web. Generate 3 to 5 concrete engineering considerations that follow from the question and hypotheses, covering measurable risks, constraints, or validation steps. Return JSON with evidence (list of {claim}). Do not cite, name, or imply any external source. These are unverified model-derived considerations, not web evidence.",
                {"question": question, "hypotheses": hypotheses},
            )
            items = considerations.get("evidence", []) if isinstance(considerations, dict) else []
            normalized = []
            for item in items:
                if isinstance(item, dict) and isinstance(item.get("claim"), str) and item["claim"].strip():
                    normalized.append(
                        {
                            "claim": item["claim"].strip(),
                            "source_title": "Model-derived consideration (not web-verified)",
                            "url": None,
                            "relevance": "model-derived",
                            "quality": "unverified",
                        }
                    )
            return {"evidence": normalized or [{
                "claim": "No verified web evidence is available because the configured provider does not support grounded search.",
                "source_title": "Evidence grounding unavailable for AI/ML API",
                "url": None,
                "relevance": "unverified",
                "quality": "unverified",
            }]}


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


class MarkdownReportComposer:
    def run(self, model: LanguageModel, exported_session: dict[str, Any]) -> dict[str, Any]:
        return model.generate_json(
            "Create a concise Markdown engineering report from canonical session JSON. Return JSON with one string field: markdown. Include only Question, Conclusion, Confidence, Key Evidence, Trade-offs, Caveats, and Next Steps when present. Do not invent, infer, or change any claim, source, URL, recommendation, or number. Do not include the raw JSON, a code fence, or commentary about this instruction.",
            {"canonical_session": exported_session},
        )
