"""
Artifact HTML Sanitizer and Security Sandbox Injector (Phase 8 / Section 4.7).

Sanitizes untrusted LLM-generated HTML:
- Removes executable scripts (<script>, event handlers like onload/onerror, javascript: URLs)
- Disallows forms, iframes, and active objects
- Injects strict Content-Security-Policy (CSP) meta tag
- Logs stripped/blocked threats for the security inspection panel
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class SanitizationResult:
    """Sanitized output and telemetry of blocked threats."""
    clean_content: str
    blocked_items: list[str] = field(default_factory=list)
    has_threats: bool = False


# Security regexes
RE_SCRIPT_TAG = re.compile(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", re.IGNORECASE | re.DOTALL)
RE_EVENT_HANDLER = re.compile(r"\s+on[a-zA-Z]+\s*=\s*['\"][^'\"]*['\"]", re.IGNORECASE)
RE_JS_URL = re.compile(r"href\s*=\s*['\"]javascript:[^'\"]*['\"]", re.IGNORECASE)
RE_IFRAME_TAG = re.compile(r"<\s*iframe[^>]*>.*?<\s*/\s*iframe\s*>", re.IGNORECASE | re.DOTALL)
RE_OBJECT_TAG = re.compile(r"<\s*(?:object|embed|applet)[^>]*>.*?<\s*/\s*(?:object|embed|applet)\s*>", re.IGNORECASE | re.DOTALL)
RE_FORM_TAG = re.compile(r"<\s*form[^>]*>.*?<\s*/\s*form\s*>", re.IGNORECASE | re.DOTALL)

CSP_META_TAG = '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; img-src data:;">'


def sanitize_html(raw_html: str) -> SanitizationResult:
    """
    Sanitize untrusted HTML and inject strict CSP meta tag.
    """
    blocked: list[str] = []
    content = raw_html

    # 1. Strip script tags
    if RE_SCRIPT_TAG.search(content):
        blocked.append("<script> tag execution")
        content = RE_SCRIPT_TAG.sub("", content)

    # 2. Strip event handlers (onload, onerror, onclick, etc.)
    if RE_EVENT_HANDLER.search(content):
        blocked.append("Inline DOM event handler (e.g. onerror/onload)")
        content = RE_EVENT_HANDLER.sub("", content)

    # 3. Strip javascript: URLs
    if RE_JS_URL.search(content):
        blocked.append("javascript: pseudo-protocol URL")
        content = RE_JS_URL.sub('href="#"', content)

    # 4. Strip iframes
    if RE_IFRAME_TAG.search(content):
        blocked.append("<iframe tag>")
        content = RE_IFRAME_TAG.sub("", content)

    # 5. Strip forms
    if RE_FORM_TAG.search(content):
        blocked.append("<form tag>")
        content = RE_FORM_TAG.sub("", content)

    # 6. Strip objects/embeds
    if RE_OBJECT_TAG.search(content):
        blocked.append("<object/embed tag>")
        content = RE_OBJECT_TAG.sub("", content)

    # 7. Inject CSP into head (or prepend if no head)
    if "<head>" in content.lower():
        content = re.sub(r"(<head[^>]*>)", r"\1\n    " + CSP_META_TAG, content, flags=re.IGNORECASE)
    else:
        content = f"{CSP_META_TAG}\n{content}"

    return SanitizationResult(
        clean_content=content,
        blocked_items=blocked,
        has_threats=len(blocked) > 0,
    )
