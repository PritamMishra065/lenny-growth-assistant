"""
Health check endpoint.
"""

from fastapi import APIRouter
from app.db.database import check_db_health
from app.db.models import HealthResponse
from app.config import settings
import httpx
import structlog

logger = structlog.get_logger()
router = APIRouter()


async def check_ollama_health() -> bool:
    """Check if Ollama is accessible."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False


async def check_llm_available() -> bool:
    """Check if the configured LLM provider is available."""
    if settings.LLM_PROVIDER == "ollama":
        return await check_ollama_health()
    elif settings.LLM_PROVIDER == "anthropic":
        return bool(settings.ANTHROPIC_API_KEY)
    elif settings.LLM_PROVIDER == "openai":
        return bool(settings.OPENAI_API_KEY)
    return False


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint returning status of all subsystems."""
    db_healthy = await check_db_health()
    llm_available = await check_llm_available()

    # ChromaDB is embedded, so it's always available if the app is running
    vector_store_healthy = True

    overall_status = "healthy" if (db_healthy and llm_available) else "degraded"

    logger.info(
        "health_check",
        status=overall_status,
        database=db_healthy,
        llm_available=llm_available,
        llm_provider=settings.LLM_PROVIDER,
    )

    return HealthResponse(
        status=overall_status,
        database=db_healthy,
        vector_store=vector_store_healthy,
        llm_provider=settings.LLM_PROVIDER,
        llm_available=llm_available,
    )
