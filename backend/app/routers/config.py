from fastapi import APIRouter
from backend.app.core.settings import settings

router = APIRouter(prefix="/config", tags=["config"])

@router.get("/providers")
async def get_providers():
    active = {
        "provider": settings.LLM_PROVIDER,
        "model": settings.OLLAMA_MODEL if settings.LLM_PROVIDER == "ollama" else settings.OPENAI_COMPAT_MODEL,
        "base_url": settings.OLLAMA_BASE_URL if settings.LLM_PROVIDER == "ollama" else settings.OPENAI_COMPAT_BASE_URL,
    }
    available = ["ollama"]
    if settings.OPENAI_COMPAT_API_KEY:
        available.append("openai_compatible")
    return {"active": active, "available": available}
