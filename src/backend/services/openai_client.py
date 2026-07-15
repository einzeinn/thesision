import json
import os
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

    def generate_json(self, instruction: str, payload: dict[str, Any], *, tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        if not self.api_key:
            key_name = "AIMLAPI_API_KEY" if self.provider == "aimlapi" else "OPENAI_API_KEY"
            raise ReasoningProviderError(f"{key_name} is not configured.")

        if self.provider == "aimlapi":
            if tools:
                raise ReasoningProviderError("Evidence grounding requires OpenAI hosted web search; AI/ML API search-tool compatibility is not verified.")
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
            response = httpx.post(
                "https://api.openai.com/v1/responses",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=body,
                timeout=float(os.getenv("PROVIDER_TIMEOUT_SECONDS", "60")),
            )
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
            response = httpx.post(
                "https://api.aimlapi.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=body,
                timeout=float(os.getenv("PROVIDER_TIMEOUT_SECONDS", "60")),
            )
            response.raise_for_status()
            response_body = self._read_response_json(response, "AI/ML API")
        except httpx.HTTPError as error:
            raise ReasoningProviderError(f"AI/ML API request failed: {error}") from error

        choices = response_body.get("choices", [])
        output_text = choices[0].get("message", {}).get("content") if choices else None
        return self._parse_json_output(output_text, "AI/ML API")

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
