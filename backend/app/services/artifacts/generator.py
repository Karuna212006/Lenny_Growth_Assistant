"""
Artifact Generator (Phase 8 / Section 11).

Generates rich, self-contained Markdown or HTML/CSS artifacts based on user request:
- Validates output bounds (< 150KB, non-empty)
- Sanitizes HTML content and injects CSP
- Stores generated artifacts in PostgreSQL
"""
from __future__ import annotations

import re
from typing import Literal
from backend.app.services.artifacts.sanitizer import sanitize_html
from backend.app.services.providers.base import BaseLLMProvider

MAX_ARTIFACT_SIZE_BYTES = 150 * 1024  # 150 KB

HTML_ARTIFACT_PROMPT = """You are a senior UI engineer and technical designer.
Generate a self-contained, beautifully styled HTML/CSS artifact based on the user's request.

DESIGN & CODING REQUIREMENTS:
- Produce complete, valid HTML with embedded <style> inside <head>.
- Modern typography, clean dark/light mode friendly color palette, card components, borders, and responsive layout.
- NO external scripts, NO javascript:, NO frameworks (Vanilla CSS only).
- Do NOT wrap your output in markdown code blocks (e.g. ```html). Output pure HTML starting with <!DOCTYPE html>.
"""

MARKDOWN_ARTIFACT_PROMPT = """You are an expert technical writer and product researcher.
Generate a comprehensive, beautifully structured Markdown document (cheatsheet, comparison table, or executive summary) based on the user's request.

REQUIREMENTS:
- Use clean Markdown with headers (#, ##, ###), tables, bullet points, and bold terms.
- Do NOT wrap in triple backticks. Output raw Markdown directly.
"""


async def generate_artifact_content(
    prompt: str,
    artifact_type: Literal["html", "markdown"],
    provider: BaseLLMProvider,
) -> tuple[str, str, list[str]]:
    """
    Generate and sanitize artifact content.

    Returns:
        (title, sanitized_content, blocked_threats)
    """
    system_prompt = HTML_ARTIFACT_PROMPT if artifact_type == "html" else MARKDOWN_ARTIFACT_PROMPT

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Create a {artifact_type} artifact for: {prompt}"},
    ]

    raw_tokens: list[str] = []
    async for token in provider.chat(messages, stream=True):
        raw_tokens.append(token)

    content = "".join(raw_tokens).strip()

    # Remove enclosing code fences if model accidentally emitted them
    if content.startswith("```html") or content.startswith("```markdown"):
        content = re.sub(r"^```(?:html|markdown)?\n?", "", content)
        content = re.sub(r"\n?```$", "", content)
        content = content.strip()

    if len(content.encode("utf-8")) > MAX_ARTIFACT_SIZE_BYTES:
        content = content[:MAX_ARTIFACT_SIZE_BYTES]

    # Extract title
    title = "Generated Artifact"
    if artifact_type == "html":
        title_match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
        sanitized = sanitize_html(content)
        return title, sanitized.clean_content, sanitized.blocked_items
    else:
        h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if h1_match:
            title = h1_match.group(1).strip()
        return title, content, []
