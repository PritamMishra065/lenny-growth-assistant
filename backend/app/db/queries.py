"""
SQL query functions for sessions and messages.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from uuid import UUID
from typing import Optional
import json


# ─── Sessions ───────────────────────────────────────────

async def create_session(db: AsyncSession, title: str = "New Chat", model_provider: str = "ollama", model_name: str = "llama3.1:8b") -> dict:
    result = await db.execute(
        text("""
            INSERT INTO sessions (title, model_provider, model_name)
            VALUES (:title, :model_provider, :model_name)
            RETURNING id, title, created_at, updated_at, model_provider, model_name, metadata
        """),
        {"title": title, "model_provider": model_provider, "model_name": model_name}
    )
    await db.commit()
    row = result.mappings().one()
    return dict(row) | {"message_count": 0}


async def get_sessions(db: AsyncSession) -> list[dict]:
    result = await db.execute(
        text("""
            SELECT s.id, s.title, s.created_at, s.updated_at, s.model_provider, s.model_name, s.metadata,
                   COALESCE(COUNT(m.id), 0)::int AS message_count
            FROM sessions s
            LEFT JOIN messages m ON m.session_id = s.id
            GROUP BY s.id
            ORDER BY s.updated_at DESC
        """)
    )
    return [dict(row) for row in result.mappings().all()]


async def get_session(db: AsyncSession, session_id: UUID) -> Optional[dict]:
    result = await db.execute(
        text("""
            SELECT s.id, s.title, s.created_at, s.updated_at, s.model_provider, s.model_name, s.metadata,
                   COALESCE(COUNT(m.id), 0)::int AS message_count
            FROM sessions s
            LEFT JOIN messages m ON m.session_id = s.id
            WHERE s.id = :session_id
            GROUP BY s.id
        """),
        {"session_id": str(session_id)}
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def delete_session(db: AsyncSession, session_id: UUID) -> bool:
    result = await db.execute(
        text("DELETE FROM sessions WHERE id = :session_id"),
        {"session_id": str(session_id)}
    )
    await db.commit()
    return result.rowcount > 0


async def update_session_title(db: AsyncSession, session_id: UUID, title: str) -> Optional[dict]:
    result = await db.execute(
        text("""
            UPDATE sessions SET title = :title, updated_at = NOW()
            WHERE id = :session_id
            RETURNING id, title, created_at, updated_at, model_provider, model_name, metadata
        """),
        {"session_id": str(session_id), "title": title}
    )
    await db.commit()
    row = result.mappings().first()
    return dict(row) if row else None


async def update_session_timestamp(db: AsyncSession, session_id: UUID):
    await db.execute(
        text("UPDATE sessions SET updated_at = NOW() WHERE id = :session_id"),
        {"session_id": str(session_id)}
    )
    await db.commit()


# ─── Messages ──────────────────────────────────────────

async def create_message(
    db: AsyncSession,
    session_id: UUID,
    role: str,
    content: str,
    sources: list = None,
    artifact: dict = None,
    skill_used: str = None,
    model_provider: str = None,
    model_name: str = None,
    tokens_used: int = None,
    latency_ms: int = None,
) -> dict:
    result = await db.execute(
        text("""
            INSERT INTO messages (session_id, role, content, sources, artifact, skill_used,
                                  model_provider, model_name, tokens_used, latency_ms)
            VALUES (:session_id, :role, :content, CAST(:sources AS jsonb), CAST(:artifact AS jsonb), :skill_used,
                    :model_provider, :model_name, :tokens_used, :latency_ms)
            RETURNING id, session_id, role, content, sources, artifact, skill_used,
                      model_provider, model_name, tokens_used, latency_ms, created_at
        """),
        {
            "session_id": str(session_id),
            "role": role,
            "content": content,
            "sources": json.dumps(sources or []),
            "artifact": json.dumps(artifact) if artifact else None,
            "skill_used": skill_used,
            "model_provider": model_provider,
            "model_name": model_name,
            "tokens_used": tokens_used,
            "latency_ms": latency_ms,
        }
    )
    await db.commit()
    row = result.mappings().one()
    return dict(row)


async def get_messages(db: AsyncSession, session_id: UUID) -> list[dict]:
    result = await db.execute(
        text("""
            SELECT id, session_id, role, content, sources, artifact, skill_used,
                   model_provider, model_name, tokens_used, latency_ms, created_at
            FROM messages
            WHERE session_id = :session_id
            ORDER BY created_at ASC
        """),
        {"session_id": str(session_id)}
    )
    return [dict(row) for row in result.mappings().all()]


async def get_session_history(db: AsyncSession, session_id: UUID, limit: int = 20) -> list[dict]:
    """Get recent messages for context building."""
    result = await db.execute(
        text("""
            SELECT role, content FROM messages
            WHERE session_id = :session_id
            ORDER BY created_at DESC
            LIMIT :limit
        """),
        {"session_id": str(session_id), "limit": limit}
    )
    rows = [dict(row) for row in result.mappings().all()]
    rows.reverse()  # Chronological order
    return rows
