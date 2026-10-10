"""
Ship 30 for 30 Essay Generator (Phase 7 / Section 10).

Generates ~1,250 word long-form essays grounded in Lenny's Podcast transcripts:
- Irresistible opening hook
- 5-part narrative progression
- Scannable visual cadence (H2/H3, bullet points, selective bold)
- Strict inline citations: [Episode title — Guest]
- Actionable Monday-morning takeaway checklist
"""
from __future__ import annotations

from typing import AsyncGenerator
from backend.app.services.providers.base import BaseLLMProvider
from backend.app.services.retrieval.search import RetrievedChunk

SHIP30_SYSTEM_PROMPT = """You are a master digital writer trained in the Ship 30 for 30 methodology and an expert analyst of Lenny's Podcast.
Your goal is to write a comprehensive, high-impact ~1,250-word essay on the requested topic, grounded strictly in the provided transcript excerpts.

ESSAY ARCHITECTURE (~1,250 Words):
1. **The Hook (75-100 words):** Open with tension and a contrarian observation. No throat-clearing. State what is at stake.
2. **The Problem / Paradigm Shift (200-250 words):** Why conventional playbooks fail. Introduce the new model from Lenny's interviews.
3. **Pillar 1: Strategic Foundations (250-300 words):** Deep dive into the core framework. Quote or attribute insights using [Episode title — Guest].
4. **Pillar 2: Tactical Execution (250-300 words):** Step-by-step operating cadence and execution playbook with real company examples.
5. **Pillar 3: Non-Obvious Pitfalls (200-250 words):** What top 1% practitioners avoid that amateurs do.
6. **The Takeaway Checklist (100-150 words):** Bulleted summary ready to implement on Monday morning.

FORMATTING & STYLE RULES:
- Use clear Markdown headings: ## for major sections, ### for sub-points.
- Keep paragraphs short (1 to 3 sentences maximum).
- Use bullet points liberally to improve scannability.
- Use **selective bolding** on the key phrases or first few words of key insights.
- Target ~1,250 words (aim between 1,125 and 1,375 words). Provide depth, detail, and substance.
- Every major strategy must cite the source as: [Episode title — Guest].
"""


async def generate_ship30_essay(
    topic: str,
    chunks: list[RetrievedChunk],
    provider: BaseLLMProvider,
) -> AsyncGenerator[str, None]:
    """
    Stream a Ship 30 for 30 structured essay grounded in transcript excerpts.
    """
    context_blocks = []
    for idx, c in enumerate(chunks, start=1):
        context_blocks.append(
            f"--- Source Excerpt {idx} {c.citation} ---\n{c.text}"
        )
    combined_context = "\n\n".join(context_blocks)

    user_prompt = (
        f"Available Transcript Context from Lenny's Podcast:\n\n{combined_context}\n\n"
        f"Essay Topic: {topic}\n\n"
        f"Write a full, publication-ready ~1,250-word Ship 30 for 30 essay on this topic. "
        f"Follow the 6-part architecture, include short paragraphs, headings, bullet points, "
        f"selective bolding, and inline citations like {chunks[0].citation if chunks else '[Episode Title — Guest]'}."
    )

    messages = [
        {"role": "system", "content": SHIP30_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    async for token in provider.chat(messages, stream=True):
        yield token
