"""
Sessions and Messages Router (LOCKED 4.3).

Handles:
- POST /sessions: Create session (upserting user from X-Anon-Key)
- GET /sessions: List sessions for user
- GET /sessions/{id}: Get session detail with messages and artifacts
- POST /sessions/{id}/messages: Send message and stream SSE events
"""
from __future__ import annotations

import json
import time
import uuid
from typing import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.exceptions import AppError
from backend.app.core.schemas import (
    ArtifactSummary,
    MessageCreate,
    MessageOut,
    SessionCreate,
    SessionDetail,
    SessionOut,
)
from backend.app.core.settings import settings
from backend.app.db.models import Artifact, Message, Session as ChatSession, User
from backend.app.db.session import async_session_factory, get_db
from backend.app.services.providers import get_provider

router = APIRouter(prefix="/sessions", tags=["sessions"])


async def get_or_create_user(db: AsyncSession, anon_key: str) -> User:
    """Find user by anon_key or create a new row safely handling concurrent requests."""
    res = await db.execute(select(User).where(User.anon_key == anon_key))
    user = res.scalar_one_or_none()
    if user:
        return user
    try:
        user = User(anon_key=anon_key)
        db.add(user)
        await db.flush()
        return user
    except Exception:
        await db.rollback()
        res = await db.execute(select(User).where(User.anon_key == anon_key))
        user = res.scalar_one_or_none()
        if user:
            return user
        raise



def resolve_anon_key(x_anon_key: str | None, anon_key_param: str | None) -> str:
    key = x_anon_key or anon_key_param
    if not key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header 'X-Anon-Key' or 'anon_key' parameter is required.",
        )
    return key


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: SessionCreate | None = None,
    x_anon_key: str | None = Header(None, alias="X-Anon-Key"),
    anon_key: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    key = resolve_anon_key(x_anon_key, anon_key)
    user = await get_or_create_user(db, key)

    session_title = (body.title if body and body.title else "New chat")
    provider_name = settings.LLM_PROVIDER
    model_name = (
        settings.OLLAMA_MODEL
        if provider_name == "ollama"
        else settings.OPENAI_COMPAT_MODEL
    )

    session = ChatSession(
        user_id=user.id,
        title=session_title,
        provider=provider_name,
        model=model_name,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return SessionOut(
        id=session.id,
        title=session.title,
        provider=session.provider,
        model=session.model,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get("", response_model=list[SessionOut])
async def list_sessions(
    x_anon_key: str | None = Header(None, alias="X-Anon-Key"),
    anon_key: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    key = resolve_anon_key(x_anon_key, anon_key)
    result = await db.execute(
        select(ChatSession)
        .join(User, ChatSession.user_id == User.id)
        .where(User.anon_key == key)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    return [
        SessionOut(
            id=s.id,
            title=s.title,
            provider=s.provider,
            model=s.model,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession)
        .options(
            selectinload(ChatSession.messages),
            selectinload(ChatSession.artifacts),
        )
        .where(ChatSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages_out = [
        MessageOut(
            id=m.id,
            role=m.role,  # type: ignore
            content=m.content,
            citations=m.citations or [],
            created_at=m.created_at,
        )
        for m in sorted(session.messages, key=lambda x: x.created_at)
    ]

    artifacts_out = [
        ArtifactSummary(
            id=a.id,
            type=a.type,  # type: ignore
            title=a.title,
            created_at=a.created_at,
        )
        for a in session.artifacts
    ]

    return SessionDetail(
        session=SessionOut(
            id=session.id,
            title=session.title,
            provider=session.provider,
            model=session.model,
            created_at=session.created_at,
            updated_at=session.updated_at,
        ),
        messages=messages_out,
        artifacts=artifacts_out,
    )


@router.post("/{session_id}/messages")
async def send_message(
    session_id: UUID,
    body: MessageCreate,
    x_anon_key: str | None = Header(None, alias="X-Anon-Key"),
    anon_key: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Send user prompt, stream SSE events from active provider,
    and persist messages.
    """
    # 1. Verify session exists
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Persist user message immediately
    user_msg = Message(
        session_id=session.id,
        role="user",
        content=body.content,
        provider=session.provider,
        model=session.model,
    )
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)

    # 3. Load recent history for context
    hist_result = await db.execute(
        select(Message)
        .where(Message.session_id == session.id)
        .order_by(Message.created_at.asc())
    )
    history_messages = hist_result.scalars().all()

    chat_history: list[dict[str, str]] = [
        {"role": m.role, "content": m.content}
        for m in history_messages
    ]

    from backend.app.agents.orchestrator import run_agent_pipeline

    async def event_generator() -> AsyncGenerator[str, None]:
        start_time = time.time()
        provider = get_provider(session.provider)
        citations_collected: list[dict[str, Any]] = []
        full_text = ""
        no_sources = False

        try:
            async for item in run_agent_pipeline(
                prompt=body.content,
                history=chat_history,
                provider=provider,
                db=db,
                session_id=session.id,
            ):
                event_name = item.get("event")
                event_data = item.get("data", {})

                if event_name == "status":
                    yield f"event: status\ndata: {json.dumps(event_data)}\n\n"
                elif event_name == "citations":
                    citations_collected = event_data.get("citations", [])
                    yield f"event: citations\ndata: {json.dumps(citations_collected)}\n\n"
                elif event_name == "artifact":
                    yield f"event: artifact\ndata: {json.dumps(event_data)}\n\n"
                elif event_name == "token":
                    t_val = event_data.get("text") or event_data.get("token") or ""
                    yield f"event: token\ndata: {json.dumps({'text': t_val, 'token': t_val})}\n\n"
                elif event_name == "done":
                    full_text = event_data.get("full_text", "")
                    no_sources = event_data.get("no_sources", False)
                    if not citations_collected:
                        citations_collected = event_data.get("citations", [])

            latency_ms = int((time.time() - start_time) * 1000)

            # Persist assistant reply in a fresh db session
            async with async_session_factory() as write_db:
                asst_msg = Message(
                    session_id=session.id,
                    role="assistant",
                    content=full_text,
                    provider=session.provider,
                    model=session.model,
                    latency_ms=latency_ms,
                    citations=citations_collected,
                )
                write_db.add(asst_msg)
                await write_db.commit()
                await write_db.refresh(asst_msg)
                asst_id = str(asst_msg.id)

            yield f"event: done\ndata: {json.dumps({'message_id': asst_id, 'no_sources': no_sources})}\n\n"

        except AppError as app_err:
            error_data = {
                "error": {
                    "code": app_err.code,
                    "message": app_err.message,
                    "request_id": "",
                }
            }
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
        except Exception as exc:
            error_data = {
                "error": {
                    "code": "MODEL_UNAVAILABLE",
                    "message": str(exc),
                    "request_id": "",
                }
            }
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
