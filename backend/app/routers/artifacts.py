from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from backend.app.db.session import get_db
from backend.app.db.models import Artifact

router = APIRouter(prefix="/artifacts", tags=["artifacts"])

@router.get("/{artifact_id}")
async def get_artifact(artifact_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Artifact).where(Artifact.id == artifact_id))
    artifact = result.scalar_one_or_none()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {"id": artifact.id, "type": artifact.type, "title": artifact.title,
            "content": artifact.content, "created_at": artifact.created_at.isoformat()}
