"""
Lenny Growth Assistant — Pydantic API schemas (LOCKED 4.3)

All request/response models for every endpoint.
Import from here; never use untyped dicts in routers.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


# ── Shared error shape ────────────────────────────────────────────────────────
# One shape everywhere: { "error": { "code", "message", "request_id" } }

ErrorCode = Literal[
    "MODEL_UNAVAILABLE",
    "MODEL_TIMEOUT",
    "NO_RELEVANT_SOURCES",
    "DB_UNAVAILABLE",
    "MISSING_API_KEY",
    "VALIDATION_ERROR",
]


class ErrorBody(BaseModel):
    code: ErrorCode
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorBody


# ── Sessions ──────────────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    """POST /sessions body. provider/model come from server config, not the client."""
    title: str | None = Field(None, max_length=120)


class SessionOut(BaseModel):
    id: UUID
    title: str
    provider: str
    model: str
    created_at: datetime
    updated_at: datetime


class Citation(BaseModel):
    """One source reference attached to an assistant message."""
    episode_id: UUID
    title: str
    guest: str | None
    chunk_id: UUID
    score: float


class MessageOut(BaseModel):
    id: UUID
    role: Literal["user", "assistant"]
    content: str
    citations: list[Citation]
    created_at: datetime


class ArtifactSummary(BaseModel):
    """Returned inside session detail and as the SSE artifact event."""
    id: UUID
    type: Literal["markdown", "html"]
    title: str
    created_at: datetime


class SessionDetail(BaseModel):
    """GET /sessions/{id} — full session with messages and artifacts."""
    session: SessionOut
    messages: list[MessageOut]
    artifacts: list[ArtifactSummary]


# ── Messages ──────────────────────────────────────────────────────────────────

class MessageCreate(BaseModel):
    """POST /sessions/{id}/messages body."""
    content: str = Field(min_length=1, max_length=4000)


# ── Artifacts ─────────────────────────────────────────────────────────────────

class ArtifactOut(ArtifactSummary):
    """GET /artifacts/{id} — full artifact with raw content."""
    session_id: UUID
    message_id: UUID | None
    content: str  # stored raw; sanitized at render time


# ── Config ────────────────────────────────────────────────────────────────────

class ProviderInfo(BaseModel):
    provider: str
    model: str
    configured: bool  # False if required key/URL is missing


class ProvidersOut(BaseModel):
    """GET /config/providers"""
    active: ProviderInfo
    available: list[ProviderInfo]


# ── Admin ─────────────────────────────────────────────────────────────────────

class IngestResult(BaseModel):
    """POST /admin/ingest response (after job completes or from background task)."""
    episodes_new: int
    episodes_updated: int
    episodes_skipped: int
    chunks_added: int


# ── Health ────────────────────────────────────────────────────────────────────

class ReadyOut(BaseModel):
    """GET /health/ready"""
    status: Literal["ok", "degraded"]
    checks: dict[str, str]  # keys: db, ollama, index → "ok" | error text


# ── SSE stream events (POST /sessions/{id}/messages) ─────────────────────────
#
# Each SSE event has a named type and JSON data field.
#
# Event       │ Data shape                                  │ UI use
# ────────────┼─────────────────────────────────────────────┼──────────────────
# status      │ {"stage": "retrieving" | "generating"}      │ progress indicator
# token       │ {"text": "..."}                             │ streaming text
# citations   │ [Citation, ...]                             │ source chips
# artifact    │ ArtifactSummary                             │ opens viewer
# done        │ {"message_id": "...", "no_sources": false}  │ ends the stream
# error       │ ErrorBody                                   │ friendly error msg
#
# NO_RELEVANT_SOURCES is NOT an HTTP error — it's a normal "done" event with
# no_sources=True. The assistant streams a clear refusal reply first.
# This keeps refusal rate measurable (plan success metric ≥ 90%).
#
# Error code → HTTP status mapping:
#   VALIDATION_ERROR    → 422
#   MODEL_UNAVAILABLE   → 503
#   MODEL_TIMEOUT       → 504
#   DB_UNAVAILABLE      → 503
#   MISSING_API_KEY     → 503
#   NO_RELEVANT_SOURCES → logged only, not an HTTP error

class SSEStatusData(BaseModel):
    stage: Literal["retrieving", "generating"]

class SSETokenData(BaseModel):
    text: str

class SSEDoneData(BaseModel):
    message_id: UUID
    no_sources: bool = False
