"""
Agent router — stub implementation for Phase 2.
Routes user messages to the appropriate skill (RAG, Ship30, Artifact).
Full implementation in Phase 4.
"""

from typing import AsyncGenerator
from uuid import UUID
import structlog

logger = structlog.get_logger()


async def route_message(
    user_message: str,
    history: list[dict],
    session_id: UUID,
) -> AsyncGenerator[dict, None]:
    """
    Route a user message to the appropriate skill and yield SSE events.
    
    Stub implementation — returns a placeholder response.
    Will be replaced with actual LLM + RAG integration in Phase 4.
    """
    logger.info("routing_message", message_preview=user_message[:100], session_id=str(session_id))

    # Stub: echo back a placeholder response
    yield {"type": "skill", "skill": "rag"}
    
    response = (
        f"🚧 **Agent layer not yet connected** (Phase 4).\n\n"
        f"Your message: *\"{user_message[:200]}\"*\n\n"
        f"This will be replaced with a grounded RAG response from Lenny's transcripts."
    )
    
    yield {"type": "text", "content": response}
    yield {"type": "sources", "sources": []}
