import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, func, text
from backend.app.db.models import Chunk, Episode
from backend.app.db.session import async_session_factory

def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

async def main():
    print("=" * 80)
    print("1e.3 Verbatim Check: DB Chunk Text vs Source Transcript Files")
    print("=" * 80)

    async with async_session_factory() as session:
        # 1. Fetch Ada Chen Rekhi chunks 22 to 25
        stmt_ada = (
            select(Chunk, Episode)
            .join(Episode, Chunk.episode_id == Episode.id)
            .where(Episode.guest.ilike("%Ada Chen Rekhi%"))
            .where(Chunk.chunk_index.in_([22, 23, 24, 25]))
            .order_by(Chunk.chunk_index)
        )
        res_ada = await session.execute(stmt_ada)
        ada_rows = res_ada.all()

        # 2. Fetch 5 random chunks from across the database
        stmt_rand = (
            select(Chunk, Episode)
            .join(Episode, Chunk.episode_id == Episode.id)
            .order_by(func.random())
            .limit(5)
        )
        res_rand = await session.execute(stmt_rand)
        rand_rows = res_rand.all()

    target_rows = [(f"Ada Chen Rekhi (Chunk {c.chunk_index})", c, ep) for c, ep in ada_rows]
    target_rows.extend([(f"Random Chunk (Episode: {ep.guest}, Chunk {c.chunk_index})", c, ep) for c, ep in rand_rows])

    total_checked = 0
    total_matched = 0

    for label, chunk, episode in target_rows:
        total_checked += 1
        print(f"\n--- [{label}] ---")
        print(f"Episode Title: {episode.title}")
        print(f"Guest: {episode.guest}")
        print(f"Source Path: {episode.source_path}")
        print(f"Chunk Index: {chunk.chunk_index} | Speaker: {chunk.speaker} | Timestamp: {chunk.start_time}")
        
        chunk_prefix = chunk.text[:150]
        print(f"First 150 chars in DB:\n{repr(chunk_prefix)}")

        # Find source file
        source_p = Path(episode.source_path)
        if not source_p.exists():
            # Try resolving relative to workspace
            source_p = Path(__file__).resolve().parent.parent / episode.source_path
        if not source_p.exists():
            # Try searching data/transcripts
            matches = list(Path("data/transcripts").glob(f"*/{source_p.name}"))
            if matches:
                source_p = matches[0]

        if not source_p.exists():
            print(f"ERROR: Source file {source_p} not found on disk.")
            continue

        raw_transcript = source_p.read_text(encoding="utf-8")
        norm_source = normalize_whitespace(raw_transcript)
        
        norm_chunk_prefix = normalize_whitespace(chunk_prefix)
        is_exact_match = norm_chunk_prefix in norm_source

        # Clean speaker header for snippet check
        # e.g., "Ada Chen Rekhi (00:28:22): (00:29:53):\nSo I managed to get into..."
        cleaned_text = re.sub(r"^[A-Za-z0-9\s\.\'\-]+\s*\(\d{1,2}:\d{2}(?::\d{2})?\):\s*", "", chunk.text)
        cleaned_text = re.sub(r"^\(\d{1,2}:\d{2}(?::\d{2})?\):\s*", "", cleaned_text)
        snippet = normalize_whitespace(cleaned_text[:120])
        snippet_match = snippet in norm_source

        if is_exact_match or snippet_match:
            total_matched += 1
            print(f"VERBATIM MATCH: YES! Found in {source_p}")
        else:
            print(f"VERBATIM MATCH: NO! Could not find snippet in {source_p}")
            print(f"Searched for: {snippet}")

    print("\n" + "=" * 80)
    print(f"Summary: {total_matched}/{total_checked} chunks verified verbatim in source transcripts.")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
