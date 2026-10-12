import asyncio
import os
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, tool

@tool("retrieve_transcripts", "Retrieve podcast transcripts", {"query": str})
async def retrieve_transcripts(args):
    return {"content": [{"type": "text", "text": "Ada Chen Rekhi recommended the Energy & Learning Matrix."}]}

async def main():
    options = ClaudeAgentOptions(
        env={
            "ANTHROPIC_BASE_URL": "http://localhost:11434",
            "ANTHROPIC_API_KEY": "ollama",
            "CLAUDE_CODE_SKIP_AUTH": "1"
        }
    )
    client = ClaudeSDKClient(options=options)
    print("Connecting to Claude SDK Client...")
    await client.connect("What did Ada Chen Rekhi say about leaving a job?")
    print("Connected. Reading responses...")
    async for message in client.receive_messages():
        print("Message received:", getattr(message, "subtype", None) or type(message), getattr(message, "data", None) or getattr(message, "message", None))
        if getattr(message, "subtype", None) == "result":
            break

if __name__ == "__main__":
    try:
        asyncio.run(asyncio.wait_for(main(), timeout=15))
    except Exception as e:
        print("Error encountered:", type(e), e)
