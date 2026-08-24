"""
Ingestion API — list, ingest, and manage transcript episodes.
"""

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from app.services.ingestion import (
    list_available_episodes,
    ingest_episodes,
    check_ingestion_status,
    clear_collection,
)
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/ingestion", tags=["ingestion"])


class IngestRequest(BaseModel):
    slugs: Optional[list[str]] = None  # Specific episode slugs to ingest
    ingest_all: bool = False            # Set True to ingest everything


class IngestResponse(BaseModel):
    status: str
    message: str = ""
    episodes: int = 0
    chunks: int = 0
    errors: int = 0
    skipped: int = 0


@router.get("/episodes")
async def get_available_episodes():
    """List all available episodes that can be ingested."""
    episodes = list_available_episodes()
    return {
        "episodes": episodes,
        "total": len(episodes),
    }


@router.get("/status")
async def get_ingestion_status():
    """Check current ingestion status — how many chunks/episodes are indexed."""
    return check_ingestion_status()


@router.post("/ingest", response_model=IngestResponse)
async def ingest(body: IngestRequest):
    """
    Ingest selected episodes into the vector store.
    
    - Send `{"slugs": ["brian-chesky", "marty-cagan"]}` to ingest specific episodes.
    - Send `{"ingest_all": true}` to ingest all available episodes.
    """
    result = await ingest_episodes(slugs=body.slugs, ingest_all=body.ingest_all)
    return IngestResponse(**result)


@router.delete("/clear")
async def clear():
    """Clear all ingested data (delete the vector store collection)."""
    return clear_collection()
