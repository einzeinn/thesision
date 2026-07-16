import json
import os
import re
import time
from typing import Any, Protocol

import httpx
from dotenv import load_dotenv


load_dotenv()


class ReasoningProviderError(RuntimeError):
    """Raised when a real reasoning provider cannot complete a request."""


class LanguageModel(Protocol):
    def generate_json(self, instruction: str, payload: dict[str, Any], *, tools: list[dict[str, Any]] | None = None) -> dict[str, Any]: ...


class ConfiguredReasoningClient:
    """Keep provider-specific HTTP outside the Orchestrator and its agents."""

    def __init__(self, api_key: str | None = None, model: str | None = None, provider: str | None = None) -> None:
        self.provider = (provider or os.getenv("AI_PROVIDER", "openai")).lower()
        if self.provider not in {"openai", "aimlapi"}:
            raise ReasoningProviderError("AI_PROVIDER must be either 'openai' or 'aimlapi'.")
        key_name = "AIMLAPI_API_KEY" if self.provider == "aimlapi" else "OPENAI_API_KEY"
        model_name = "AIMLAPI_MODEL" if self.provider == "aimlapi" else "OPENAI_MODEL"
        default_model = "openai/gpt-5.6-luna" if self.provider == "aimlapi" else "gpt-4.1-mini"
        self.api_key = api_key if api_key is not None else os.getenv(key_name)
        self.model = model or os.getenv(model_name, default_model)
        self.evidence_model = os.getenv("AIMLAPI_EVIDENCE_MODEL", "perplexity/sonar")

    def _post_with_retry(self, url: str, body: dict[str, Any]) -> httpx.Response:
        """Retry only temporary provider failures; malformed requests fail at once."""
        attempts = max(1, min(3, int(os.getenv("PROVIDER_RETRY_ATTEMPTS", "3"))))
        last_error: httpx.HTTPError | None = None
        for attempt in range(attempts):
            try:
                response = httpx.post(
                    url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=body,
                    timeout=float(os.getenv("PROVIDER_TIMEOUT_SECONDS", "60")),
                )
            except httpx.HTTPError as error:
                last_error = error
                if attempt == attempts - 1:
                    raise
            else:
                status_code = getattr(response, "status_code", None)
                if status_code not in {429, 500, 502, 503, 504} or attempt == attempts - 1:
                    return response
            time.sleep(2**attempt)
        if last_error is not None:
            raise last_error
        raise ReasoningProviderError("Provider retry loop ended without a response.")

    def generate_json(self, instruction: str, payload: dict[str, Any], *, tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        if not self.api_key:
            key_name = "AIMLAPI_API_KEY" if self.provider == "aimlapi" else "OPENAI_API_KEY"
            raise ReasoningProviderError(f"{key_name} is not configured.")

        if self.provider == "aimlapi":
            if tools:
                return self._generate_aimlapi_grounded_evidence(instruction, payload)
            return self._generate_aimlapi_json(instruction, payload)
        return self._generate_openai_json(instruction, payload, tools=tools)

    def _generate_openai_json(self, instruction: str, payload: dict[str, Any], *, tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        body = {
            "model": self.model,
            "instructions": instruction,
            "input": json.dumps(payload),
            "text": {"format": {"type": "json_object"}},
        }
        if tools:
            body["tools"] = tools
        try:
            response = self._post_with_retry("https://api.openai.com/v1/responses", body)
            response.raise_for_status()
            response_body = self._read_response_json(response, "OpenAI")
        except httpx.HTTPError as error:
            raise ReasoningProviderError(f"OpenAI request failed: {error}") from error

        result = self._parse_json_output(response_body.get("output_text"), "OpenAI")
        return self._ground_evidence(result, response_body) if tools else result

    @staticmethod
    def _ground_evidence(result: dict[str, Any], response_body: dict[str, Any]) -> dict[str, Any]:
        citations: dict[str, str] = {}
        for output in response_body.get("output", []):
            if not isinstance(output, dict):
                continue
            for content in output.get("content", []):
                if not isinstance(content, dict):
                    continue
                for annotation in content.get("annotations", []):
                    if not isinstance(annotation, dict) or annotation.get("type") != "url_citation":
                        continue
                    url = annotation.get("url")
                    if isinstance(url, str) and url:
                        citations[url.rstrip("/")] = str(annotation.get("title") or url)

        grounded: list[dict[str, Any]] = []
        for item in result.get("evidence", []):
            if not isinstance(item, dict):
                continue
            url = item.get("url")
            if isinstance(url, str) and url.rstrip("/") in citations:
                item["url"] = url
                item["source_title"] = citations[url.rstrip("/")]
                grounded.append(item)
            else:
                grounded.append({
                    "claim": item.get("claim", "No verified source was found for this claim."),
                    "source_title": "No verified web source found",
                    "url": None,
                    "relevance": "unverified",
                    "quality": "unverified",
                })
        result["evidence"] = grounded
        return result

    def _generate_aimlapi_json(self, instruction: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": instruction},
                {"role": "user", "content": json.dumps(payload)},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        try:
            response = self._post_with_retry("https://api.aimlapi.com/v1/chat/completions", body)
            response.raise_for_status()
            response_body = self._read_response_json(response, "AI/ML API")
        except httpx.HTTPError as error:
            raise ReasoningProviderError(f"AI/ML API request failed: {error}") from error

        choices = response_body.get("choices", [])
        output_text = choices[0].get("message", {}).get("content") if choices else None
        return self._parse_json_output(output_text, "AI/ML API")

    def _generate_aimlapi_grounded_evidence(self, instruction: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = {
            "model": self.evidence_model,
            "messages": [
                {"role": "system", "content": instruction},
                {"role": "user", "content": json.dumps(payload)},
            ],
            "temperature": 0.2,
            "web_search_options": {"search_mode": "web"},
        }
        try:
            response = self._post_with_retry("https://api.aimlapi.com/v1/chat/completions", body)
            response.raise_for_status()
            response_body = self._read_response_json(response, "AI/ML API evidence model")
        except httpx.HTTPError as error:
            raise ReasoningProviderError(f"AI/ML API evidence request failed: {error}") from error

        choices = response_body.get("choices", [])
        output_text = choices[0].get("message", {}).get("content") if choices else None
        return self._ground_aimlapi_evidence(output_text, response_body)

    @staticmethod
    def _ground_aimlapi_evidence(output_text: Any, response_body: dict[str, Any]) -> dict[str, Any]:
        sources: dict[str, dict[str, str]] = {}
        for item in response_body.get("search_results", []):
            if isinstance(item, dict) and isinstance(item.get("url"), str):
                url = item["url"].rstrip("/")
                source_text = next(
                    (
                        value.strip()
                        for key in ("snippet", "description", "content", "text")
                        if isinstance((value := item.get(key)), str) and value.strip()
                    ),
                    "",
                )
                sources[url] = {
                    "title": str(item.get("title") or item["url"]),
                    "summary": re.sub(r"\[\d+(?:\]\[\d+)*\]", "", source_text).strip(),
                }
        for url in response_body.get("citations", []):
            if isinstance(url, str) and url:
                sources.setdefault(url.rstrip("/"), {"title": url, "summary": ""})

        summary = re.sub(r"\[\d+(?:\]\[\d+)*\]", "", output_text).strip() if isinstance(output_text, str) else ""
        if not summary or not sources:
            return {"evidence": [{
                "claim": "No verified web source was returned for this search.",
                "source_title": "No verified web source found",
                "url": None,
                "relevance": "unverified",
                "quality": "unverified",
            }]}

        return {"evidence": [
            {
                "claim": source["summary"] or summary,
                "source_title": source["title"],
                "url": url,
                "relevance": "grounded-search",
                "quality": "medium",
            }
            for url, source in list(sources.items())[:5]
        ]}

    @staticmethod
    def _read_response_json(response: httpx.Response, provider_name: str) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as error:
            body_preview = response.text[:200].strip() or "an empty response"
            raise ReasoningProviderError(f"{provider_name} returned a non-JSON response: {body_preview}") from error
        if not isinstance(payload, dict):
            raise ReasoningProviderError(f"{provider_name} returned a JSON response with the wrong shape.")
        return payload

    @staticmethod
    def _parse_json_output(output_text: Any, provider_name: str) -> dict[str, Any]:
        if not output_text:
            raise ReasoningProviderError(f"{provider_name} returned no structured reasoning output.")
        try:
            result = json.loads(output_text)
        except json.JSONDecodeError as error:
            raise ReasoningProviderError(f"{provider_name} returned invalid JSON reasoning output.") from error
        if not isinstance(result, dict):
            raise ReasoningProviderError(f"{provider_name} returned a reasoning output with the wrong shape.")
        return result
