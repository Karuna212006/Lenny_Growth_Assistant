"""
Follow-up Query Rewriter (Section 4.4 / Phase 6).

Detects conversational follow-ups and rewrites them into standalone search queries
using session history so vector search captures the intended context.
"""
from __future__ import annotations

import re
from backend.app.agents.prompts import QUERY_REWRITE_SYSTEM_PROMPT
from backend.app.services.providers.base import BaseLLMProvider

RE_FOLLOW_UP_SIGNALS = re.compile(
    r"\b(it|he|she|they|that|this|the\s+second\s+(?:point|one|lever)|the\s+first\s+one|why\s+did\s+(?:he|she|they)|tell\s+me\s+more|elaborate|what\s+about\s+(?:that|it)|how\s+so)\b",
    re.IGNORECASE,
)


def is_follow_up(prompt: str) -> bool:
    """Heuristic check whether prompt references prior conversational context."""
    cleaned = prompt.strip()
    words = cleaned.split()
    if len(words) <= 4:
        # Short phrases like "why?", "how so?", "tell me more" are almost always follow-ups
        return True
    return bool(RE_FOLLOW_UP_SIGNALS.search(cleaned))


async def rewrite_query(
    prompt: str,
    history: list[dict[str, str]],
    provider: BaseLLMProvider | None = None,
) -> str:
    """
    Rewrite a user prompt into a standalone search query if it is a follow-up.
    """
    if not history or len(history) <= 1:
        return prompt

    if not is_follow_up(prompt):
        return prompt

    if provider is None:
        # Simple heuristic fallback: combine with last user prompt
        prev_user_queries = [m["content"] for m in history if m.get("role") == "user"]
        if prev_user_queries:
            return f"{prev_user_queries[-1]} {prompt}"
        return prompt

    # Take recent 3 messages for context window efficiency
    recent_history = history[-3:]
    context_str = "\n".join(
        f"{m.get('role', 'user').capitalize()}: {m.get('content', '')}"
        for m in recent_history
    )

    messages = [
        {"role": "system", "content": QUERY_REWRITE_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Conversation context:\n{context_str}\n\nFollow-up question:\n{prompt}",
        },
    ]

    try:
        rewritten = ""
        async for token in provider.chat(messages, stream=False):
            rewritten += token

        cleaned = rewritten.strip().strip('"\'')
        return cleaned if cleaned else prompt
    except Exception:
        return prompt
