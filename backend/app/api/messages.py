"""
Message and chat endpoints — including streaming SSE responses.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import json
import time

from app.db.database import get_db
from app.db.models import MessageCreate, MessageResponse, MessageListResponse
from app.db import queries
from app.config import settings
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/sessions/{session_id}/messages", tags=["messages"])


@router.get("", response_model=MessageListResponse)
async def get_messages(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get all messages in a session."""
    # Verify session exists
    session = await queries.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = await queries.get_messages(db, session_id)
    return MessageListResponse(
        messages=[MessageResponse(**m) for m in messages],
        total=len(messages),
    )


@router.post("")
async def send_message(session_id: UUID, body: MessageCreate, db: AsyncSession = Depends(get_db)):
    """
    Send a user message and stream the assistant's response via SSE.
    """
    # Verify session exists
    session = await queries.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    start_time = time.time()

    # Save user message
    await queries.create_message(
        db,
        session_id=session_id,
        role="user",
        content=body.content,
    )

    # Update session timestamp
    await queries.update_session_timestamp(db, session_id)

    # Auto-title the session from the first message
    if session.get("message_count", 0) == 0:
        title = body.content[:80] + ("..." if len(body.content) > 80 else "")
        await queries.update_session_title(db, session_id, title)

    async def generate_sse():
        """Generate SSE stream for the assistant's response."""
        try:
            from app.agents.router import route_message
            from app.db.database import async_session

            full_content = ""
            sources = []
            artifact = None
            skill_used = None
            model_provider = settings.LLM_PROVIDER
            model_name = getattr(settings, f"{settings.LLM_PROVIDER.upper()}_MODEL", "unknown")

            # Get session history with a fresh DB session
            async with async_session() as db_session:
                history = await queries.get_session_history(db_session, session_id)

            # Route to appropriate skill and stream response
            async for event in route_message(body.content, history, session_id):
                event_type = event.get("type", "text")

                if event_type == "text":
                    chunk = event.get("content", "")
                    full_content += chunk
                    yield f"event: chunk\ndata: {json.dumps({'type': 'text', 'content': chunk})}\n\n"

                elif event_type == "sources":
                    sources = event.get("sources", [])
                    yield f"event: sources\ndata: {json.dumps({'sources': sources})}\n\n"

                elif event_type == "artifact":
                    artifact = event.get("artifact", None)
                    yield f"event: artifact\ndata: {json.dumps(artifact)}\n\n"

                elif event_type == "skill":
                    skill_used = event.get("skill", None)

                elif event_type == "error":
                    yield f"event: error\ndata: {json.dumps({'error': event.get('message', 'Unknown error')})}\n\n"
                    return

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Save assistant message with a fresh DB session
            async with async_session() as db_session:
                saved_msg = await queries.create_message(
                    db_session,
                    session_id=session_id,
                    role="assistant",
                    content=full_content,
                    sources=sources,
                    artifact=artifact,
                    skill_used=skill_used,
                    model_provider=model_provider,
                    model_name=model_name,
                    latency_ms=latency_ms,
                )

            # Send done event
            yield f"event: done\ndata: {json.dumps({'message_id': str(saved_msg['id']), 'skill_used': skill_used, 'latency_ms': latency_ms})}\n\n"

            logger.info(
                "chat_response",
                session_id=str(session_id),
                skill=skill_used,
                model=model_name,
                provider=model_provider,
                latency_ms=latency_ms,
            )

        except Exception as e:
            logger.error("chat_response_error", error=str(e), session_id=str(session_id))
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
