"""
Ollama Provider Implementation (Section 4.6).

Connects to a local or Docker-hosted Ollama instance.
Supports streaming token generation, vector embeddings via nomic-embed-text,
and availability health checks.
"""
from __future__ import annotations

import json
from typing import AsyncIterator, Any, Literal
import httpx

from backend.app.core.settings import settings
from backend.app.services.providers.base import (
    BaseLLMProvider,
    BaseEmbedder,
    handle_provider_error,
)


class OllamaProvider(BaseLLMProvider):
    """Provider for local Ollama server running models like Qwen 2.5 and Nomic Embed."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        embed_model: str | None = None,
        timeout_seconds: int | None = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.embed_model = embed_model or settings.EMBEDDING_MODEL
        self.timeout = float(timeout_seconds or settings.LLM_TIMEOUT_SECONDS)

    async def chat(
        self,
        messages: list[dict[str, Any]],
        stream: bool = True
    ) -> AsyncIterator[str]:
        """Stream tokens or yield completed response from Ollama /api/chat."""
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if stream:
                    async with client.stream("POST", url, json=payload) as response:
                        response.raise_for_status()
                        async for raw_line in response.aiter_lines():
                            line = raw_line.strip()
                            if not line:
                                continue
                            try:
                                data = json.loads(line)
                            except json.JSONDecodeError:
                                continue

                            delta = data.get("message", {}).get("content", "")
                            if delta:
                                yield delta
                            if data.get("done", False):
                                break
                else:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    yield data.get("message", {}).get("content", "")

        except Exception as exc:
            handle_provider_error(exc, "Ollama")

    async def embed(self, text: str) -> list[float]:
        """Generate vector embedding using Ollama /api/embed or legacy /api/embeddings."""
        try:
            async with httpx.AsyncClient(timeout=min(self.timeout, 30.0)) as client:
                # 1. Try modern /api/embed endpoint
                embed_url = f"{self.base_url}/api/embed"
                payload = {
                    "model": self.embed_model,
                    "input": text,
                }
                response = await client.post(embed_url, json=payload)

                if response.status_code == 200:
                    data = response.json()
                    embeddings = data.get("embeddings", [])
                    if embeddings and len(embeddings) > 0:
                        return embeddings[0]

                # 2. Fall back to legacy /api/embeddings endpoint
                legacy_url = f"{self.base_url}/api/embeddings"
                legacy_payload = {
                    "model": self.embed_model,
                    "prompt": text,
                }
                legacy_resp = await client.post(legacy_url, json=legacy_payload)
                legacy_resp.raise_for_status()
                return legacy_resp.json().get("embedding", [])

        except Exception as exc:
            handle_provider_error(exc, "Ollama Embedding")
            return []

    async def is_available(self) -> bool:
        """Check if Ollama server is responding and model is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Check version / tags endpoint
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code != 200:
                    return False
                # Optionally check if model is loaded/pulled
                models = resp.json().get("models", [])
                tag_names = [m.get("name", "") for m in models]
                # Return True if server responds; check model name if tags are present
                if not tag_names:
                    return True
                # Match full model name or base name before tag
                model_base = self.model.split(":")[0]
                return any(self.model in name or model_base in name for name in tag_names)
        except Exception:
            return False


class OllamaEmbedder(BaseEmbedder):
    """
    Dedicated embedder for Ollama (LOCKED 4.6).
    Uses nomic-embed-text (768 dimensions), applies document/query task prefixes,
    and batches requests with generous load timeout.
    """

    def __init__(
        self,
        base_url: str | None = None,
        embed_model: str | None = None,
        timeout_seconds: float = 120.0,
        batch_size: int = 32,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.embed_model = embed_model or settings.EMBEDDING_MODEL
        self.timeout = timeout_seconds
        self.batch_size = batch_size

    async def embed(
        self,
        texts: list[str],
        kind: Literal["document", "query"] = "document",
    ) -> list[list[float]]:
        if not texts:
            return []

        prefix = "search_document: " if kind == "document" else "search_query: "
        prefixed_texts = [
            f"{prefix}{t}" if not t.startswith(("search_document: ", "search_query: ")) else t
            for t in texts
        ]

        all_embeddings: list[list[float]] = []
        embed_url = f"{self.base_url}/api/embed"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for i in range(0, len(prefixed_texts), self.batch_size):
                    batch = prefixed_texts[i : i + self.batch_size]
                    payload = {
                        "model": self.embed_model,
                        "input": batch,
                    }
                    response = await client.post(embed_url, json=payload)
                    if response.status_code == 200:
                        data = response.json()
                        batch_embeds = data.get("embeddings", [])
                        all_embeddings.extend(batch_embeds)
                    else:
                        # Fallback to single-item legacy endpoint if batch /api/embed fails
                        for text_item in batch:
                            legacy_resp = await client.post(
                                f"{self.base_url}/api/embeddings",
                                json={"model": self.embed_model, "prompt": text_item},
                            )
                            legacy_resp.raise_for_status()
                            all_embeddings.append(legacy_resp.json().get("embedding", []))

            return all_embeddings

        except Exception as exc:
            handle_provider_error(exc, "Ollama Embedder")
            return []

    async def is_available(self) -> bool:
        """Check if Ollama server responds and nomic-embed-text is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code != 200:
                    return False
                models = resp.json().get("models", [])
                tag_names = [m.get("name", "") for m in models]
                if not tag_names:
                    return True
                model_base = self.embed_model.split(":")[0]
                return any(self.embed_model in name or model_base in name for name in tag_names)
        except Exception:
            return False

