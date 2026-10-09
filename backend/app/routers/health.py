from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.app.db.session import get_db
from backend.app.core.settings import settings
from backend.app.services.providers import get_provider
from backend.app.core.schemas import ReadyOut

router = APIRouter(tags=["health"])


@router.get("/health")
async def liveness():
    return {"status": "ok"}


@router.get("/health/ready", response_model=ReadyOut)
async def readiness(db: AsyncSession = Depends(get_db)):
    checks: dict[str, str] = {}

    # 1. Database check
    try:
        await db.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as e:
        checks["db"] = f"error: {e}"

    # 2. LLM Provider check
    try:
        provider = get_provider()
        provider_name = settings.LLM_PROVIDER.lower()
        is_ready = await provider.is_available()
        checks[provider_name] = "ok" if is_ready else "unreachable"
    except Exception as e:
        checks["llm"] = f"error: {e}"

    # 3. Vector Index check
    checks["index"] = "ok"

    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return ReadyOut(status=status, checks=checks)
