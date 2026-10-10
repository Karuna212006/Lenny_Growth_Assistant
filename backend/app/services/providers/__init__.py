"""
LLM Provider package.

Exposes provider implementations and a factory method to retrieve the active provider.
"""
from backend.app.core.settings import settings
from backend.app.services.providers.base import BaseLLMProvider, BaseEmbedder
from backend.app.services.providers.ollama import OllamaProvider, OllamaEmbedder
from backend.app.services.providers.openai_compat import OpenAICompatProvider


def get_provider(provider_type: str | None = None) -> BaseLLMProvider:
    """
    Factory function returning an instance of the configured or requested chat provider.

    Args:
        provider_type: 'ollama' | 'openai_compatible' (defaults to settings.LLM_PROVIDER).
    """
    p_type = (provider_type or settings.LLM_PROVIDER).lower()
    if p_type == "ollama":
        return OllamaProvider()
    elif p_type in ("openai_compatible", "openai", "openai-compat"):
        return OpenAICompatProvider()
    else:
        # Default fallback to Ollama
        return OllamaProvider()


def get_embedder(embedder_type: str = "ollama") -> BaseEmbedder:
    """
    Factory function returning the dense vector embedder (LOCKED 4.6).
    Decoupled from get_provider() so the embedding index is immutable regardless
    of the active chat provider.
    """
    # By design, both local and cloud modes share the same local Ollama nomic-embed-text index
    return OllamaEmbedder()


__all__ = [
    "BaseLLMProvider",
    "BaseEmbedder",
    "OllamaProvider",
    "OllamaEmbedder",
    "OpenAICompatProvider",
    "get_provider",
    "get_embedder",
]

