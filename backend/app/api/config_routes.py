"""
Model configuration endpoints — switch LLM provider at runtime.
"""

from fastapi import APIRouter, HTTPException
from app.db.models import ModelConfig, ModelConfigUpdate
from app.config import settings
from app.api.health import check_ollama_health
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/config", tags=["config"])


def get_available_providers() -> list[dict]:
    """Get list of available LLM providers with their status."""
    providers = [
        {
            "id": "ollama",
            "name": "Ollama (Local)",
            "model": settings.OLLAMA_MODEL,
            "configured": True,  # Always configured, may not be running
        },
    ]

    if settings.ANTHROPIC_API_KEY:
        providers.append({
            "id": "anthropic",
            "name": "Anthropic Claude",
            "model": settings.ANTHROPIC_MODEL,
            "configured": True,
        })
    else:
        providers.append({
            "id": "anthropic",
            "name": "Anthropic Claude",
            "model": settings.ANTHROPIC_MODEL,
            "configured": False,
        })

    if settings.OPENAI_API_KEY:
        providers.append({
            "id": "openai",
            "name": "OpenAI",
            "model": settings.OPENAI_MODEL,
            "configured": True,
        })
    else:
        providers.append({
            "id": "openai",
            "name": "OpenAI",
            "model": settings.OPENAI_MODEL,
            "configured": False,
        })

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
    # Validate the provider is configured
    if body.provider == "anthropic" and not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="Anthropic API key not configured. Set ANTHROPIC_API_KEY in .env"
        )
    if body.provider == "openai" and not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="OpenAI API key not configured. Set OPENAI_API_KEY in .env"
        )

    # Update the runtime setting
    settings.LLM_PROVIDER = body.provider
    if body.model:
        attr_name = f"{body.provider.upper()}_MODEL"
        if hasattr(settings, attr_name):
            setattr(settings, attr_name, body.model)

    current_model = getattr(settings, f"{settings.LLM_PROVIDER.upper()}_MODEL", "unknown")

    logger.info(
        "model_config_updated",
        provider=body.provider,
        model=current_model,
    )

    return ModelConfig(
        provider=settings.LLM_PROVIDER,
        model=current_model,
        available_providers=get_available_providers(),
    )
