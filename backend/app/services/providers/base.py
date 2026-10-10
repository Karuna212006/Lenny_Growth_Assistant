"""
Base LLM Provider Interface (Section 4.6).

Every provider (Ollama, OpenAI-compatible, etc.) must implement this interface.
Ensures application logic is completely decoupled from any specific LLM provider or SDK.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator, Any, Literal
import httpx
from backend.app.core.exceptions import AppError


class BaseLLMProvider(ABC):
    """Abstract base class that all chat LLM providers must implement."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        stream: bool = True
    ) -> AsyncIterator[str]:
        """
        Send a conversation history to the model and stream text tokens.

        Args:
            messages: List of message dictionaries with 'role' ('system', 'user', 'assistant')
                      and 'content' string.
            stream: Whether to stream tokens incrementally (default True).

        Yields:
            Token text chunks as strings as they arrive from the provider.
        """
        ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate dense vector embedding for a text chunk (legacy single-text method)."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """
        Check if the provider endpoint and model are ready and accessible.

        Returns:
            True if healthy and reachable, False otherwise.
        """
        ...


class BaseEmbedder(ABC):
    """
    Abstract interface for dense embedding generation (LOCKED 4.6).
    Decoupled from chat providers so switching chat models never touches the index.
    """

    @abstractmethod
    async def embed(
        self,
        texts: list[str],
        kind: Literal["document", "query"] = "document",
    ) -> list[list[float]]:
        """
        Generate dense vector embeddings for a batch of texts.

        Applies task prefixes ('search_document: ' or 'search_query: ') required
        by nomic-embed-text to optimize retrieval quality.

        Args:
            texts: List of text strings to embed.
            kind: 'document' for chunks at ingestion, 'query' for user search queries.

        Returns:
            List of 768-dimensional float embedding vectors.
        """
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the embedding service and model are ready."""
        ...


def handle_provider_error(exc: Exception, provider_name: str) -> None:
    """Map low-level HTTP / network exceptions to standard AppErrors."""
    if isinstance(exc, (httpx.ConnectError, httpx.NetworkError)):
        raise AppError(
            code="MODEL_UNAVAILABLE",
            message=f"{provider_name} service is unreachable. Please verify that the provider is running.",
            status=503
        ) from exc
    if isinstance(exc, httpx.TimeoutException):
        raise AppError(
            code="MODEL_TIMEOUT",
            message=f"Request to {provider_name} timed out. Local inference may be overloaded.",
            status=504
        ) from exc
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        if status == 401 or status == 403:
            raise AppError(
                code="MISSING_API_KEY",
                message=f"Authentication failed for {provider_name}. Check API key configuration.",
                status=503
            ) from exc
        raise AppError(
            code="MODEL_UNAVAILABLE",
            message=f"{provider_name} returned HTTP {status}: {exc.response.text[:200]}",
            status=503
        ) from exc
    if isinstance(exc, AppError):
        raise exc
    raise AppError(
        code="MODEL_UNAVAILABLE",
        message=f"Unexpected error communicating with {provider_name}: {str(exc)}",
        status=500
    ) from exc
