import asyncio
import os
import sys
import time
import statistics
from uuid import uuid4
from unittest.mock import AsyncMock, patch

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
        text="The Energy & Learning Matrix tracks energy and skill acquisition across a 60-day window. If both are low for more than 4 consecutive weeks, staying becomes an active liability.",
        speaker="Ada Chen Rekhi",
        start_time="00:15:30",
        score=0.91,
    )
]

async def measure_ttft(skip_tool_call: bool):
    provider = OllamaProvider()
    db_mock = AsyncMock()

    # If skip_tool_call is True, bypass invoke_retrieval_tool_agent by patching it to return search_transcripts directly
    t0 = time.time()
    ttft = None

    if skip_tool_call:
        with patch("backend.app.agents.orchestrator.invoke_retrieval_tool_agent", return_value=canned_chunks):
            async for item in run_agent_pipeline(query, history=[], provider=provider, db=db_mock):
                if item["event"] == "token" and ttft is None:
                    ttft = time.time() - t0
                    break
    else:
        with patch("backend.app.agents.orchestrator.search_transcripts", return_value=canned_chunks):
            async for item in run_agent_pipeline(query, history=[], provider=provider, db=db_mock):
                if item["event"] == "token" and ttft is None:
                    ttft = time.time() - t0
                    break

    return ttft or (time.time() - t0)

async def main():
    print("=== Benchmarking Time to First Token (TTFT) Over 5 Runs ===")
    
    with_tool_times = []
    print("\n--- WITH Tool-Calling Step (Extra Model Round-Trip) ---")
    for i in range(1, 6):
        t = await measure_ttft(skip_tool_call=False)
        with_tool_times.append(t)
        print(f"Run {i}: {t:.2f}s")
    median_with = statistics.median(with_tool_times)
    print(f"Median WITH tool step: {median_with:.2f}s")

    without_tool_times = []
    print("\n--- WITHOUT Tool-Calling Step (Direct Vector Search) ---")
    for i in range(1, 6):
        t = await measure_ttft(skip_tool_call=True)
        without_tool_times.append(t)
        print(f"Run {i}: {t:.2f}s")
    median_without = statistics.median(without_tool_times)
    print(f"Median WITHOUT tool step: {median_without:.2f}s")

    diff = median_with - median_without
    print("\n" + "=" * 50)
    print(f"Difference (Added latency): {diff:.2f}s")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
