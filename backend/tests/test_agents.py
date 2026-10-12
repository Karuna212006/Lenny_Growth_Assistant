"""
Unit tests for Agent Layer and Routing (Phase 6 / Section 4.4).

Verifies:
- Rule-based and fallback intent classification (qa | essay | artifact | out_of_scope)
- Follow-up query detection and rewriting
- Grounded QA pipeline with citation emission
- Immediate refusal on out-of-scope queries
"""
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from backend.app.agents.orchestrator import run_agent_pipeline
from backend.app.agents.prompts import OUT_OF_SCOPE_REFUSAL
from backend.app.agents.rewriter import is_follow_up, rewrite_query
from backend.app.agents.router import classify_intent, classify_intent_rules
from backend.app.services.providers.base import BaseLLMProvider
from backend.app.services.retrieval.search import RetrievedChunk


class MockProvider(BaseLLMProvider):
    """Mock LLM Provider for deterministic testing."""

    async def chat(self, messages, stream=True):
        # Yield dummy response
        yield "According to [How to build a growth team — Adam Fishman], onboarding is critical."

    async def embed(self, text: str):
        return [0.1] * 768

    async def is_available(self):
        return True


class TestAgentLayer(unittest.IsolatedAsyncioTestCase):

    def test_intent_classification_rules(self):
        """Verify rule-based heuristics classify requests deterministically."""
        # Essay
        self.assertEqual(classify_intent_rules("Write an essay about finding product-market fit"), "essay")
        self.assertEqual(classify_intent_rules("Draft a Ship 30 piece on growth loops"), "essay")

        # Artifact
        self.assertEqual(classify_intent_rules("Create an HTML component for user onboarding"), "artifact")
        self.assertEqual(classify_intent_rules("Generate a cheatsheet table in html/css"), "artifact")

        # Out of scope
        self.assertEqual(classify_intent_rules("How to bake a banana bread with walnuts?"), "out_of_scope")
        self.assertEqual(classify_intent_rules("What is the weather forecast today?"), "out_of_scope")

        # QA / Unmatched by rules
        self.assertIsNone(classify_intent_rules("How do I structure my first growth team?"))

    async def test_classify_intent_full(self):
        """Verify classify_intent falls back to QA when no rules match."""
        provider = MockProvider()
        intent = await classify_intent("How do I structure my first growth team?", provider=provider)
        self.assertEqual(intent, "qa")

        out_intent = await classify_intent("What is the best recipe for chocolate chip cookies?", provider=provider)
        self.assertEqual(out_intent, "out_of_scope")

    def test_follow_up_detection(self):
        """Verify pronoun and context follow-up detection."""
        self.assertTrue(is_follow_up("Why did he recommend that?"))
        self.assertTrue(is_follow_up("What about the second point?"))
        self.assertTrue(is_follow_up("tell me more"))
        self.assertTrue(is_follow_up("why?"))

        self.assertFalse(is_follow_up("What is cohort retention in SaaS products?"))

    async def test_rewrite_query(self):
        """Verify query rewriter resolves follow-up questions."""
        history = [
            {"role": "user", "content": "What did Brian Chesky say about founder mode?"},
            {"role": "assistant", "content": "He explained that founders should stay deeply involved in details."},
        ]

        # Without provider (rule fallback)
        rewritten_rule = await rewrite_query("Why did he say that?", history, provider=None)
        self.assertIn("Brian Chesky", rewritten_rule)

    async def test_orchestrator_out_of_scope(self):
        """Verify out-of-scope questions immediately refuse without search or hallucination."""
        provider = MockProvider()
        db_mock = AsyncMock()

        events = []
        async for item in run_agent_pipeline("Give me a recipe for banana bread", history=[], provider=provider, db=db_mock):
            events.append(item)

        event_names = [e["event"] for e in events]
        self.assertIn("status", event_names)
        self.assertIn("token", event_names)
        self.assertIn("done", event_names)

        # Check final done event
        done_event = next(e for e in events if e["event"] == "done")
        self.assertTrue(done_event["data"]["no_sources"])
        self.assertEqual(done_event["data"]["intent"], "out_of_scope")
        self.assertEqual(done_event["data"]["citations"], [])
        self.assertIn("not covered", done_event["data"]["full_text"])

    async def test_orchestrator_qa_flow(self):
        """Verify grounded QA retrieves sources, emits citations, and streams tokens."""
        provider = MockProvider()
        db_mock = AsyncMock()

        fake_chunk = RetrievedChunk(
            chunk_id=uuid4(),
            episode_id=uuid4(),
            episode_title="How to build a growth team",
            guest="Adam Fishman",
            source_path="episodes/adam-fishman/transcript.md",
            chunk_index=0,
            text="Onboarding is the only part of your product that 100% of users see.",
            speaker="Adam Fishman",
            start_time="00:00:00",
            score=0.88,
        )

        with patch("backend.app.agents.orchestrator.search_transcripts", return_value=[fake_chunk]):
            events = []
            async for item in run_agent_pipeline(
                "How important is onboarding?",
                history=[],
                provider=provider,
                db=db_mock,
            ):
                events.append(item)

        event_names = [e["event"] for e in events]
        self.assertIn("status", event_names)
        self.assertIn("citations", event_names)
        self.assertIn("token", event_names)
        self.assertIn("done", event_names)

        # Citations verification
        citations_event = next(e for e in events if e["event"] == "citations")
        citations = citations_event["data"]["citations"]
        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0]["title"], "How to build a growth team")
        self.assertEqual(citations[0]["guest"], "Adam Fishman")
        self.assertEqual(citations[0]["citation"], "[How to build a growth team — Adam Fishman]")

        # Done event verification
        done_event = next(e for e in events if e["event"] == "done")
        self.assertFalse(done_event["data"]["no_sources"])
        self.assertEqual(done_event["data"]["intent"], "qa")

    async def test_orchestrator_tool_calling_invoked(self):
        """Verify the agent tool-calling step invokes retrieve_transcripts tool and calls search service."""
        provider = MockProvider()
        db_mock = AsyncMock()

        fake_chunk = RetrievedChunk(
            chunk_id=uuid4(),
            episode_id=uuid4(),
            episode_title="Onboarding Frameworks",
            guest="Adam Fishman",
            source_path="episodes/adam-fishman/transcript.md",
            chunk_index=0,
            text="Onboarding is critical.",
            speaker="Adam Fishman",
            start_time="00:00:00",
            score=0.92,
        )

        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "retrieve_transcripts"
        mock_tool_block.input = {"query": "onboarding frameworks"}

        mock_response = MagicMock()
        mock_response.content = [mock_tool_block]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response

        with patch("anthropic.Anthropic", return_value=mock_client):
            with patch("backend.app.agents.orchestrator.search_transcripts", return_value=[fake_chunk]) as mock_search:
                events = []
                async for item in run_agent_pipeline(
                    "What did Adam Fishman say about onboarding?",
                    history=[],
                    provider=provider,
                    db=db_mock,
                ):
                    events.append(item)

                mock_client.messages.create.assert_called_once()
                mock_search.assert_called_with("onboarding frameworks", db=db_mock, top_k=None)
                self.assertTrue(any(e["event"] == "citations" for e in events))

    async def test_empty_retrieval_refuses_without_model_chat(self):
        """Verify that when retrieval is empty, assistant immediately refuses and provider.chat is never called."""
        class SpyProvider(BaseLLMProvider):
            def __init__(self):
                self.chat_called = False

            async def chat(self, messages, stream=True):
                self.chat_called = True
                yield "Should never be reached"

            async def embed(self, text: str):
                return [0.1] * 768

            async def is_available(self):
                return True

        provider = SpyProvider()
        db_mock = AsyncMock()

        with patch("backend.app.agents.orchestrator.classify_intent", return_value="qa"):
            with patch("backend.app.agents.orchestrator.search_transcripts", return_value=[]):
                events = []
                async for item in run_agent_pipeline(
                    "Can you tell me about hyper-dimensional wormhole physics?",
                    history=[],
                    provider=provider,
                    db=db_mock,
                ):
                    events.append(item)

                self.assertFalse(provider.chat_called, "provider.chat MUST NOT be called to answer when retrieval is empty")
                done_event = next(e for e in events if e["event"] == "done")
                self.assertTrue(done_event["data"]["no_sources"])
                self.assertIn("no relevant discussions were found", done_event["data"]["full_text"])


if __name__ == "__main__":
    unittest.main()

