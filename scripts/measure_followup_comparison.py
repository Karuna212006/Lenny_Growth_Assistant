import asyncio
import time
import sys
from pathlib import Path
from statistics import median
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.agents.orchestrator import run_agent_pipeline
from backend.app.services.providers import get_provider
from backend.app.db.session import async_session_factory

HISTORY = [
    {"role": "user", "content": "What did Ada Chen Rekhi advise about career growth?"},
    {"role": "assistant", "content": "Ada Chen Rekhi advised exploring and exploiting different modes in your early career."},
]
FOLLOW_UP_PROMPT = "Can you elaborate on her advice about knowing when to leave your job?"

async def measure_single_run(use_tool_loop: bool) -> tuple[float, list[str]]:
    provider = get_provider("ollama")
    events = []
    first_token_time = None
    start_time = time.perf_counter()

    async with async_session_factory() as db:
        if use_tool_loop:
            gen = run_agent_pipeline(FOLLOW_UP_PROMPT, history=HISTORY, provider=provider, db=db)
            async for item in gen:
                events.append(item.get("event"))
                if item.get("event") == "token" and first_token_time is None:
                    first_token_time = time.perf_counter() - start_time
        else:
            # Bypass tool loop: patch invoke_retrieval_tool_agent to directly call search_transcripts
            from backend.app.services.retrieval.search import search_transcripts
            with patch("backend.app.agents.orchestrator.invoke_retrieval_tool_agent", new=search_transcripts):
                gen = run_agent_pipeline(FOLLOW_UP_PROMPT, history=HISTORY, provider=provider, db=db)
                async for item in gen:
                    events.append(item.get("event"))
                    if item.get("event") == "token" and first_token_time is None:
                        first_token_time = time.perf_counter() - start_time

    ttft = first_token_time or (time.perf_counter() - start_time)
    return ttft, events

async def main():
    print("=" * 80)
    print("1e.5 Follow-up Latency: (a) Tool Loop vs (b) Rewriter Only")
    print("=" * 80)

    # 1. Measure (a) Tool Loop (5 runs)
    print("\nMeasuring (a) Tool Loop over 5 runs...")
    tool_times = []
    for i in range(1, 6):
        t, evs = await measure_single_run(use_tool_loop=True)
        tool_times.append(t)
        has_status = "status" in evs
        print(f"  Run {i}: TTFT = {t:.3f}s (events seen: {set(evs)}, status emitted: {has_status})")

    # 2. Measure (b) Rewriter Only (5 runs)
    print("\nMeasuring (b) Rewriter Only over 5 runs...")
    rewriter_times = []
    for i in range(1, 6):
        t, evs = await measure_single_run(use_tool_loop=False)
        rewriter_times.append(t)
        print(f"  Run {i}: TTFT = {t:.3f}s (events seen: {set(evs)})")

    med_tool = median(tool_times)
    med_rewriter = median(rewriter_times)

    print("\n" + "=" * 80)
    print("Summary Latency Comparison:")
    print(f"  (a) Follow-up with Tool Loop:     Median TTFT = {med_tool:.3f}s (Runs: {[round(x, 2) for x in tool_times]})")
    print(f"  (b) Follow-up with Rewriter Only: Median TTFT = {med_rewriter:.3f}s (Runs: {[round(x, 2) for x in rewriter_times]})")
    print(f"  Overhead of tool loop:            {med_tool - med_rewriter:+.3f}s")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
