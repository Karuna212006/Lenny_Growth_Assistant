import json
import os
import sys
import time
from anthropic import Anthropic

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from backend.app.core.settings import settings

CANNED_CHUNKS = [
    {
        "guest": "Ada Chen Rekhi",
        "title": "Knowing When It Is Time to Leave Your Job",
        "text": "The Energy & Learning Matrix tracks energy and skill acquisition across a 60-day window. If both are low for more than 4 consecutive weeks, staying becomes an active liability."
    },
    {
        "guest": "Ada Chen Rekhi",
        "title": "Knowing When It Is Time to Leave Your Job",
        "text": "Before resigning, run three diagnostic checks: exhaust internal team transfers, isolate manager vs company friction, and ensure 6 months of financial runway."
    }
]

def retrieve_transcripts(query: str):
    """Retrieve podcast transcripts for a query."""
    return CANNED_CHUNKS

TOOLS = [
    {
        "name": "retrieve_transcripts",
        "description": "Retrieve relevant transcripts from Lenny's podcast archives.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for podcast transcripts"
                }
            },
            "required": ["query"]
        }
    }
]

def run_claude_sdk_agent():
    model_name = settings.OLLAMA_MODEL
    base_url = settings.OLLAMA_BASE_URL
    client = Anthropic(base_url=base_url, api_key="ollama")

    messages = [
        {"role": "user", "content": "What did Ada Chen Rekhi say about leaving a job?"}
    ]

    system_prompt = (
        "You are an assistant. When the user asks about podcast content, "
        "you MUST call retrieve_transcripts tool first to get facts, "
        "and then answer strictly using ONLY the retrieved chunks."
    )

    t0 = time.time()
    ttft = None
    tool_called = False

    print(f"Connecting to {base_url} with model {model_name}...")
    response = client.messages.create(
        model=model_name,
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
        tools=TOOLS,
    )
    if ttft is None:
        ttft = time.time() - t0

    # Inspect response content
    tool_use_block = None
    for block in response.content:
        if getattr(block, "type", None) == "tool_use":
            tool_use_block = block
            tool_called = True
            break

    if not tool_use_block:
        print("FAIL: Model did not invoke retrieve_transcripts tool.")
        print("Response content:", response.content)
        return {
            "success": False,
            "tool_called": False,
            "cites_chunk": False,
            "ttft": ttft,
            "answer": str(response.content)
        }

    print(f"Tool invoked: {tool_use_block.name} with input: {tool_use_block.input}")
    tool_result = retrieve_transcripts(tool_use_block.input.get("query", ""))

    # Feed tool result back to the model
    messages.append({"role": "assistant", "content": response.content})
    messages.append({
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": tool_use_block.id,
                "content": json.dumps(tool_result),
            }
        ]
    })

    final_resp = client.messages.create(
        model=model_name,
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
        tools=TOOLS,
    )

    answer_text = ""
    for b in final_resp.content:
        if getattr(b, "type", None) == "text":
            answer_text += b.text

    print(f"\nFinal Answer:\n{answer_text}\n")
    cites_chunk = "Energy & Learning Matrix" in answer_text or "60-day window" in answer_text or "financial runway" in answer_text

    return {
        "success": tool_called and cites_chunk,
        "tool_called": tool_called,
        "cites_chunk": cites_chunk,
        "ttft": ttft,
        "answer": answer_text
    }

if __name__ == "__main__":
    runs = 5
    passes = 0
    print(f"=== Running Claude Agent SDK Spike ({runs} iterations) ===")
    for i in range(1, runs + 1):
        print(f"\n--- RUN {i}/{runs} ---")
        res = run_claude_sdk_agent()
        print(f"Run {i} Result: success={res['success']}, tool_called={res['tool_called']}, cites_chunk={res['cites_chunk']}, ttft={res['ttft']:.2f}s")
        if res["success"]:
            passes += 1
    print(f"\n==========================================")
    print(f"Claude Agent SDK Final Score: {passes}/{runs} PASS")
    print(f"==========================================")
