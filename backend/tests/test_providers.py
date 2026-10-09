"""
Unit tests for Provider Interface (Section 4.6).

Uses Python's standard `unittest` library (works without extra dependencies,
and compatible with pytest).
"""
import unittest
from unittest.mock import AsyncMock, patch
import httpx

from backend.app.services.providers.base import BaseLLMProvider, handle_provider_error
from backend.app.services.providers.ollama import OllamaProvider
from backend.app.services.providers.openai_compat import OpenAICompatProvider
from backend.app.services.providers import get_provider
from backend.app.core.exceptions import AppError


class TestProviderInterface(unittest.IsolatedAsyncioTestCase):

    def test_base_provider_subclass_enforcement(self):
        """Verify that concrete implementations must implement chat, embed, and is_available."""
        class IncompleteProvider(BaseLLMProvider):
            pass

        with self.assertRaises(TypeError):
            IncompleteProvider()  # type: ignore

    def test_provider_factory(self):
        """Verify factory returns appropriate provider instance."""
        ollama = get_provider("ollama")
        self.assertIsInstance(ollama, OllamaProvider)

        openai = get_provider("openai_compatible")
        self.assertIsInstance(openai, OpenAICompatProvider)

    def test_error_mapping(self):
        """Verify low-level HTTP exceptions map to expected AppError codes."""
        with self.assertRaises(AppError) as ctx1:
            handle_provider_error(httpx.ConnectError("Connection refused"), "Ollama")
        self.assertEqual(ctx1.exception.code, "MODEL_UNAVAILABLE")
        self.assertEqual(ctx1.exception.status, 503)

        with self.assertRaises(AppError) as ctx2:
            handle_provider_error(httpx.TimeoutException("Read timed out"), "Ollama")
        self.assertEqual(ctx2.exception.code, "MODEL_TIMEOUT")
        self.assertEqual(ctx2.exception.status, 504)

    async def test_openai_compat_validation_without_keys(self):
        """Verify OpenAICompatProvider raises MISSING_API_KEY if key is missing."""
        provider = OpenAICompatProvider(base_url="http://localhost:8000/v1", api_key="")
        with self.assertRaises(AppError) as ctx:
            await provider.embed("sample text")
        self.assertEqual(ctx.exception.code, "MISSING_API_KEY")

    async def test_ollama_is_available_unreachable(self):
        """Verify is_available returns False when connection fails."""
        provider = OllamaProvider(base_url="http://invalid-ollama-url:11434")
        available = await provider.is_available()
        self.assertFalse(available)


if __name__ == "__main__":
    unittest.main()
