import json
import os
from typing import Any, Protocol

import httpx
from dotenv import load_dotenv


load_dotenv()


class ReasoningProviderError(RuntimeError):
    """Raised when a real reasoning provider cannot complete a request."""


class LanguageModel(Protocol):
    def generate_json(self, instruction: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class ConfiguredReasoningClient:
    """Keep provider-specific HTTP outside the Orchestrator and its agents."""

    def __init__(self, api_key: str | None = None, model: str | None = None, provider: str | None = None) -> None:
        self.provider = (provider or os.getenv("AI_PROVIDER", "openai")).lower()
        if self.provider not in {"openai", "aimlapi"}:
            raise ReasoningProviderError("AI_PROVIDER must be either 'openai' or 'aimlapi'.")
        key_name = "AIMLAPI_API_KEY" if self.provider == "aimlapi" else "OPENAI_API_KEY"
        model_name = "AIMLAPI_MODEL" if self.provider == "aimlapi" else "OPENAI_MODEL"
        default_model = "gpt-4o" if self.provider == "aimlapi" else "gpt-4.1-mini"
        self.api_key = api_key if api_key is not None else os.getenv(key_name)
        self.model = model or os.getenv(model_name, default_model)

    def generate_json(self, instruction: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            key_name = "AIMLAPI_API_KEY" if self.provider == "aimlapi" else "OPENAI_API_KEY"
            raise ReasoningProviderError(f"{key_name} is not configured.")

        if self.provider == "aimlapi":
            return self._generate_aimlapi_json(instruction, payload)
        return self._generate_openai_json(instruction, payload)

    def _generate_openai_json(self, instruction: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = {
            "model": self.model,
            "instructions": instruction,
            "input": json.dumps(payload),
            "text": {"format": {"type": "json_object"}},
        }
        try:
            response = httpx.post(
                "https://api.openai.com/v1/responses",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=body,
                timeout=60.0,
            )
            response.raise_for_status()
            response_body = self._read_response_json(response, "OpenAI")
        except httpx.HTTPError as error:
            raise ReasoningProviderError(f"OpenAI request failed: {error}") from error

        return self._parse_json_output(response_body.get("output_text"), "OpenAI")

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
                timeout=60.0,
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
