"""
Unit tests for Artifact Generation and HTML Security Sanitization (Phase 8 / Section 4.7).

Verifies:
- Dangerous script execution is neutralized (<script>, inline event handlers, javascript: URLs)
- CSP meta tag is injected
- Markdown and HTML generation formats
- Blocked threats are reported
"""
import unittest

from backend.app.services.artifacts.sanitizer import sanitize_html
from backend.app.services.artifacts.generator import generate_artifact_content
from backend.app.services.providers.base import BaseLLMProvider


class MockArtifactProvider(BaseLLMProvider):
    """Mock LLM Provider for artifact tests."""

    async def chat(self, messages, stream=True):
        # Emits a component with an attempted malicious script injection to verify sanitizer
        yield "<!DOCTYPE html><html><head><title>Metrics Dashboard</title></head><body>"
        yield "<h1>SaaS Metrics</h1>"
        yield "<script>alert('pwned');</script>"
        yield "<img src='data:image/png;base64,123' onerror='alert(1)'>"
        yield "<a href='javascript:evil()'>Click me</a>"
        yield "<p>Clean paragraph</p></body></html>"

    async def embed(self, text: str):
        return [0.1] * 768

    async def is_available(self):
        return True


class TestArtifactSecurity(unittest.IsolatedAsyncioTestCase):

    def test_sanitizer_removes_scripts_and_handlers(self):
        """Verify that script tags, onerror, and javascript: links are stripped."""
        dirty_html = (
            "<div>"
            "<script>evil();</script>"
            "<img src='test.png' onerror='alert(document.cookie)'>"
            "<a href='javascript:steal()'>Link</a>"
            "</div>"
        )
        res = sanitize_html(dirty_html)

        self.assertTrue(res.has_threats)
        self.assertNotIn("<script>", res.clean_content)
        self.assertNotIn("evil();", res.clean_content)
        self.assertNotIn("onerror", res.clean_content)
        self.assertNotIn("javascript:steal()", res.clean_content)

        # Check threat report
        self.assertIn("<script> tag execution", res.blocked_items)
        self.assertIn("Inline DOM event handler (e.g. onerror/onload)", res.blocked_items)
        self.assertIn("javascript: pseudo-protocol URL", res.blocked_items)

        # Check CSP injection
        self.assertIn("Content-Security-Policy", res.clean_content)

    async def test_generate_artifact_content(self):
        """Verify artifact generator strips threats and extracts title."""
        provider = MockArtifactProvider()
        title, clean_html, blocked = await generate_artifact_content(
            "Create dashboard",
            "html",
            provider,
        )

        self.assertEqual(title, "Metrics Dashboard")
        self.assertNotIn("<script>", clean_html)
        self.assertNotIn("onerror", clean_html)
        self.assertIn("Content-Security-Policy", clean_html)
        self.assertIn("<script> tag execution", blocked)


if __name__ == "__main__":
    unittest.main()
