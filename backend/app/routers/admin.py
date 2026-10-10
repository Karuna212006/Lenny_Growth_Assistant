"""
Admin Router (Step 5).

Provides endpoints for administrative actions including on-demand transcript ingestion.
"""
from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, status

from backend.app.db.session import async_session_factory
from backend.app.services.retrieval.ingest import ingest_transcripts

router = APIRouter(prefix="/admin", tags=["admin"])


async def _run_ingest_background(limit: int | None = None) -> None:
    transcripts_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "transcripts"
    async with async_session_factory() as db:
        await ingest_transcripts(transcripts_dir=transcripts_dir, db=db, limit=limit)


@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def trigger_ingest(
    background_tasks: BackgroundTasks,
    limit: int | None = None,
):
    """Trigger background transcript ingestion."""
    background_tasks.add_task(_run_ingest_background, limit=limit)
    return {
        "status": "ingestion started",
        "message": "Transcript ingestion job dispatched to background.",
    }
