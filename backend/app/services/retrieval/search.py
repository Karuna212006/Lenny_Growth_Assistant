"""
Vector Search and Retrieval Engine (Step 4).

Queries PostgreSQL + pgvector for top-k relevant transcript chunks using
cosine distance. Applies relevance thresholds (RETRIEVAL_MIN_SCORE) to support
the NO_RELEVANT_SOURCES out-of-scope refusal path.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Support running directly or as a module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

from backend.app.core.settings import settings
from backend.app.db.models import Chunk, Episode
from backend.app.services.providers import get_embedder


@dataclass
class RetrievedChunk:
    """A retrieved transcript chunk with episode metadata and similarity score."""
    chunk_id: UUID
    episode_id: UUID
    episode_title: str
    guest: str | None
    source_path: str
    chunk_index: int
    text: str
    speaker: str | None
    start_time: str | None
    score: float

    @property
    def citation(self) -> str:
        """Standard citation string: [Episode title — Guest] or [Episode title]."""
        if self.guest:
            return f"[{self.episode_title} — {self.guest}]"
        return f"[{self.episode_title}]"


async def search_transcripts(
    query: str,
    db: AsyncSession,
    top_k: int | None = None,
    min_score: float | None = None,
) -> list[RetrievedChunk]:
    """
    Perform semantic vector search across transcript chunks.

    1. Embeds query with OllamaEmbedder using 'search_query:' prefix.
    2. Performs cosine distance query on chunks.embedding.
    3. Joins episode metadata (title, guest, source_path).
    4. Filters results using min_score threshold.
    """
    k = top_k or settings.RETRIEVAL_TOP_K
    threshold = min_score if min_score is not None else settings.RETRIEVAL_MIN_SCORE

    embedder = get_embedder()
    query_embeddings = await embedder.embed([query], kind="query")

    if not query_embeddings or len(query_embeddings[0]) == 0:
        return []

    q_vec = query_embeddings[0]

    # pgvector cosine distance: chunks.embedding.cosine_distance(q_vec)
    # Cosine distance = 1 - cosine_similarity, so similarity = 1 - distance
    distance_col = Chunk.embedding.cosine_distance(q_vec).label("distance")

    stmt = (
        select(
            Chunk.id.label("chunk_id"),
            Chunk.episode_id,
            Episode.title.label("episode_title"),
            Episode.guest,
            Episode.source_path,
            Chunk.chunk_index,
            Chunk.text,
            Chunk.speaker,
            Chunk.start_time,
            distance_col,
        )
        .join(Episode, Chunk.episode_id == Episode.id)
        .order_by(distance_col.asc())
        .limit(k)
    )

    result = await db.execute(stmt)
    rows = result.all()

    retrieved: list[RetrievedChunk] = []
    for row in rows:
        similarity = 1.0 - float(row.distance)
        if similarity >= threshold:
            retrieved.append(
                RetrievedChunk(
                    chunk_id=row.chunk_id,
                    episode_id=row.episode_id,
                    episode_title=row.episode_title,
                    guest=row.guest,
                    source_path=row.source_path,
                    chunk_index=row.chunk_index,
                    text=row.text,
                    speaker=row.speaker,
                    start_time=row.start_time,
                    score=similarity,
                )
            )

    return retrieved
