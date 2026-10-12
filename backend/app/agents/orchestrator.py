"""
Agent Orchestrator and Execution Pipelines (Section 4.4 / Phase 6).

Coordinates the fixed execution pipelines:
- qa: query rewriting -> vector retrieval -> citation enforcement -> streaming answer
- out_of_scope: polite refusal without LLM hallucination
- essay / artifact: routed to specialized skill and artifact handlers
"""
from __future__ import annotations

import json
from typing import AsyncGenerator, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.prompts import (
    OUT_OF_SCOPE_REFUSAL,
    QA_SYSTEM_PROMPT,
)
from backend.app.agents.rewriter import rewrite_query
from backend.app.agents.router import classify_intent, Intent
import logging
from backend.app.core.settings import settings
from backend.app.services.providers.base import BaseLLMProvider
from backend.app.services.retrieval.search import search_transcripts, RetrievedChunk

logger = logging.getLogger("lenny.agents.orchestrator")

RETRIEVAL_TOOL_SCHEMA = [
    {
        "name": "retrieve_transcripts",
        "description": "Retrieve relevant transcripts from Lenny's podcast archives based on a search query.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to locate relevant podcast episodes and transcripts",
                }
            },
            "required": ["query"],
        },
    }
]


async def invoke_retrieval_tool_agent(
    search_query: str,
    db: AsyncSession,
    top_k: int | None = None,
) -> list[RetrievedChunk]:
    """
    Execute transcript retrieval through the Anthropic Python SDK tool-calling loop.
    Calls local Ollama's Messages API compatibility layer to invoke the retrieve_transcripts tool,
    then executes real vector search in pgvector.
    """
    model_name = settings.OLLAMA_MODEL if settings.LLM_PROVIDER == "ollama" else (settings.OPENAI_COMPAT_MODEL or "qwen2.5:7b-instruct")
    base_url = settings.OLLAMA_BASE_URL if settings.LLM_PROVIDER == "ollama" else (settings.OPENAI_COMPAT_BASE_URL or "http://localhost:11434")
    api_key = settings.OPENAI_COMPAT_API_KEY or "ollama"

    query_to_search = search_query

    try:
        from anthropic import Anthropic
        client = Anthropic(base_url=base_url, api_key=api_key, timeout=float(min(settings.LLM_TIMEOUT_SECONDS, 30)))
        system_prompt = (
            "You are a podcast research assistant. When asked about podcast topics, "
            "you MUST call the retrieve_transcripts tool with a precise search query."
        )
        response = client.messages.create(
            model=model_name,
            max_tokens=256,
            system=system_prompt,
            messages=[{"role": "user", "content": search_query}],
            tools=RETRIEVAL_TOOL_SCHEMA,
        )

        for block in getattr(response, "content", []):
            if getattr(block, "type", None) == "tool_use" and block.name == "retrieve_transcripts":
                query_to_search = block.input.get("query", search_query)
                logger.info("Agent SDK tool call invoked: %s with query='%s'", block.name, query_to_search)
                break
    except Exception as exc:
        logger.warning("Agent SDK tool call fell back to direct search: %s", exc)

    return await search_transcripts(query_to_search, db=db, top_k=top_k)



async def run_agent_pipeline(
    prompt: str,
    history: list[dict[str, str]],
    provider: BaseLLMProvider,
    db: AsyncSession,
    session_id: UUID | None = None,
) -> AsyncGenerator[dict[str, Any], None]:
    """
    Execute the agent workflow and yield SSE event dictionaries.

    Yielded dictionary structure:
    {"event": str, "data": dict}
    """
    # 1. Classify Intent
    intent: Intent = await classify_intent(prompt, provider=provider)

    # Path A: Out of Scope
    if intent == "out_of_scope":
        yield {"event": "status", "data": {"stage": "generating"}}
        words = OUT_OF_SCOPE_REFUSAL.split(" ")
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            yield {"event": "token", "data": {"text": token}}
        yield {
            "event": "done",
            "data": {
                "citations": [],
                "no_sources": True,
                "full_text": OUT_OF_SCOPE_REFUSAL,
                "intent": "out_of_scope",
            },
        }
        return

    # Path B: Artifact Generation (Markdown or HTML/CSS)
    if intent == "artifact":
        yield {"event": "status", "data": {"stage": "generating"}}
        from backend.app.services.artifacts.generator import generate_artifact_content
        from backend.app.db.models import Artifact

        is_html = any(k in prompt.lower() for k in ("html", "css", "ui", "component", "mockup", "page", "dashboard"))
        art_type = "html" if is_html else "markdown"

        title, clean_content, blocked = await generate_artifact_content(prompt, art_type, provider)

        art_id = None
        if session_id is not None:
            artifact_obj = Artifact(
                session_id=session_id,
                type=art_type,
                title=title,
                content=clean_content,
            )
            db.add(artifact_obj)
            await db.commit()
            await db.refresh(artifact_obj)
            art_id = str(artifact_obj.id)

        artifact_summary = {
            "id": art_id or "preview",
            "type": art_type,
            "title": title,
            "blocked_threats": blocked,
        }
        yield {"event": "artifact", "data": artifact_summary}

        explanation = (
            f"I have created the requested {art_type.upper()} artifact: **{title}**.\n\n"
            f"You can view and inspect the rendered preview and code in the Artifact Viewer panel beside this chat."
        )
        for word in explanation.split(" "):
            yield {"event": "token", "data": {"text": word + " "}}

        yield {
            "event": "done",
            "data": {
                "citations": [],
                "no_sources": False,
                "full_text": explanation,
                "intent": "artifact",
                "artifact_id": art_id,
            },
        }
        return

    # Path C: Essay Generation (Ship 30 for 30 Skill)
    if intent == "essay":
        yield {"event": "status", "data": {"stage": "retrieving"}}
        search_query = await rewrite_query(prompt, history, provider=provider)
        try:
            retrieved_chunks = await invoke_retrieval_tool_agent(search_query, db=db, top_k=8)
        except Exception:
            retrieved_chunks = []

        if not retrieved_chunks:
            yield {"event": "status", "data": {"stage": "generating"}}
            refusal_msg = (
                f"Cannot generate a grounded essay on '{prompt}': no supporting discussions were "
                f"found in Lenny's Podcast transcripts. Grounding is strictly enforced."
            )
            for word in refusal_msg.split(" "):
                yield {"event": "token", "data": {"text": word + " "}}
            yield {
                "event": "done",
                "data": {
                    "citations": [],
                    "no_sources": True,
                    "full_text": refusal_msg,
                    "intent": "essay",
                },
            }
            return

        citations_data = [
            {
                "episode_id": str(c.episode_id),
                "title": c.episode_title,
                "guest": c.guest,
                "chunk_id": str(c.chunk_id),
                "score": round(c.score, 4),
                "citation": c.citation,
                "speaker": c.speaker,
                "start_time": c.start_time,
            }
            for c in retrieved_chunks
        ]
        yield {"event": "citations", "data": {"citations": citations_data}}
        yield {"event": "status", "data": {"stage": "generating"}}

        from backend.app.skills.ship30.generator import generate_ship30_essay

        accumulated_tokens: list[str] = []
        async for token in generate_ship30_essay(prompt, retrieved_chunks, provider):
            accumulated_tokens.append(token)
            yield {"event": "token", "data": {"text": token}}

        full_text = "".join(accumulated_tokens)
        yield {
            "event": "done",
            "data": {
                "citations": citations_data,
                "no_sources": False,
                "full_text": full_text,
                "intent": "essay",
            },
        }
        return

    # Path B: Standard Q&A
    yield {"event": "status", "data": {"stage": "retrieving"}}

    # Rewrite query if conversational follow-up
    search_query = await rewrite_query(prompt, history, provider=provider)

    # Perform vector search across transcript chunks in pgvector via agent SDK tool calling
    retrieved_chunks: list[RetrievedChunk] = []
    try:
        retrieved_chunks = await invoke_retrieval_tool_agent(search_query, db=db)
    except Exception as exc:
        # DB search error or empty db
        retrieved_chunks = []

    # If no relevant chunks found or below similarity threshold
    if not retrieved_chunks:
        yield {"event": "status", "data": {"stage": "generating"}}
        refusal_msg = (
            f"Based on the available transcripts from Lenny's Podcast, no relevant discussions "
            f"were found regarding '{prompt}'. I only answer based on topics covered by Lenny and his guests."
        )
        words = refusal_msg.split(" ")
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            yield {"event": "token", "data": {"text": token}}
        yield {
            "event": "done",
            "data": {
                "citations": [],
                "no_sources": True,
                "full_text": refusal_msg,
                "intent": "qa",
            },
        }
        return

    # Send citations metadata to frontend
    citations_data = [
        {
            "episode_id": str(c.episode_id),
            "title": c.episode_title,
            "guest": c.guest,
            "chunk_id": str(c.chunk_id),
            "score": round(c.score, 4),
            "citation": c.citation,
            "speaker": c.speaker,
            "start_time": c.start_time,
        }
        for c in retrieved_chunks
    ]
    yield {"event": "citations", "data": {"citations": citations_data}}

    # 3. Assemble Grounded Prompt
    context_blocks = []
    for idx, c in enumerate(retrieved_chunks, start=1):
        context_blocks.append(
            f"--- Excerpt {idx} {c.citation} ---\n{c.text}"
        )
    combined_context = "\n\n".join(context_blocks)

    augmented_user_message = (
        f"Context from Lenny's Podcast Transcripts:\n\n{combined_context}\n\n"
        f"User Question: {prompt}\n\n"
        f"Please answer the question thoroughly, citing claims using exact source tags like {retrieved_chunks[0].citation}."
    )

    llm_messages = [
        {"role": "system", "content": QA_SYSTEM_PROMPT},
        {"role": "user", "content": augmented_user_message},
    ]

    # 4. Stream Tokens from Provider
    yield {"event": "status", "data": {"stage": "generating"}}

    accumulated_tokens: list[str] = []
    async for token in provider.chat(llm_messages, stream=True):
        accumulated_tokens.append(token)
        yield {"event": "token", "data": {"text": token}}

    full_text = "".join(accumulated_tokens)
    yield {
        "event": "done",
        "data": {
            "citations": citations_data,
            "no_sources": False,
            "full_text": full_text,
            "intent": "qa",
        },
    }
