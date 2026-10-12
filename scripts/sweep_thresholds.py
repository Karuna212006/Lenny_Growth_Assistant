import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.services.retrieval.search import search_transcripts
from backend.app.db.session import async_session_factory
from backend.app.services.providers import get_embedder

ANSWERABLE_QUESTIONS = [
    "What did Ada Chen Rekhi advise about knowing when it's time to leave your job?",
    "How did Adam Fishman describe the core pillars of growth teams?",
    "What did April Dunford say about sales pitch and differentiated value?",
    "What did Ethan Evans advise about career ownership and promotions?",
    "What did Barbra Gago say about category creation and rebranding?",
]

UNRELATED_QUESTIONS = [
    "What is the capital city of Australia and what is its population?",
    "How do you make authentic Neapolitan pizza dough with double zero flour?",
    "Who won the FIFA World Cup in 1994 and what was the penalty shootout score?",
]

THRESHOLDS = [0.30, 0.35, 0.40, 0.45, 0.50, 0.55]

async def run_sweep():
    print("=" * 80)
    print("1e.4 Distance Threshold Sweep (Real Database & nomic-embed-text)")
    print("=" * 80)

    # 1. First test Ada query top retrieved chunks and distances
    ada_query = ANSWERABLE_QUESTIONS[0]
    print(f"\nEvaluating Top Chunks for Ada Query:\n'{ada_query}'")
    async with async_session_factory() as db:
        top_chunks = await search_transcripts(ada_query, db=db, top_k=6, min_score=None)
        print(f"Retrieved {len(top_chunks)} chunks total:")
        for idx, c in enumerate(top_chunks, start=1):
            # score is cosine similarity; distance = 1.0 - similarity
            dist = 1.0 - c.score
            passes_030 = dist <= 0.30
            passes_045 = dist <= 0.45
            print(f"  [Chunk {idx}] ID: {c.chunk_id}")
            print(f"    Episode: {c.episode_title} — {c.guest}")
            print(f"    Similarity: {c.score:.4f} | Cosine Distance: {dist:.4f}")
            print(f"    Passes 0.30 threshold: {passes_030} | Passes 0.45 threshold: {passes_045}")
            print(f"    Snippet: {c.text[:120]}...\n")

    # 2. Sweep across all questions
    results = {}
    for t in THRESHOLDS:
        results[t] = {"ans_count": 0, "ref_count": 0}

    print("\nRunning threshold sweep across 5 answerable and 3 unrelated questions...")
    async with async_session_factory() as db:
        # Check answerable
        print("\nAnswerable Questions:")
        for q in ANSWERABLE_QUESTIONS:
            chunks = await search_transcripts(q, db=db, top_k=1, min_score=None)
            best_dist = (1.0 - chunks[0].score) if chunks else 1.0
            print(f"  Q: '{q[:50]}...' -> Best Distance: {best_dist:.4f}")
            for t in THRESHOLDS:
                if best_dist <= t:
                    results[t]["ans_count"] += 1

        # Check unrelated
        print("\nUnrelated Questions:")
        for q in UNRELATED_QUESTIONS:
            chunks = await search_transcripts(q, db=db, top_k=1, min_score=None)
            best_dist = (1.0 - chunks[0].score) if chunks else 1.0
            print(f"  Q: '{q[:50]}...' -> Best Distance: {best_dist:.4f}")
            for t in THRESHOLDS:
                if best_dist > t:
                    results[t]["ref_count"] += 1

    print("\n" + "=" * 80)
    print("Sweep Results Summary Table:")
    print("threshold | answered (of 5) | refused (of 3)")
    print("-" * 45)
    for t in THRESHOLDS:
        ans = results[t]["ans_count"]
        ref = results[t]["ref_count"]
        print(f"  {t:.2f}    |       {ans}/5       |      {ref}/3")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_sweep())
