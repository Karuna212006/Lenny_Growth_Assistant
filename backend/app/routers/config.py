from fastapi import APIRouter
from backend.app.core.settings import settings
from backend.app.core.schemas import ProvidersOut, ProviderInfo

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/providers", response_model=ProvidersOut)
async def get_providers():
    is_ollama = settings.LLM_PROVIDER.lower() == "ollama"
    active_info = ProviderInfo(
        provider=settings.LLM_PROVIDER,
        model=settings.OLLAMA_MODEL if is_ollama else settings.OPENAI_COMPAT_MODEL,
        configured=True if is_ollama else bool(settings.OPENAI_COMPAT_API_KEY and settings.OPENAI_COMPAT_BASE_URL),
    )
    available = [
        ProviderInfo(
            provider="ollama",
            model=settings.OLLAMA_MODEL,
            configured=True,
        ),
        ProviderInfo(
            provider="openai_compatible",
            model=settings.OPENAI_COMPAT_MODEL or "openai-compatible",
            configured=bool(settings.OPENAI_COMPAT_API_KEY and settings.OPENAI_COMPAT_BASE_URL),
        ),
    ]
    return ProvidersOut(active=active_info, available=available)
