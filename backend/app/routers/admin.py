from fastapi import APIRouter, BackgroundTasks

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/ingest")
async def trigger_ingest(background_tasks: BackgroundTasks):
    # TODO: wire to ingestion service
    background_tasks.add_task(_run_ingest)
    return {"status": "ingestion started"}

async def _run_ingest():
    pass  # replaced by services/retrieval/ingest.py
