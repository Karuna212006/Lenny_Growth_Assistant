from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from uuid import UUID
import uuid
from backend.app.db.session import get_db
from backend.app.db.models import User, Session as ChatSession, Message, Artifact
from backend.app.core.settings import settings

router = APIRouter(prefix="/sessions", tags=["sessions"])

class CreateSessionRequest(BaseModel):
    anon_key: str
    title: str = "New chat"

class SessionResponse(BaseModel):
    id: UUID
    title: str
    provider: str
    model: str
    created_at: str
    updated_at: str

@router.post("", response_model=SessionResponse)
async def create_session(body: CreateSessionRequest, db: AsyncSession = Depends(get_db)):
    # upsert user
    result = await db.execute(select(User).where(User.anon_key == body.anon_key))
    user = result.scalar_one_or_none()
    if not user:
        user = User(anon_key=body.anon_key)
        db.add(user)
        await db.flush()
    session = ChatSession(
        user_id=user.id,
        title=body.title,
        provider=settings.LLM_PROVIDER,
        model=settings.OLLAMA_MODEL if settings.LLM_PROVIDER == "ollama" else settings.OPENAI_COMPAT_MODEL,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return SessionResponse(
        id=session.id, title=session.title,
        provider=session.provider, model=session.model,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
    )

@router.get("", response_model=list[SessionResponse])
async def list_sessions(anon_key: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatSession)
        .join(User, ChatSession.user_id == User.id)
        .where(User.anon_key == anon_key)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    return [SessionResponse(id=s.id, title=s.title, provider=s.provider, model=s.model,
                            created_at=s.created_at.isoformat(), updated_at=s.updated_at.isoformat())
            for s in sessions]
