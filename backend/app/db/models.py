"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


# ─── Sessions ───────────────────────────────────────────

class SessionCreate(BaseModel):
    title: Optional[str] = "New Chat"


class SessionResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    model_provider: str
    model_name: str
    message_count: Optional[int] = 0

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int


# ─── Messages ──────────────────────────────────────────

class SourceReference(BaseModel):
    episode: str = ""
    guest: str = ""
    url: str = ""
    excerpt: str = ""


class ArtifactData(BaseModel):
    type: str = "markdown"  # "markdown" or "html"
    content: str = ""
    title: str = ""


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    model_override: Optional[str] = None  # Override session default model


class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    sources: list[SourceReference] = []
    artifact: Optional[ArtifactData] = None
    skill_used: Optional[str] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    tokens_used: Optional[int] = None
    latency_ms: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageListResponse(BaseModel):
    messages: list[MessageResponse]
    total: int


# ─── Config ────────────────────────────────────────────

class ModelConfig(BaseModel):
    provider: str
    model: str
    available_providers: list[dict] = []


class ModelConfigUpdate(BaseModel):
    provider: str = Field(..., pattern="^(ollama|gemini|anthropic|openai)$")
    model: Optional[str] = None
    api_key: Optional[str] = None


# ─── Errors ────────────────────────────────────────────

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict = {}


class ErrorResponse(BaseModel):
    error: ErrorDetail


# ─── Health ────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    database: bool
    vector_store: bool
    llm_provider: str
    llm_available: bool
    version: str = "0.1.0"
