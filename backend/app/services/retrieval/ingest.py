"""
Transcripts Ingestion Pipeline (Step 3).

Reads transcript markdown files, parses frontmatter and speaker turns,
computes deterministic SHA-256 hashes for incremental refresh,
batches chunks for embedding with OllamaEmbedder (nomic-embed-text, 768 dims),
and persists episodes and chunks to PostgreSQL + pgvector.

Usage via CLI:
    python -m backend.app.services.retrieval.ingest --limit 5
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

# Support running directly or as a module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

from backend.app.db.models import Chunk, Episode
from backend.app.db.session import async_session_factory
from backend.app.services.providers import get_embedder
from backend.app.services.retrieval.chunking import (
    chunk_transcript,
    parse_transcript,
)


@dataclass
class IngestStats:
    """Summary metrics of an ingestion run."""
    episodes_scanned: int = 0
    episodes_ingested: int = 0
    episodes_skipped: int = 0
    chunks_inserted: int = 0
    duration_seconds: float = 0.0


async def ingest_transcripts(
    transcripts_dir: Path | str,
    db: AsyncSession,
    limit: int | None = None,
    force_refresh: bool = False,
) -> IngestStats:
    """
    Ingest transcripts incrementally from a directory into PostgreSQL + pgvector.

    - Computes content_hash to skip unchanged episodes.
    - If hash changed or force_refresh is True, removes old chunks and re-embeds.
    - Batches embedding calls using OllamaEmbedder with 'search_document:' task prefix.
    """
    start_time = time.time()
    t_dir = Path(transcripts_dir)
    stats = IngestStats()

    if not t_dir.exists():
        print(f"Transcripts directory {t_dir} does not exist.", file=sys.stderr)
        return stats

    transcript_files = sorted(list(t_dir.glob("*/transcript.md")))
    stats.episodes_scanned = len(transcript_files)

    if limit and limit > 0:
        transcript_files = transcript_files[:limit]

    embedder = get_embedder()

    for idx, file_path in enumerate(transcript_files, start=1):
        rel_path = str(file_path.relative_to(t_dir.parent.parent) if t_dir.is_absolute() else file_path)
        content = file_path.read_text(encoding="utf-8")
        parsed = parse_transcript(content, source_path=rel_path)

        # 1. Check if episode already exists in DB
        stmt = select(Episode).where(Episode.source_path == rel_path)
        res = await db.execute(stmt)
        existing_episode = res.scalar_one_or_none()

        if existing_episode and not force_refresh:
            if existing_episode.content_hash == parsed.content_hash:
                # Content has not changed, skip re-embedding
                stats.episodes_skipped += 1
                continue

        # 2. Episode is new or content hash changed
        if existing_episode:
            # Delete old chunks for clean replacement
            await db.execute(delete(Chunk).where(Chunk.episode_id == existing_episode.id))
            existing_episode.title = parsed.title
            existing_episode.guest = parsed.guest
            existing_episode.content_hash = parsed.content_hash
            episode_obj = existing_episode
        else:
            episode_obj = Episode(
                title=parsed.title,
                guest=parsed.guest,
                source_path=rel_path,
                content_hash=parsed.content_hash,
            )
            db.add(episode_obj)
            await db.flush()

        # 3. Chunk transcript (~300-500 tokens)
        chunks_data = chunk_transcript(
            parsed,
            min_tokens=250,
            target_tokens=400,
            max_tokens=500,
            overlap_turns=1,
        )

        if not chunks_data:
            stats.episodes_ingested += 1
            await db.commit()
            continue

        # 4. Generate embeddings in batch via OllamaEmbedder with 'document' prefix
        chunk_texts = [c.text for c in chunks_data]
        embeddings = await embedder.embed(chunk_texts, kind="document")

        if len(embeddings) != len(chunks_data):
            raise RuntimeError(
                f"Embedder returned {len(embeddings)} vectors for {len(chunks_data)} chunks in {parsed.title}"
            )

        # 5. Insert chunks
        for c_data, emb in zip(chunks_data, embeddings):
            chunk_row = Chunk(
                episode_id=episode_obj.id,
                chunk_index=c_data.chunk_index,
                text=c_data.text,
                speaker=c_data.speaker,
                start_time=c_data.start_time,
                embedding=emb,
            )
            db.add(chunk_row)

        await db.commit()
        stats.episodes_ingested += 1
        stats.chunks_inserted += len(chunks_data)
        print(f"[{idx}/{len(transcript_files)}] Ingested '{parsed.title}' ({len(chunks_data)} chunks)")

    stats.duration_seconds = time.time() - start_time
    return stats


async def run_cli() -> None:
    parser = argparse.ArgumentParser(description="Ingest Lenny's Podcast transcripts into pgvector")
    parser.add_argument("--limit", type=int, default=None, help="Max number of episodes to ingest")
    parser.add_argument("--force", action="store_true", help="Force re-embedding of all episodes")
    default_dir = Path(__file__).resolve().parents[4] / "data" / "transcripts"
    if not default_dir.exists():
        default_dir = Path(__file__).resolve().parents[3] / "data" / "transcripts"
    parser.add_argument(
        "--transcripts-dir",
        type=str,
        default=str(default_dir),
        help="Path to transcripts directory",
    )
    args = parser.parse_args()

    print(f"Starting ingestion from: {args.transcripts_dir}")
    async with async_session_factory() as db:
        stats = await ingest_transcripts(
            transcripts_dir=args.transcripts_dir,
            db=db,
            limit=args.limit,
            force_refresh=args.force,
        )

    print("\n--- Ingestion Complete ---")
    print(f"Episodes scanned:  {stats.episodes_scanned}")
    print(f"Episodes ingested: {stats.episodes_ingested}")
    print(f"Episodes skipped:  {stats.episodes_skipped} (unchanged content hash)")
    print(f"Chunks inserted:   {stats.chunks_inserted}")
    print(f"Duration:          {stats.duration_seconds:.2f}s")


if __name__ == "__main__":
    asyncio.run(run_cli())
