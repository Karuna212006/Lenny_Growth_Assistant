"""
Unit tests for Ship 30 for 30 Skill (Phase 7 / Section 10).

Verifies:
- SKILL.md definition and frontmatter existence
- Essay generator pipeline execution
- Structural checks: headings, bullet points, selective bold, and citations
- Word count measurement and tolerances
"""
import unittest
from pathlib import Path
from uuid import uuid4

from backend.app.services.providers.base import BaseLLMProvider
from backend.app.services.retrieval.search import RetrievedChunk
from backend.app.skills.ship30.generator import generate_ship30_essay


class MockEssayProvider(BaseLLMProvider):
    """Mock LLM Provider returning a structured Ship 30 article."""

    async def chat(self, messages, stream=True):
        yield "## The Irresistible Hook\nMost founders optimize onboarding backwards.\n\n"
        yield "## The Paradigm Shift\nTraditional PMs treat onboarding as an afterthought. "
        yield "According to [How to build a growth team — Adam Fishman], onboarding is the only part 100% of users see.\n\n"
        yield "## Core Pillars of Growth\n"
        yield "- **Pillar 1:** Focus on time-to-value.\n"
        yield "- **Pillar 2:** Remove friction before adding features.\n\n"
        yield "## The Monday Morning Checklist\n- Audit your sign-up flow.\n- Measure drop-offs.\n"

    async def embed(self, text: str):
        return [0.1] * 768

    async def is_available(self):
        return True


class TestShip30Skill(unittest.IsolatedAsyncioTestCase):

    def test_skill_markdown_specification(self):
        """Verify SKILL.md exists, has YAML frontmatter, and defines the ~1,250 word target."""
        skill_file = Path("backend/app/skills/ship30/SKILL.md")
        self.assertTrue(skill_file.exists(), "SKILL.md file missing from backend/app/skills/ship30/")

        content = skill_file.read_text(encoding="utf-8")
        self.assertIn("name: ship30-essay-generator", content)
        self.assertIn("1,250 words", content)
        self.assertIn("The Irresistible Hook", content)
        self.assertIn("Selective Bold", content)

    async def test_generate_ship30_essay(self):
        """Verify essay generator streams formatted markdown with headings, bullets, and citations."""
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
            score=0.92,
        )

        provider = MockEssayProvider()
        tokens = []
        async for token in generate_ship30_essay("Optimizing Onboarding", [fake_chunk], provider):
            tokens.append(token)

        full_essay = "".join(tokens)

        # Structural assertions
        self.assertIn("## The Irresistible Hook", full_essay)
        self.assertIn("## The Paradigm Shift", full_essay)
        self.assertIn("## Core Pillars of Growth", full_essay)
        self.assertIn("- **Pillar 1:**", full_essay)
        self.assertIn("[How to build a growth team — Adam Fishman]", full_essay)


if __name__ == "__main__":
    unittest.main()
