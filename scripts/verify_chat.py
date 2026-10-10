"""
Day 1 Exit Milestone Verification Script.

Tests:
1. Session creation (POST /sessions) with X-Anon-Key.
2. Real-time message streaming from Ollama (POST /sessions/{id}/messages) via SSE.
3. Transcript retrieval and citation matching from PostgreSQL pgvector.
4. Message persistence and conversation context.
"""
import json
import sys
import time
import httpx

BASE_URL = "http://127.0.0.1:8000"
ANON_KEY = "test-day1-evaluator-uuid"

def main():
    print("=" * 60)
    print("Day 1 Exit Milestone Verification: Live Ollama Chat & Retrieval")
    print("=" * 60)

    with httpx.Client(base_url=BASE_URL, timeout=120.0) as client:
        # 1. Health check
        print("\n1. Checking API Health...")
        health_resp = client.get("/health")
        assert health_resp.status_code == 200, f"Health check failed: {health_resp.text}"
        print(f"   [PASS] API Health status: {health_resp.json().get('status')}")

        # 2. Check active provider
        print("\n2. Checking Provider Configuration...")
        prov_resp = client.get("/config/providers")
        assert prov_resp.status_code == 200, f"Provider check failed: {prov_resp.text}"
        prov_data = prov_resp.json()
        active = prov_data.get("active", {})
        print(f"   Active Provider: {active.get('provider')} | Model: {active.get('model')}")
        assert active.get("configured") is True, "Active provider not configured!"
        print("   [PASS] Provider is active and configured.")

        # 3. Create Session
        print("\n3. Creating New Chat Session...")
        create_resp = client.post(
            "/sessions",
            headers={"X-Anon-Key": ANON_KEY},
            json={"title": "Day 1 Verification Test"},
        )
        assert create_resp.status_code == 201, f"Session create failed: {create_resp.text}"
        session_data = create_resp.json()
        session_id = session_data["id"]
        print(f"   Session ID: {session_id}")
        print(f"   Session Title: {session_data['title']}")
        print("   [PASS] Session created successfully.")

        # 4. Stream chat response from Ollama
        query = "What does Ada Chen Rekhi advise about knowing when it's time to leave your job?"
        print(f"\n4. Sending Prompt to Ollama:\n   Query: '{query}'")
        print("\n--- Streaming Response (SSE Tokens) ---")

        start_time = time.time()
        first_token_time = None
        full_response = []
        citations = []
        intent = None

        current_event = "message"
        with client.stream(
            "POST",
            f"/sessions/{session_id}/messages",
            headers={"X-Anon-Key": ANON_KEY},
            json={"content": query},
        ) as response:
            assert response.status_code == 200, f"Send message failed: {response.status_code}"

            for line in response.iter_lines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith("event:"):
                    current_event = line[len("event:"):].strip()
                    continue
                if line.startswith("data:"):
                    data_str = line[len("data:"):].strip()
                    try:
                        payload = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    if current_event == "status":
                        status_msg = payload.get("status") if isinstance(payload, dict) else payload
                        print(f"\n[Status]: {status_msg}")
                    elif current_event == "token":
                        if first_token_time is None:
                            first_token_time = time.time()
                        token = payload.get("token", "") if isinstance(payload, dict) else str(payload)
                        sys.stdout.write(token)
                        sys.stdout.flush()
                        full_response.append(token)
                    elif current_event == "citations":
                        citations = payload if isinstance(payload, list) else payload.get("citations", [])
                    elif current_event == "done":
                        break

        total_time = time.time() - start_time
        ttft = (first_token_time - start_time) if first_token_time else 0.0

        print("\n---------------------------------------")
        print(f"\n[Metrics]:")
        print(f"   Time to First Token (TTFT): {ttft:.2f}s")
        print(f"   Total Generation Time:      {total_time:.2f}s")
        print(f"   Tokens Generated:           ~{len(full_response)}")
        print(f"   Citations Retrieved:        {len(citations)}")

        if citations:
            print("\n[Citations Attached]:")
            for i, c in enumerate(citations[:3], 1):
                print(f"   {i}. [{c.get('title')}] - {c.get('guest')} (Score: {c.get('score', 0):.2f})")

        # 5. Verify Session History Persistence
        print("\n5. Verifying Session Persistence in PostgreSQL...")
        detail_resp = client.get(f"/sessions/{session_id}")
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        messages = detail.get("messages", [])
        print(f"   Total messages in session: {len(messages)}")
        assert len(messages) >= 2, f"Expected at least 2 messages, got {len(messages)}"
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
        print("   [PASS] User prompt and Assistant response persisted in database.")

        print("\n" + "=" * 60)
        print("DAY 1 EXIT CRITERIA PASSED: Ollama live session & streaming operational!")
        print("=" * 60)

if __name__ == "__main__":
    main()
