from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.app.db.session import get_db
from backend.app.core.settings import settings
import httpx

router = APIRouter(tags=["health"])

@router.get("/health")
async def liveness():
    return {"status": "ok"}

@router.get("/health/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    checks = {}
    # DB
    try:
        await db.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as e:
        checks["db"] = f"error: {e}"
    # Ollama
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            checks["ollama"] = "ok" if r.status_code == 200 else f"status {r.status_code}"
    except Exception as e:
        checks["ollama"] = f"error: {e}"

    ready = all(v == "ok" for v in checks.values())
    return {"ready": ready, "checks": checks}
