"""
Verification Script for nomic-embed-text and OllamaEmbedder (LOCKED 4.6).

Verifies:
1. Dimensionality: len(embedding) == 768.
2. Semantic similarity: A query vector ('how do I grow a startup') scores significantly
   higher against related content ('startup growth tactics') than unrelated content
   ('banana bread recipe').
"""
from __future__ import annotations

import asyncio
import math
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.services.providers.ollama import OllamaEmbedder


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


async def verify() -> None:
    print("Connecting to host OllamaEmbedder at http://localhost:11434...")
    embedder = OllamaEmbedder(base_url="http://localhost:11434", timeout_seconds=120.0)

    available = await embedder.is_available()
    print(f"OllamaEmbedder available: {available}")
    if not available:
        print("Warning: nomic-embed-text might still be loading or pulling.", file=sys.stderr)

    query_text = "how do I grow a startup"
    doc_related = "startup growth tactics, customer acquisition loops, and onboarding"
    doc_unrelated = "classic homemade banana bread recipe with ripe bananas and walnuts"

    print("\n1. Generating query embedding (with 'search_query:' prefix)...")
    q_embeds = await embedder.embed([query_text], kind="query")
    if not q_embeds or len(q_embeds[0]) == 0:
        print("Error: Empty embedding returned!", file=sys.stderr)
        sys.exit(1)

    q_vec = q_embeds[0]
    dims = len(q_vec)
    print(f"   Query vector dimension: {dims}")
    assert dims == 768, f"Expected 768 dimensions, got {dims}"
    print("   [PASS] Dimension check: Exactly 768 dimensions.")

    print("\n2. Generating batch document embeddings (with 'search_document:' prefix)...")
    doc_embeds = await embedder.embed([doc_related, doc_unrelated], kind="document")
    assert len(doc_embeds) == 2, f"Expected 2 embeddings, got {len(doc_embeds)}"
    assert len(doc_embeds[0]) == 768
    assert len(doc_embeds[1]) == 768

    sim_related = cosine_similarity(q_vec, doc_embeds[0])
    sim_unrelated = cosine_similarity(q_vec, doc_embeds[1])

    print(f"\n3. Semantic Similarity Results:")
    print(f"   Query:      '{query_text}'")
    print(f"   Related:    '{doc_related}' -> Cosine Sim: {sim_related:.4f}")
    print(f"   Unrelated:  '{doc_unrelated}' -> Cosine Sim: {sim_unrelated:.4f}")

    assert sim_related > sim_unrelated, (
        f"Semantic check failed: related ({sim_related:.4f}) <= unrelated ({sim_unrelated:.4f})"
    )
    print(f"   Difference: +{sim_related - sim_unrelated:.4f} in favor of related text.")
    print("   [PASS] Semantic similarity check passed!\n")
    print("=== All embedder verification checks passed successfully! ===")


if __name__ == "__main__":
    asyncio.run(verify())
