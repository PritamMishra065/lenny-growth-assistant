"""
Model configuration endpoints — switch LLM provider at runtime.
"""

from fastapi import APIRouter, HTTPException
from app.db.models import ModelConfig, ModelConfigUpdate
from app.config import settings
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/config", tags=["config"])


def get_available_providers() -> list[dict]:
    """Get list of available LLM providers with their status."""
    providers = [
        {
            "id": "gemini",
            "name": "Google Gemini",
            "model": settings.GEMINI_MODEL,
            "configured": bool(settings.GEMINI_API_KEY),
        },
        {
            "id": "ollama",
            "name": "Ollama (Local)",
            "model": settings.OLLAMA_MODEL,
            "configured": True,
        },
        {
            "id": "anthropic",
            "name": "Anthropic Claude",
            "model": settings.ANTHROPIC_MODEL,
            "configured": bool(settings.ANTHROPIC_API_KEY),
        },
        {
            "id": "openai",
            "name": "OpenAI",
            "model": settings.OPENAI_MODEL,
            "configured": bool(settings.OPENAI_API_KEY),
        },
    ]
    return providers


@router.get("/model", response_model=ModelConfig)
async def get_model_config():
    """Get current active model configuration."""
    current_model = getattr(settings, f"{settings.LLM_PROVIDER.upper()}_MODEL", "unknown")
    return ModelConfig(
        provider=settings.LLM_PROVIDER,
        model=current_model,
        available_providers=get_available_providers(),
    )


@router.put("/model", response_model=ModelConfig)
async def update_model_config(body: ModelConfigUpdate):
    """Switch the active LLM provider."""
    provider = body.provider.lower()

    if provider == "gemini" and not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="Gemini API key not configured. Set GEMINI_API_KEY in .env"
        )
    if provider == "anthropic" and not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="Anthropic API key not configured. Set ANTHROPIC_API_KEY in .env"
        )
    if provider == "openai" and not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="OpenAI API key not configured. Set OPENAI_API_KEY in .env"
        )

    settings.LLM_PROVIDER = provider
    if body.model:
        attr_name = f"{provider.upper()}_MODEL"
        if hasattr(settings, attr_name):
            setattr(settings, attr_name, body.model)

    current_model = getattr(settings, f"{settings.LLM_PROVIDER.upper()}_MODEL", "unknown")

    logger.info(
        "model_config_updated",
        provider=settings.LLM_PROVIDER,
        model=current_model,
    )

    return ModelConfig(
        provider=settings.LLM_PROVIDER,
        model=current_model,
        available_providers=get_available_providers(),
    )
