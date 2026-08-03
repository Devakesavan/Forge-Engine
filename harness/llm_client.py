"""Minimal OpenAI-compatible chat-completions client."""

from __future__ import annotations

import requests


class LLMResponseError(requests.RequestException):
    """Raised when the API returns JSON that is not a chat completion."""


def _format_api_error(payload: dict) -> str:
    error = payload.get("error")
    if isinstance(error, dict):
        message = error.get("message") or error.get("code") or error
        return str(message)
    if error:
        return str(error)
    return str(payload)


class LocalLLMClient:
    """Chat-completions client for OpenRouter or local OpenAI-compatible servers."""

    def __init__(self, base_url: str, model: str, api_key: str = "not-needed", max_tokens: int | None = None):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.max_tokens = max_tokens

    def chat(self, messages, tools, temperature: float = 0.2) -> dict:
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": temperature,
        }
        if self.max_tokens:
            payload["max_tokens"] = self.max_tokens
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=300,
        )
        try:
            payload = response.json()
        except ValueError as exc:
            response.raise_for_status()
            raise LLMResponseError(f"API returned non-JSON response: {exc}") from exc

        if not response.ok:
            raise LLMResponseError(f"HTTP {response.status_code}: {_format_api_error(payload)}")
        if "error" in payload:
            raise LLMResponseError(_format_api_error(payload))
        if not payload.get("choices"):
            raise LLMResponseError(f"API response missing choices: {payload}")
        return payload
