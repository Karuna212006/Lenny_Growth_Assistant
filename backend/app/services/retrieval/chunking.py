"""
Transcript Parser and Chunker (LOCKED Step 2).

Pure functions for parsing Lenny's Podcast transcripts and chunking them into
~300-500 approximate token blocks with speaker preservation and overlap.
No database or model dependencies.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any
import yaml


@dataclass
class SpeakerTurn:
    """A single dialogue turn spoken by one person."""
    speaker: str
    start_time: str | None
    text: str


@dataclass
class ParsedTranscript:
    """Parsed transcript metadata and dialogue turns."""
    title: str
    guest: str | None
    source_path: str
    content_hash: str
    turns: list[SpeakerTurn]
    metadata: dict[str, Any]


@dataclass
class ChunkData:
    """A chunk ready for embedding and storage in pgvector."""
    chunk_index: int
    text: str
    speaker: str | None
    start_time: str | None
    token_count: int


def approx_tokens(text: str) -> int:
    """Approximate token count using word count * 1.3."""
    words = len(text.split())
    return max(1, int(words * 1.3)) if words > 0 else 0


# Regex patterns for the 3 variations found in the transcript corpus:
# 1. Standard: "Adam Fishman (00:00:00): text" or "Lenny (01:19): text"
RE_SPEAKER_PAREN_TIME = re.compile(
    r"^([A-Za-z0-9\s\.\'\-]+?)\s*\((?:(\d{1,2}:\d{2}:\d{2})|(\d{1,2}:\d{2}))\):\s*(.*)$"
)

# 2. Bracketed: "[00:00:00] Ryan: text"
RE_BRACKET_TIME_SPEAKER = re.compile(
    r"^\[(?:(\d{1,2}:\d{2}:\d{2})|(\d{1,2}:\d{2}))\]\s*([A-Za-z0-9\s\.\'\-]+?):\s*(.*)$"
)

# 3. Simple: "Adriel Frederick: text" (no timestamp)
RE_SPEAKER_COLON = re.compile(
    r"^([A-Za-z0-9\s\.\'\-]+?):\s*(.*)$"
)


def compute_content_hash(text: str) -> str:
    """Compute deterministic SHA-256 hash of the raw transcript content."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_transcript(content: str, source_path: str = "") -> ParsedTranscript:
    """
    Parse a transcript markdown file containing YAML frontmatter and speaker dialogue.

    Extracts:
    - metadata (title, guest, youtube_url, duration, etc.)
    - SHA256 content hash
    - speaker turns with speaker name and start timestamp
    """
    content_hash = compute_content_hash(content)
    frontmatter: dict[str, Any] = {}
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                loaded = yaml.safe_load(parts[1])
                if isinstance(loaded, dict):
                    frontmatter = loaded
            except Exception:
                frontmatter = {}
            body = parts[2]

    title = frontmatter.get("title") or ""
    guest = frontmatter.get("guest") or None

    # Fallback to H1 header if title not in frontmatter
    if not title:
        h1_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        if h1_match:
            title = h1_match.group(1).strip()
        else:
            title = "Untitled Episode"

    turns: list[SpeakerTurn] = []
    lines = body.splitlines()

    current_speaker: str | None = None
    current_time: str | None = None
    current_lines: list[str] = []

    def flush_turn():
        nonlocal current_speaker, current_time, current_lines
        if current_speaker is not None and current_lines:
            text = "\n".join(current_lines).strip()
            if text:
                turns.append(
                    SpeakerTurn(
                        speaker=current_speaker,
                        start_time=current_time,
                        text=text,
                    )
                )
        current_lines = []

    in_transcript_section = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            if current_lines:
                current_lines.append("")
            continue

        # Skip headers like "# Title" or "## Transcript"
        if line.startswith("#"):
            if "transcript" in line.lower():
                in_transcript_section = True
            continue

        # Pattern 1: Speaker (00:00:00): ...
        m1 = RE_SPEAKER_PAREN_TIME.match(line)
        if m1:
            flush_turn()
            current_speaker = m1.group(1).strip()
            current_time = m1.group(2) or m1.group(3)
            current_lines = [m1.group(4)]
            continue

        # Pattern 2: [00:00:00] Speaker: ...
        m2 = RE_BRACKET_TIME_SPEAKER.match(line)
        if m2:
            flush_turn()
            current_time = m2.group(1) or m2.group(2)
            current_speaker = m2.group(3).strip()
            current_lines = [m2.group(4)]
            continue

        # Pattern 3: Speaker: ... (ensure not a URL or metadata tag)
        if not in_transcript_section or ":" in line:
            m3 = RE_SPEAKER_COLON.match(line)
            if m3 and not line.startswith("http") and len(m3.group(1).split()) <= 4:
                # Valid speaker line
                flush_turn()
                current_speaker = m3.group(1).strip()
                current_time = None
                current_lines = [m3.group(2)]
                continue

        # Continuation line for the current speaker turn
        if current_speaker is not None:
            current_lines.append(line)
        else:
            # Preamble before first speaker label
            current_speaker = "Introduction"
            current_time = "00:00:00"
            current_lines = [line]

    flush_turn()

    return ParsedTranscript(
        title=title,
        guest=guest,
        source_path=source_path,
        content_hash=content_hash,
        turns=turns,
        metadata=frontmatter,
    )


def _split_long_turn(
    turn: SpeakerTurn,
    max_tokens: int = 450,
) -> list[SpeakerTurn]:
    """
    Split a single speaker turn that exceeds max_tokens into smaller paragraphs
    or sentences while retaining speaker and timestamp.
    """
    paragraphs = [p.strip() for p in turn.text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [turn.text]

    split_turns: list[SpeakerTurn] = []
    accumulated: list[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = approx_tokens(para)

        # If a single paragraph is too large, split by sentences
        if para_tokens > max_tokens:
            if accumulated:
                split_turns.append(
                    SpeakerTurn(
                        speaker=turn.speaker,
                        start_time=turn.start_time,
                        text=" ".join(accumulated),
                    )
                )
                accumulated = []
                current_tokens = 0

            # Sentence split
            sentences = re.split(r"(?<=[.!?])\s+", para)
            sent_accum: list[str] = []
            sent_tokens = 0
            for sent in sentences:
                st = approx_tokens(sent)
                if sent_tokens + st > max_tokens and sent_accum:
                    split_turns.append(
                        SpeakerTurn(
                            speaker=turn.speaker,
                            start_time=turn.start_time,
                            text=" ".join(sent_accum),
                        )
                    )
                    sent_accum = [sent]
                    sent_tokens = st
                else:
                    sent_accum.append(sent)
                    sent_tokens += st
            if sent_accum:
                split_turns.append(
                    SpeakerTurn(
                        speaker=turn.speaker,
                        start_time=turn.start_time,
                        text=" ".join(sent_accum),
                    )
                )
            continue

        if current_tokens + para_tokens > max_tokens and accumulated:
            split_turns.append(
                SpeakerTurn(
                    speaker=turn.speaker,
                    start_time=turn.start_time,
                    text=" ".join(accumulated),
                )
            )
            accumulated = [para]
            current_tokens = para_tokens
        else:
            accumulated.append(para)
            current_tokens += para_tokens

    if accumulated:
        split_turns.append(
            SpeakerTurn(
                speaker=turn.speaker,
                start_time=turn.start_time,
                text=" ".join(accumulated),
            )
        )

    return split_turns


def _format_turn_text(turn: SpeakerTurn) -> str:
    """Format turn with speaker and timestamp header for readable chunking."""
    ts = f" ({turn.start_time})" if turn.start_time else ""
    return f"{turn.speaker}{ts}: {turn.text}"


def chunk_transcript(
    transcript: ParsedTranscript,
    min_tokens: int = 250,
    target_tokens: int = 400,
    max_tokens: int = 500,
    overlap_turns: int = 1,
) -> list[ChunkData]:
    """
    Chunk dialogue turns into ~300-500 approximate token blocks.

    - Keeps speaker turns whole when possible.
    - Splits extra-long turns by paragraph/sentence.
    - Includes small overlap (1 previous turn) across chunk boundaries.
    - Formats chunk text with speaker and timestamp attribution for vector search.
    """
    if not transcript.turns:
        return []

    # 1. Normalize turns: split any individual turns that exceed max_tokens
    normalized_turns: list[SpeakerTurn] = []
    for turn in transcript.turns:
        if approx_tokens(turn.text) > max_tokens:
            normalized_turns.extend(_split_long_turn(turn, max_tokens=max_tokens))
        else:
            normalized_turns.append(turn)

    chunks: list[ChunkData] = []
    current_turns: list[SpeakerTurn] = []
    current_tokens = 0
    chunk_index = 0

    idx = 0
    n = len(normalized_turns)

    while idx < n:
        turn = normalized_turns[idx]
        turn_text = _format_turn_text(turn)
        turn_tok = approx_tokens(turn_text)

        # If adding this turn would exceed max_tokens and we already have sufficient tokens
        if current_tokens + turn_tok > max_tokens and current_tokens >= min_tokens:
            # Emit current chunk
            chunk_body = "\n\n".join(_format_turn_text(t) for t in current_turns)
            speakers = list(dict.fromkeys(t.speaker for t in current_turns))
            speaker_label = ", ".join(speakers)
            first_time = next((t.start_time for t in current_turns if t.start_time), None)

            chunks.append(
                ChunkData(
                    chunk_index=chunk_index,
                    text=chunk_body,
                    speaker=speaker_label,
                    start_time=first_time,
                    token_count=current_tokens,
                )
            )
            chunk_index += 1

            # Prepare overlap for next chunk
            overlap_slice = current_turns[-overlap_turns:] if overlap_turns > 0 else []
            current_turns = list(overlap_slice)
            current_tokens = sum(approx_tokens(_format_turn_text(t)) for t in current_turns)

        current_turns.append(turn)
        current_tokens += turn_tok
        idx += 1

    # Emit final remaining chunk
    if current_turns:
        chunk_body = "\n\n".join(_format_turn_text(t) for t in current_turns)
        speakers = list(dict.fromkeys(t.speaker for t in current_turns))
        speaker_label = ", ".join(speakers)
        first_time = next((t.start_time for t in current_turns if t.start_time), None)

        chunks.append(
            ChunkData(
                chunk_index=chunk_index,
                text=chunk_body,
                speaker=speaker_label,
                start_time=first_time,
                token_count=current_tokens,
            )
        )

    return chunks
