import asyncio
import math
import os
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.services.retrieval.chunking import parse_transcript, chunk_transcript
from backend.app.services.providers import get_embedder, get_provider
from backend.app.agents.prompts import QA_SYSTEM_PROMPT
from backend.app.services.retrieval.search import RetrievedChunk

query = "What did Ada Chen Rekhi advise about knowing when it's time to leave your job?"

async def run():
    print("=" * 70)
    print("1d.1: Real Pipeline (Real Transcript, Real Embeddings, Real Ollama Model)")
    print(f"Query: '{query}'")
    print("=" * 70)

    # 1. Load real transcript and chunk
    transcript_path = Path("data/transcripts/ada-chen-rekhi/transcript.md")
    content = transcript_path.read_text(encoding="utf-8")
    parsed = parse_transcript(content, source_path=str(transcript_path))
    chunks = chunk_transcript(parsed, min_tokens=250, target_tokens=400, max_tokens=500, overlap_turns=1)
    print(f"\nParsed episode: '{parsed.title}' (Guest: {parsed.guest})")
    print(f"Total chunks from real transcript: {len(chunks)}")

    # 2. Embed with local Ollama nomic-embed-text
    embedder = get_embedder()
    print("\nComputing real query embedding with Ollama nomic-embed-text...")
    q_emb = (await embedder.embed([query], kind="query"))[0]

    print(f"Computing real document embeddings for {len(chunks)} chunks with Ollama nomic-embed-text...")
    doc_texts = [c.text for c in chunks]
    doc_embs = await embedder.embed(doc_texts, kind="document")

    # 3. Compute cosine distance
    scored = []
    for idx, (c, d_emb) in enumerate(zip(chunks, doc_embs)):
        dot = sum(a * b for a, b in zip(q_emb, d_emb))
        norm_q = math.sqrt(sum(a * a for a in q_emb))
        norm_d = math.sqrt(sum(a * a for a in d_emb))
        sim = dot / (norm_q * norm_d)
        dist = 1.0 - sim
        scored.append((dist, sim, idx, c))

    scored.sort(key=lambda x: x[0])

    top_k = 4
    top_results = scored[:top_k]

    print("\n--- (a) Exact Retrieved Chunks ---")
    retrieved_chunks = []
    for rank, (dist, sim, idx, c) in enumerate(top_results, start=1):
        chunk_id = uuid4()
        r_chunk = RetrievedChunk(
            chunk_id=chunk_id,
            episode_id=uuid4(),
            episode_title=parsed.title,
            guest=parsed.guest,
            source_path=str(transcript_path),
            chunk_index=c.chunk_index,
            text=c.text,
            speaker=c.speaker,
            start_time=c.start_time,
            score=sim,
        )
        retrieved_chunks.append((dist, r_chunk))
        print(f"\n[Source S{rank}] Chunk ID: {chunk_id}")
        print(f"Episode: {parsed.title} — {parsed.guest}")
        print(f"Distance: {dist:.4f} (Cosine similarity: {sim:.4f})")
        print(f"Timestamp: {c.start_time} | Speaker: {c.speaker}")
        print(f"First 200 chars:\n{c.text[:200].strip()}...")

    # 4. Assemble Grounded Prompt
    context_blocks = []
    for idx, (dist, c) in enumerate(retrieved_chunks, start=1):
        context_blocks.append(f"--- [S{idx}] {c.citation} ({c.start_time}) ---\n{c.text}")
    combined_context = "\n\n".join(context_blocks)

    augmented_user_message = (
        f"Context from Lenny's Podcast Transcripts:\n\n{combined_context}\n\n"
        f"User Question: {query}\n\n"
        f"Instructions:\n"
        f"- Answer thoroughly and objectively using ONLY the facts directly stated in the context excerpts above.\n"
        f"- Cite every factual claim using [S#] tags matching the numbered sources (e.g., [S1], [S2]).\n"
        f"- If the sources do not contain sufficient evidence to answer certain aspects, explicitly state that.\n"
        f"- Do NOT make up external frameworks, dates, numbers, or rules not present in the excerpts."
    )

    llm_messages = [
        {"role": "system", "content": QA_SYSTEM_PROMPT},
        {"role": "user", "content": augmented_user_message},
    ]

    print("\n--- (b) Full Prompt Sent to Model ---")
    print("=" * 60)
    print(augmented_user_message)
    print("=" * 60)

    # 5. Generate Real Answer via Ollama qwen2.5:7b-instruct
    print("\n--- (c) Model's Real Answer ---")
    provider = get_provider("ollama")
    tokens = []
    async for token in provider.chat(llm_messages, stream=True):
        tokens.append(token)
        sys.stdout.write(token)
        sys.stdout.flush()

    full_answer = "".join(tokens)
    print("\n\n" + "=" * 70)
    print(f"Total answer length: {len(full_answer.split())} words")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run())
