from typing import Any

from src.backend.services.openai_client import LanguageModel, ReasoningProviderError


class HypothesisGenerator:
    def run(
        self,
        model: LanguageModel,
        question: str,
        context: str,
        prior_round: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        refinement_context = prior_round or {}
        is_refinement = bool(refinement_context)
        return model.generate_json(
            (
                "Generate engineering hypotheses. Return JSON with hypotheses (list of {claim, assumptions, unknowns}). "
                "Do not make a final recommendation. "
                + (
                    "This is a refinement round. The canonical refinement_target identifies the specific prior artifact to test. "
                    "Generate hypotheses that directly investigate that target, while retaining the original question as context. "
                    "Do not merely restate an unchanged earlier hypothesis."
                    if is_refinement
                    else "This is the initial reasoning round."
                )
            ),
            {
                "question": question,
                "context": context,
                **({"prior_round": refinement_context} if is_refinement else {}),
            },
        )


class EvidenceRetriever:
    def run(
        self,
        model: LanguageModel,
        question: str,
        hypotheses: dict[str, Any],
        prior_round: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        refinement_context = prior_round or {}
        is_refinement = bool(refinement_context)
        try:
            result = model.generate_json(
                (
                    "Use the web search tool to retrieve sources for the engineering hypotheses; do not rely on recalled citations. "
                    "Return JSON with evidence (list of {claim, source_title, url, relevance, quality}). Include a URL only when it "
                    "was returned by the web search tool and directly supports the attached claim. If no relevant result exists, return an "
                    "item with url null, source_title 'No verified web source found', and relevance and quality 'unverified'. Never invent "
                    "a source, title, or URL. "
                    + (
                        "This is a refinement round: retrieve evidence specifically relevant to canonical refinement_target, and do not return a URL "
                        "already present in previous_evidence unless it supplies a materially distinct finding."
                        if is_refinement
                        else ""
                    )
                ),
                {
                    "question": question,
                    "hypotheses": hypotheses,
                    **({"prior_round": refinement_context} if is_refinement else {}),
                },
                tools=[{"type": "web_search"}],
            )
            return self._exclude_previously_seen_urls(result, refinement_context)
        except ReasoningProviderError as error:
            if getattr(model, "provider", None) != "aimlapi" and "hosted web search" not in str(error):
                raise
            considerations = model.generate_json(
                "The configured provider cannot browse the web. Generate 3 to 5 concrete engineering considerations that follow from the question and hypotheses, covering measurable risks, constraints, or validation steps. Return JSON with evidence (list of {claim}). Do not cite, name, or imply any external source. These are unverified model-derived considerations, not web evidence.",
                {
                    "question": question,
                    "hypotheses": hypotheses,
                    **({"prior_round": refinement_context} if is_refinement else {}),
                },
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

    @staticmethod
    def _exclude_previously_seen_urls(
        result: dict[str, Any], prior_round: dict[str, Any],
    ) -> dict[str, Any]:
        history = prior_round.get("previous_evidence")
        if not isinstance(history, list):
            return result
        known_urls = {
            item["url"].rstrip("/")
            for item in history
            if isinstance(item, dict) and isinstance(item.get("url"), str) and item["url"].strip()
        }
        if not known_urls or not isinstance(result.get("evidence"), list):
            return result
        fresh = [
            item
            for item in result["evidence"]
            if not isinstance(item, dict)
            or not isinstance(item.get("url"), str)
            or item["url"].rstrip("/") not in known_urls
        ]
        if fresh:
            return {**result, "evidence": fresh}
        return {
            **result,
            "evidence": [
                {
                    "claim": "No new verified web source was returned beyond sources already considered.",
                    "source_title": "No new verified web source found",
                    "url": None,
                    "relevance": "unverified",
                    "quality": "unverified",
                }
            ],
        }


class PerspectiveAnalyzer:
    def run(self, model: LanguageModel, question: str, evidence: dict[str, Any]) -> dict[str, Any]:
        return model.generate_json(
            "Analyze the engineering decision from maintainability, performance, and scalability perspectives. Return JSON with perspectives (list of {name, analysis, tradeoffs}).",
            {"question": question, "evidence": evidence},
        )


class Judge:
    def run(self, model: LanguageModel, state: dict[str, Any]) -> dict[str, Any]:
        result = model.generate_json(self._instruction(), state)
        normalized = self._normalize(result)
        if normalized is not None:
            return normalized

        repaired = model.generate_json(
            "Repair this incomplete Judge output. Return only JSON that satisfies the Judge contract. "
            "Do not add facts, sources, or claims absent from the supplied reasoning artifacts. "
            "Both conflict_summary and synthesis must be non-empty strings, even when no conflict exists.",
            {"reasoning": state, "incomplete_judge_output": result},
        )
        normalized = self._normalize(repaired)
        if normalized is not None:
            return normalized
        raise ReasoningProviderError(
            "Judge returned incomplete reasoning output after repair; no misleading Judge or Conflict result was saved."
        )

    @staticmethod
    def _instruction() -> str:
        return (
            "Judge the supplied reasoning by comparing the hypotheses, grounded evidence, and perspectives. "
            "Return JSON with validated_claims (list of strings), conflicts (list of strings), "
            "unresolved_conflicts (list of strings), conflict_summary (non-empty string), and synthesis "
            "(non-empty string). conflict_summary must explain either the material conflict and its impact, "
            "or why no material conflict remains. synthesis must state the comparative result and why it "
            "follows from the recorded artifacts. Reject unsupported claims rather than filling gaps."
        )

    @staticmethod
    def _string_list(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]

    def _normalize(self, result: Any) -> dict[str, Any] | None:
        if not isinstance(result, dict):
            return None
        synthesis = result.get("synthesis")
        conflict_summary = result.get("conflict_summary")
        if not isinstance(synthesis, str) or not synthesis.strip():
            return None
        if not isinstance(conflict_summary, str) or not conflict_summary.strip():
            return None
        return {
            "validated_claims": self._string_list(result.get("validated_claims")),
            "conflicts": self._string_list(result.get("conflicts")),
            "unresolved_conflicts": self._string_list(result.get("unresolved_conflicts")),
            "conflict_summary": conflict_summary.strip(),
            "synthesis": synthesis.strip(),
        }


class ConclusionGenerator:
    def run(self, model: LanguageModel, state: dict[str, Any]) -> dict[str, Any]:
        return model.generate_json(
            "Write a transparent engineering conclusion from the judged reasoning. Return JSON with conclusion, rationale, caveats, and next_steps. State that the human makes the final decision.",
            state,
        )


class MarkdownReportComposer:
    def run(self, model: LanguageModel, exported_session: dict[str, Any]) -> dict[str, Any]:
        return model.generate_json(
            "Create a concise, explainable Markdown engineering report from canonical session JSON. Return JSON with one string field: markdown. Use these headings exactly: Question, Confidence, Evidence Assessment, Reasoning Trace, Trade-offs, Caveats, Decision Would Change If, Conclusion. In Confidence, render the persisted overall score as a ten-cell █/░ bar followed by its percentage, then a ### Reason list for recorded evidence quality, unresolved conflicts, and perspective coverage; these are context signals, not component scores. Explain confidence only with canonical evaluator inputs; mark unavailable dimensions Unknown. Evidence is cumulative: gather every Evidence graph node, deduplicate only identical URLs, state the total unique-source and round counts, and show up to eight recent sources with their links. Do not repeat an identical evidence summary: state it once, then preserve each later source as its own Source Focus and link. Render Decision Would Change If inside an HTML <details> block with a concise <summary>. Use recorded perspective analysis when no explicit trade-off list exists, and use Judge synthesis as Why when conclusion rationale is absent. Reasoning Trace must describe observable Question → hypothesis → evidence → perspective → conflict → judge → conclusion artifacts, never chain-of-thought. Keep Conclusion under about 150 words and limit it to recommendation, why, and change conditions. Render caveats as uncertainty, impact, and needed evidence; use Unknown when absent. Do not invent, infer, or change any claim, source, URL, recommendation, statistic, confidence, or condition. Do not include raw JSON, a code fence, or commentary about this instruction.",
            {"canonical_session": exported_session},
        )
