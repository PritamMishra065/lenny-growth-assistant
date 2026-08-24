"""
Session CRUD endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.database import get_db
from app.db.models import SessionCreate, SessionResponse, SessionListResponse
from app.db import queries
from app.config import settings
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(body: SessionCreate = SessionCreate(), db: AsyncSession = Depends(get_db)):
    """Create a new chat session."""
    session = await queries.create_session(
        db,
        title=body.title or "New Chat",
        model_provider=settings.LLM_PROVIDER,
        model_name=getattr(settings, f"{settings.LLM_PROVIDER.upper()}_MODEL", "unknown"),
    )
    logger.info("session_created", session_id=str(session["id"]))
    return SessionResponse(**session)


@router.get("", response_model=SessionListResponse)
async def list_sessions(db: AsyncSession = Depends(get_db)):
    """List all sessions ordered by most recently updated."""
    sessions = await queries.get_sessions(db)
    return SessionListResponse(
        sessions=[SessionResponse(**s) for s in sessions],
        total=len(sessions),
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a specific session by ID."""
    session = await queries.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(**session)


@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a session and all its messages."""
    deleted = await queries.delete_session(db, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    logger.info("session_deleted", session_id=str(session_id))


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(session_id: UUID, body: SessionCreate, db: AsyncSession = Depends(get_db)):
    """Update session title."""
    session = await queries.update_session_title(db, session_id, body.title)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(**session, message_count=0)
