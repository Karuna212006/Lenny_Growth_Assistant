"""
Intent Router (Section 4.4 / Phase 6).

Classifies user requests into fixed pipeline intents:
- 'qa': Standard grounded Q&A with transcript citations
- 'essay': Ship 30 for 30 structured essay generation (~1,250 words)
- 'artifact': Markdown or HTML/CSS component generation for the beside-chat viewer
- 'out_of_scope': Irrelevant queries cleanly refused without hallucination

Combines deterministic rule heuristics with LLM classification fallback.
"""
from __future__ import annotations

import re
from typing import Literal

from backend.app.agents.prompts import ROUTER_SYSTEM_PROMPT
from backend.app.services.providers.base import BaseLLMProvider

Intent = Literal["qa", "essay", "artifact", "out_of_scope"]

RE_ESSAY = re.compile(
    r"\b(write\s+(?:an?\s+)?essay|ship\s*30|1250\s*words|long[\s-]form\s+article|write\s+(?:an?\s+)?article|compose\s+(?:an?\s+)?essay)\b",
    re.IGNORECASE,
)

RE_ARTIFACT = re.compile(
    r"\b(create|generate|build|make|render)\s+(?:an?\s+)?(?:html|css|ui|component|artifact|table|cheatsheet|dashboard|page|mockup)\b|"
    r"\b(in\s+html|as\s+html|html/css|as\s+an\s+artifact|render\s+beside)\b",
    re.IGNORECASE,
)

RE_OUT_OF_SCOPE = re.compile(
    r"\b(recipe|banana\s+bread|baking|cook|weather\s+forecast|horoscope|astrology|lyrics|guitar\s+chords|movie\s+spoilers|sports\s+scores)\b",
    re.IGNORECASE,
)


def classify_intent_rules(prompt: str) -> Intent | None:
    """
    Deterministic rule-based intent classification.
    High-precision heuristics that guarantee small local models cannot misroute critical requests.
    """
    cleaned = prompt.strip()

    if RE_ESSAY.search(cleaned):
        return "essay"

    if RE_ARTIFACT.search(cleaned):
        return "artifact"

    if RE_OUT_OF_SCOPE.search(cleaned):
        return "out_of_scope"

    return None


async def classify_intent(
    prompt: str,
    provider: BaseLLMProvider | None = None,
) -> Intent:
    """
    Classify user message intent using fast rules, falling back to LLM classification.
    """
    rule_intent = classify_intent_rules(prompt)
    if rule_intent is not None:
        return rule_intent

    # If no rule triggered and no provider provided, default to qa
    if provider is None:
        return "qa"

    # LLM classification
    messages = [
        {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    try:
        response_text = ""
        async for token in provider.chat(messages, stream=False):
            response_text += token

        cleaned_resp = response_text.strip().lower()
        for candidate in ("essay", "artifact", "out_of_scope", "qa"):
            if candidate in cleaned_resp:
                return candidate  # type: ignore

        return "qa"
    except Exception:
        # Resilient fallback on LLM failure
        return "qa"
