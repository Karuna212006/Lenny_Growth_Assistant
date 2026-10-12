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

canned_chunks = [
    RetrievedChunk(
        chunk_id=uuid4(),
        episode_id=uuid4(),
        episode_title="Knowing When It Is Time to Leave Your Job",
        guest="Ada Chen Rekhi",
        source_path="episodes/ada-chen-rekhi/transcript.md",
        chunk_index=1,
        text="Ada Chen Rekhi explains when it is time to leave your job. Fundamental aspects of the role can be limiting or you are not learning a lot.",
        speaker="Ada Chen Rekhi",
        start_time="00:15:30",
        score=0.91,
    )
]

standalone_query = "What did Ada Chen Rekhi advise about knowing when it's time to leave your job?"
follow_up_query = "Why did she advise that?"
history = [
    {"role": "user", "content": "What did Ada Chen Rekhi advise about knowing when it's time to leave your job?"},
    {"role": "assistant", "content": "She advised leaving when you are not learning or your values do not align."},
]

async def measure_single_ttft(query: str, hist: list[dict[str, str]]):
    provider = OllamaProvider()
    db_mock = AsyncMock()

    t_start = time.time()
    ttft = None

    with patch("backend.app.agents.orchestrator.search_transcripts", return_value=canned_chunks):
        async for item in run_agent_pipeline(query, history=hist, provider=provider, db=db_mock):
            if item["event"] == "token" and ttft is None:
                ttft = time.time() - t_start
                break

    return ttft or (time.time() - t_start)

async def main():
    print("=" * 65)
    print("Benchmarking TTFT: Request Start -> First 'token' SSE Event")
    print("=" * 65)

    # 1. Standalone Question (Tool Step Skipped)
    print("\n--- 1. Standalone Question (Skip Optimization Active) ---")
    standalone_times = []
    for i in range(1, 6):
        t = await measure_single_ttft(standalone_query, hist=[])
        standalone_times.append(t)
        print(f"Run {i}: {t:.2f}s")
    median_standalone = statistics.median(standalone_times)
    print(f"Median Standalone TTFT: {median_standalone:.2f}s")

    # 2. Follow-up Question (Agent Tool Loop Active)
    print("\n--- 2. Follow-up Question (Conversational Tool Loop Active) ---")
    followup_times = []
    for i in range(1, 6):
        t = await measure_single_ttft(follow_up_query, hist=history)
        followup_times.append(t)
        print(f"Run {i}: {t:.2f}s")
    median_followup = statistics.median(followup_times)
    print(f"Median Follow-up TTFT: {median_followup:.2f}s")

    print("\n" + "=" * 65)
    print(f"Summary:")
    print(f"Standalone TTFT (Median): {median_standalone:.2f}s")
    print(f"Follow-up TTFT (Median):  {median_followup:.2f}s")
    print(f"Tool Roundtrip Overhead: +{median_followup - median_standalone:.2f}s")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(main())
