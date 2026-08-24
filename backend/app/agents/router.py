"""
Agent Router — Intelligent intent classification and skill dispatch.
Routes queries to RAG Conversational Skill, Ship 30 for 30 Skill, or Artifact Skill.
"""

from typing import AsyncGenerator
from uuid import UUID
import structlog
from app.agents.rag_skill import execute_rag_skill
from app.agents.ship30_skill import execute_ship30_skill
from app.agents.artifact_skill import execute_artifact_skill

logger = structlog.get_logger()


def classify_intent(message: str) -> str:
    """Classify the user intent to select the appropriate agent skill."""
    msg = message.lower().strip()

    # Ship 30 for 30 intent
    ship30_keywords = [
        "ship 30", "ship30", "atomic essay", "write an essay", "write essay",
        "essay on", "publishable essay", "write an article", "write article",
        "long-form essay", "essay format", "digital essay"
    ]
    if any(kw in msg for kw in ship30_keywords):
        return "ship30"

    # Artifact generation intent
    artifact_keywords = [
        "artifact", "html", "css", "prd", "calculator", "widget", "template",
        "playbook", "cheat sheet", "strategy memo", "scorecard", "framework doc",
        "interactive component", "mockup"
    ]
    if any(kw in msg for kw in artifact_keywords):
        return "artifact"

    # Default to grounded RAG conversational assistant
    return "rag"


async def route_message(
    user_message: str,
    history: list[dict],
    session_id: UUID,
) -> AsyncGenerator[dict, None]:
    """
    Route a user message to the appropriate skill and yield streaming events.
    
    Events yielded:
    - {"type": "skill", "skill": "rag"|"ship30"|"artifact"}
    - {"type": "sources", "sources": [...]}
    - {"type": "text", "content": "..."}
    - {"type": "artifact", "artifact": {...}} (optional)
    """
    skill = classify_intent(user_message)
    logger.info("dispatching_skill", skill=skill, session_id=str(session_id), query_preview=user_message[:80])

    # Announce the active skill to the stream
    yield {"type": "skill", "skill": skill}

    if skill == "ship30":
        async for event in execute_ship30_skill(user_message, history):
            yield event
    elif skill == "artifact":
        async for event in execute_artifact_skill(user_message, history):
            yield event
    else:
        async for event in execute_rag_skill(user_message, history):
            yield event
