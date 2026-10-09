"""
OpenAI-Compatible Provider Implementation (Section 4.6).

Connects to any OpenAI-compatible endpoint (OpenAI, OpenRouter, vLLM, Groq, Together, etc.).
Supports streaming token generation, vector embeddings, and readiness probes.
"""
from __future__ import annotations

import json
from typing import AsyncIterator, Any
import httpx

from backend.app.core.settings import settings
from backend.app.core.exceptions import AppError
from backend.app.services.providers.base import BaseLLMProvider, handle_provider_error


class OpenAICompatProvider(BaseLLMProvider):
    """Provider for OpenAI-compatible HTTP APIs."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        embed_model: str | None = None,
        timeout_seconds: int | None = None,
    ):
        self.base_url = (base_url or settings.OPENAI_COMPAT_BASE_URL).rstrip("/")
        self.api_key = api_key or settings.OPENAI_COMPAT_API_KEY
        self.model = model or settings.OPENAI_COMPAT_MODEL
        self.embed_model = embed_model or settings.EMBEDDING_MODEL
        self.timeout = float(timeout_seconds or settings.LLM_TIMEOUT_SECONDS)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _validate_config(self) -> None:
        if not self.base_url:
            raise AppError(
                code="MODEL_UNAVAILABLE",
                message="OpenAI-compatible base URL is not configured. Set OPENAI_COMPAT_BASE_URL.",
                status=503,
            )
        if not self.api_key:
            raise AppError(
                code="MISSING_API_KEY",
                message="OpenAI-compatible API key is missing. Set OPENAI_COMPAT_API_KEY.",
                status=503,
            )

    async def chat(
        self,
        messages: list[dict[str, Any]],
        stream: bool = True
    ) -> AsyncIterator[str]:
        """Stream chat completion tokens or yield complete response."""
        self._validate_config()
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if stream:
                    async with client.stream("POST", url, headers=self._headers(), json=payload) as response:
                        response.raise_for_status()
                        async for raw_line in response.aiter_lines():
                            line = raw_line.strip()
                            if not line or not line.startswith("data:"):
                                continue
                            data_str = line[5:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                            except json.JSONDecodeError:
                                continue

                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {}).get("content", "")
                                if delta:
                                    yield delta
                else:
                    response = await client.post(url, headers=self._headers(), json=payload)
                    response.raise_for_status()
                    data = response.json()
                    choices = data.get("choices", [])
                    if choices:
                        yield choices[0].get("message", {}).get("content", "")

        except Exception as exc:
            handle_provider_error(exc, "OpenAI-compatible")

    async def embed(self, text: str) -> list[float]:
        """Generate embedding vector using /embeddings endpoint."""
        self._validate_config()
        url = f"{self.base_url}/embeddings"
        payload = {
            "model": self.embed_model,
            "input": text,
        }

        try:
            async with httpx.AsyncClient(timeout=min(self.timeout, 30.0)) as client:
                response = await client.post(url, headers=self._headers(), json=payload)
                response.raise_for_status()
                data = response.json()
                items = data.get("data", [])
                if items and len(items) > 0:
                    return items[0].get("embedding", [])
                return []
        except Exception as exc:
            handle_provider_error(exc, "OpenAI-compatible Embedding")
            return []

    async def is_available(self) -> bool:
        """Check if base URL and credentials respond."""
        if not self.base_url or not self.api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/models", headers=self._headers())
                return resp.status_code == 200
        except Exception:
            return False
