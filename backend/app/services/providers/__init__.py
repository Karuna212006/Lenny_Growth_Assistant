"""
LLM Provider package.

Exposes provider implementations and a factory method to retrieve the active provider.
"""
from backend.app.core.settings import settings
from backend.app.services.providers.base import BaseLLMProvider
from backend.app.services.providers.ollama import OllamaProvider
from backend.app.services.providers.openai_compat import OpenAICompatProvider


def get_provider(provider_type: str | None = None) -> BaseLLMProvider:
    """
    Factory function returning an instance of the configured or requested provider.

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


__all__ = [
    "BaseLLMProvider",
    "OllamaProvider",
    "OpenAICompatProvider",
    "get_provider",
]
