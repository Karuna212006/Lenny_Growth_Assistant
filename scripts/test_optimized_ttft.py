import asyncio
import time
import statistics
from uuid import uuid4
from unittest.mock import AsyncMock, patch
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.agents.orchestrator import run_agent_pipeline
from backend.app.services.providers.ollama import OllamaProvider
from backend.app.services.retrieval.search import RetrievedChunk

query = "What did Ada Chen Rekhi advise about knowing when it's time to leave your job?"
canned_chunks = [
    RetrievedChunk(
        chunk_id=uuid4(),
        episode_id=uuid4(),
        episode_title="Knowing When It Is Time to Leave Your Job",
        guest="Ada Chen Rekhi",
        source_path="episodes/ada-chen-rekhi/transcript.md",
        chunk_index=1,
        text="On curiosity loops and contextual advice.",
        speaker="Ada Chen Rekhi",
        start_time="00:15:30",
        score=0.91,
    )
]

async def measure():
    provider = OllamaProvider()
    db_mock = AsyncMock()
    times = []
    with patch("backend.app.agents.orchestrator.search_transcripts", return_value=canned_chunks):
        for i in range(1, 6):
            t0 = time.time()
            ttft = None
            async for item in run_agent_pipeline(query, history=[], provider=provider, db=db_mock):
                if item["event"] == "token" and ttft is None:
                    ttft = time.time() - t0
                    break
            times.append(ttft or (time.time() - t0))
            print(f"Optimized Run {i}: {times[-1]:.2f}s")
    print(f"Median Optimized TTFT: {statistics.median(times):.2f}s")

if __name__ == "__main__":
    asyncio.run(measure())
