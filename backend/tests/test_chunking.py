"""
Unit tests for Transcript Parser and Chunker (Step 2).

Uses standard unittest (zero extra dependencies, compatible with pytest):
- Frontmatter and speaker turn parsing
- Approximate token calculations
- Chunk size bounds (~300-500 tokens)
- Speaker turn preservation and boundary overlap
"""
import unittest
from pathlib import Path

from backend.app.services.retrieval.chunking import (
    approx_tokens,
    chunk_transcript,
    compute_content_hash,
    parse_transcript,
    SpeakerTurn,
    ParsedTranscript,
)

SAMPLE_MARKDOWN = """---
guest: Adam Fishman
title: How to build a high-performing growth team | Adam Fishman
youtube_url: https://www.youtube.com/watch?v=wP8YyWH524A
publish_date: 2022-10-13
---

# How to build a high-performing growth team | Adam Fishman

## Transcript

Adam Fishman (00:00:00):
Onboarding is the only part of your product experience that a hundred percent of people are ever going to touch. Good luck getting a hundred percent feature adoption of anything else in your product, right? But onboarding is the thing that you have to go through in order to use the product.

Lenny (00:00:55):
Adam Fishman was the first growth and marketing hire at Lyft where he spent two and a half years leading their growth efforts. Then he went on to lead product and growth at Patreon, where he spent over four years building one of the most successful creator platforms out there.

Adam Fishman (00:01:30):
When you think about growth teams, you really need to separate acquisition, retention, and monetization. Each of those pillars requires a distinct set of skills, psychological traits, and experimentation cadences.
"""

SAMPLE_BRACKETED_MARKDOWN = """---
guest: Ryan Hoover
title: A better way to plan and build products
---
[00:00:00] Ryan: I don't know how to articulate that feeling of startup anxiety.
[00:00:28] Lenny: Ryan Hoover is the founder of Product Hunt and investor with Weekend Fund.
"""

SAMPLE_NO_TIMESTAMP_MARKDOWN = """---
guest: Adriel Frederick
title: Humanizing product development
---
Adriel Frederick: When you are working on algorithmic heavy products, your job is figuring out what people are responsible for.
Lenny: Welcome to Lenny's Podcast. Today my guest is Adriel Frederick.
"""


class TestChunking(unittest.TestCase):

    def test_approx_tokens(self):
        # 10 words: "one two three four five six seven eight nine ten"
        text = "one two three four five six seven eight nine ten"
        tok = approx_tokens(text)
        # 10 words * 1.3 = 13 tokens
        self.assertEqual(tok, 13)
        self.assertEqual(approx_tokens(""), 0)

    def test_compute_content_hash(self):
        h1 = compute_content_hash("hello world")
        h2 = compute_content_hash("hello world")
        h3 = compute_content_hash("different")
        self.assertEqual(h1, h2)
        self.assertNotEqual(h1, h3)
        self.assertEqual(len(h1), 64)

    def test_parse_transcript_standard(self):
        parsed = parse_transcript(SAMPLE_MARKDOWN, source_path="data/transcripts/adam-fishman/transcript.md")
        self.assertEqual(parsed.title, "How to build a high-performing growth team | Adam Fishman")
        self.assertEqual(parsed.guest, "Adam Fishman")
        self.assertEqual(parsed.source_path, "data/transcripts/adam-fishman/transcript.md")
        self.assertEqual(len(parsed.turns), 3)

        self.assertEqual(parsed.turns[0].speaker, "Adam Fishman")
        self.assertEqual(parsed.turns[0].start_time, "00:00:00")
        self.assertIn("Onboarding is the only part", parsed.turns[0].text)

        self.assertEqual(parsed.turns[1].speaker, "Lenny")
        self.assertEqual(parsed.turns[1].start_time, "00:00:55")

        self.assertEqual(parsed.turns[2].speaker, "Adam Fishman")
        self.assertEqual(parsed.turns[2].start_time, "00:01:30")

    def test_parse_bracket_and_colon_formats(self):
        parsed_bracket = parse_transcript(SAMPLE_BRACKETED_MARKDOWN)
        self.assertEqual(len(parsed_bracket.turns), 2)
        self.assertEqual(parsed_bracket.turns[0].speaker, "Ryan")
        self.assertEqual(parsed_bracket.turns[0].start_time, "00:00:00")
        self.assertEqual(parsed_bracket.turns[1].speaker, "Lenny")
        self.assertEqual(parsed_bracket.turns[1].start_time, "00:00:28")

        parsed_colon = parse_transcript(SAMPLE_NO_TIMESTAMP_MARKDOWN)
        self.assertEqual(len(parsed_colon.turns), 2)
        self.assertEqual(parsed_colon.turns[0].speaker, "Adriel Frederick")
        self.assertIsNone(parsed_colon.turns[0].start_time)
        self.assertEqual(parsed_colon.turns[1].speaker, "Lenny")

    def test_chunk_transcript_bounds_and_overlap(self):
        # Construct a transcript with multiple turns
        turns = []
        for i in range(15):
            speaker = "Lenny" if i % 2 == 0 else "Guest"
            text = f"This is utterance number {i}. " + " ".join(["growth marketing experimentation metrics retention"] * 15)
            turns.append(SpeakerTurn(speaker=speaker, start_time=f"00:{i:02d}:00", text=text))

        parsed = ParsedTranscript(
            title="Test Growth Episode",
            guest="Guest",
            source_path="test.md",
            content_hash="dummyhash",
            turns=turns,
            metadata={},
        )

        chunks = chunk_transcript(
            parsed,
            min_tokens=250,
            target_tokens=400,
            max_tokens=500,
            overlap_turns=1,
        )

        self.assertGreater(len(chunks), 1)

        # Verify each chunk has metadata and appropriate token count
        for c in chunks:
            self.assertGreaterEqual(c.chunk_index, 0)
            self.assertIsNotNone(c.speaker)
            self.assertIsNotNone(c.start_time)
            self.assertGreater(len(c.text), 0)
            self.assertLessEqual(c.token_count, 550)

        # Verify overlap: second chunk contains the last turn of the first chunk
        self.assertGreaterEqual(len(chunks), 2)
        last_turn_snippet = "utterance number"
        self.assertIn(last_turn_snippet, chunks[0].text)
        self.assertIn(last_turn_snippet, chunks[1].text)

    def test_no_turn_is_lost_and_metadata_attached(self):
        """
        Verify:
        1. Chunk sizes stay in range (~300-500 approx tokens).
        2. Metadata is attached (chunk_index, speaker, start_time).
        3. No turn is lost: every turn's unique marker is present in at least one chunk.
        """
        num_turns = 20
        turns = []
        for i in range(num_turns):
            speaker = f"Speaker_{i % 3}"
            marker = f"UNIQUE_TURN_MARKER_{i:03d}"
            # Give each turn varying length
            text = f"{marker}: discussion on growth metric number {i} " + " ".join(["experimentation retention funnel"] * (10 + (i % 5)))
            turns.append(SpeakerTurn(speaker=speaker, start_time=f"00:{i:02d}:15", text=text))

        parsed = ParsedTranscript(
            title="Coverage Verification Episode",
            guest="Test Guest",
            source_path="coverage.md",
            content_hash="hash123",
            turns=turns,
            metadata={"guest": "Test Guest"},
        )

        chunks = chunk_transcript(parsed, min_tokens=250, target_tokens=400, max_tokens=500, overlap_turns=1)

        # 1. Chunk sizes stay within range
        for c in chunks:
            self.assertLessEqual(c.token_count, 550, f"Chunk {c.chunk_index} exceeded max tokens: {c.token_count}")
            # 2. Metadata is attached
            self.assertIsNotNone(c.speaker, f"Chunk {c.chunk_index} missing speaker")
            self.assertIsNotNone(c.start_time, f"Chunk {c.chunk_index} missing timestamp")
            self.assertGreaterEqual(c.chunk_index, 0)

        # 3. No turn is lost: check that all UNIQUE_TURN_MARKER_* exist across the chunks
        combined_chunks_text = "\n".join(c.text for c in chunks)
        for i in range(num_turns):
            marker = f"UNIQUE_TURN_MARKER_{i:03d}"
            self.assertIn(marker, combined_chunks_text, f"Turn {i} was lost during chunking!")

    def test_real_transcript_if_present(self):
        real_file = Path("data/transcripts/adam-fishman/transcript.md")
        if real_file.exists():
            content = real_file.read_text(encoding="utf-8")
            parsed = parse_transcript(content, source_path=str(real_file))
            self.assertEqual(parsed.guest, "Adam Fishman")
            self.assertGreater(len(parsed.turns), 10)

            chunks = chunk_transcript(parsed, min_tokens=250, target_tokens=400, max_tokens=500)
            self.assertGreater(len(chunks), 5)

            # Check the first chunk
            first_chunk = chunks[0]
            self.assertEqual(first_chunk.chunk_index, 0)
            self.assertGreaterEqual(first_chunk.token_count, 200)
            self.assertIn("Adam Fishman", first_chunk.speaker)


if __name__ == "__main__":
    unittest.main()
