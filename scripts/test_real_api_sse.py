import asyncio
import json
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.db.models import Session as ChatSession, User
from backend.app.db.session import async_session_factory

async def main():
    print("=" * 80)
    print("1e.4 Real API Test: POST /sessions/{id}/messages with Real Database")
    print("=" * 80)

    # 1. Create user and session in real DB
    async with async_session_factory() as db:
        user = User(anon_key="eval-user-" + str(uuid4())[:8])
        db.add(user)
        await db.flush()

        session = ChatSession(
            user_id=user.id,
            title="Real Grounding Eval",
            provider="ollama",
            model="qwen2.5:7b-instruct",
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        session_id = str(session.id)
        anon_key = user.anon_key

    print(f"Created Session ID: {session_id} for User: {anon_key}")

    # 2. Call POST /sessions/{id}/messages via AsyncClient
    query = "What did Ada Chen Rekhi advise about knowing when it's time to leave your job?"
    payload = {"content": query}
    headers = {"X-Anon-Key": anon_key}

    print(f"\nSending Query: '{query}'")
    print("Streaming SSE Output:\n" + "-" * 60)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream(
            "POST",
            f"/sessions/{session_id}/messages",
            json=payload,
            headers=headers,
            timeout=120.0,
        ) as response:
            print(f"HTTP Status: {response.status_code}")
            full_events = []
            async for line in response.aiter_lines():
                if line:
                    print(line)
                    full_events.append(line)

    print("-" * 60)
    print("Stream Completed.")

if __name__ == "__main__":
    asyncio.run(main())
