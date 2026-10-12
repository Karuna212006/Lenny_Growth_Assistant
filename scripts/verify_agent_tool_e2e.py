import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from backend.app.agents.orchestrator import run_agent_pipeline
from backend.app.core.settings import settings
from backend.app.services.providers.ollama import OllamaProvider
from backend.app.services.retrieval.search import RetrievedChunk

# Configure logging to print tool call log lines
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(levelname)s [%(name)s] %(message)s")

async def test_e2e_agent_qa():
    print("=" * 60)
    print("Verifying Anthropic SDK Tool Calling Loop in Agent Pipeline")
    print("=" * 60)

    provider = OllamaProvider()
    db_mock = AsyncMock()

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
        ),
        RetrievedChunk(
            chunk_id=uuid4(),
            episode_id=uuid4(),
            episode_title="Knowing When It Is Time to Leave Your Job",
            guest="Ada Chen Rekhi",
            source_path="episodes/ada-chen-rekhi/transcript.md",
            chunk_index=2,
            text="Before resigning, run three diagnostic checks: exhaust internal team transfers, isolate manager vs company friction, and ensure 6 months of financial runway.",
            speaker="Ada Chen Rekhi",
            start_time="00:22:10",
            score=0.88,
        )
    ]

    prompt = "What did Ada Chen Rekhi advise about knowing when it's time to leave your job?"
    print(f"\nPrompt: '{prompt}'")
    print("\n--- Streaming SSE Events ---")

    events = []
    tokens = []
    with patch("backend.app.agents.orchestrator.search_transcripts", return_value=canned_chunks) as mock_search:
        async for item in run_agent_pipeline(
            prompt=prompt,
            history=[],
            provider=provider,
            db=db_mock,
        ):
            event_type = item["event"]
            data = item["data"]
            events.append(item)
            if event_type == "token":
                tokens.append(data["text"])
                sys.stdout.write(data["text"])
                sys.stdout.flush()
            else:
                print(f"\n[SSE EVENT: {event_type}] {data}")

    print("\n\n" + "=" * 60)
    print(f"Total tokens generated: {len(tokens)}")
    print(f"Citations emitted: {len([e for e in events if e['event'] == 'citations'])}")
    print(f"Done event: {[e for e in events if e['event'] == 'done']}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_e2e_agent_qa())
