import json
import os
from typing import Any, Protocol

import httpx


class ReasoningProviderError(RuntimeError):
    """Raised when a real reasoning provider cannot complete a request."""


class LanguageModel(Protocol):
    def generate_json(self, instruction: str, payload: dict[str, Any]) -> dict[str, Any]: ...


class OpenAIResponsesClient:
    """Small adapter that keeps provider-specific HTTP outside the agents."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    def generate_json(self, instruction: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise ReasoningProviderError("OPENAI_API_KEY is not configured.")

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
            response_body = response.json()
        except httpx.HTTPError as error:
            raise ReasoningProviderError(f"OpenAI request failed: {error}") from error

        output_text = response_body.get("output_text")
        if not output_text:
            raise ReasoningProviderError("OpenAI returned no structured reasoning output.")
        try:
            result = json.loads(output_text)
        except json.JSONDecodeError as error:
            raise ReasoningProviderError("OpenAI returned invalid JSON reasoning output.") from error
        if not isinstance(result, dict):
            raise ReasoningProviderError("OpenAI returned a reasoning output with the wrong shape.")
        return result
