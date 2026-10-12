# Decision Record: Agent Layer Implementation (Spike & Integration Results)

## 1. Context & Assignment Requirement
The assignment brief specifies that the agent layer should use either the **Anthropic Claude Agent SDK** or the **Pi Coding Agent**, alongside the mandatory requirement that the demo operates offline using a local **Ollama** model (`qwen2.5:7b-instruct`).

This document records the exact packages evaluated, spike methodology, limitations discovered, and the integrated runtime architecture.

---

## 2. Package & Spike Audit

### Candidate 1a: Anthropic Python Client Library (`anthropic==1.13.0`)
- **Package**: `anthropic==1.13.0` (Official Anthropic Python client library).
- **Import**: `from anthropic import Anthropic`.
- **Mechanism**:
  - Connects to Ollama's Messages API compatibility layer at `http://localhost:11434/v1/messages`.
  - Configured with `base_url=settings.OLLAMA_BASE_URL` and dummy `api_key="ollama"` (zero cost).
  - Supplies `retrieve_transcripts` JSON tool schema via `tools=TOOLS` on `client.messages.create()`.
- **Empirical Spike (5 Consecutive Runs with Canned Chunks)**:
  - Isolate tool calling from retrieval quality:
  - Run 1: **PASS** (Tool invoked: `retrieve_transcripts`, TTFT: 3.49s)
  - Run 2: **PASS** (Tool invoked: `retrieve_transcripts`, TTFT: 3.24s)
  - Run 3: **PASS** (Tool invoked: `retrieve_transcripts`, TTFT: 3.30s)
  - Run 4: **PASS** (Tool invoked: `retrieve_transcripts`, TTFT: 3.22s)
  - Run 5: **PASS** (Tool invoked: `retrieve_transcripts`, TTFT: 3.17s)
- **Result**: **5/5 PASS (100%)**. Tool calling is reliable against local Ollama.

### Candidate 1b: Claude Agent SDK (`claude-agent-sdk==0.2.165`)
- **Package**: `claude-agent-sdk==0.2.165`.
- **Import**: `from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions`.
- **Mechanism**:
  - Investigated and installed. Under the hood, `claude-agent-sdk` is an RPC bridge that spawns the bundled Claude Code CLI binary (`site-packages/claude_agent_sdk/_bundled/claude.exe`) via `SubprocessCLITransport`.
  - It expects Claude Code user authentication, defaults to model `claude-opus-5-5`, and relies on Anthropic cloud infrastructure.
  - When pointed to local Ollama with `ANTHROPIC_BASE_URL=http://localhost:11434` and `qwen2.5:7b-instruct`, connection and message reception timed out. It cannot run directly against a standalone local Ollama model without Claude Code cloud authentication.
- **Result**: **Attempted, failed due to Claude Code CLI / cloud auth dependency**.

### Candidate 2: Pi Coding Agent (`@earendil-works/pi-coding-agent==1.1.0`)
- **Package**: `@earendil-works/pi-coding-agent==1.1.0` (npm global binary `pi`).
- **Mechanism**:
  - Custom tool extension `scripts/spike/pi_tool_ext.mjs` registered `retrieve_transcripts`.
  - Evaluated in non-interactive / print mode (`pi -p ...`).
- **Result**: **Not evaluated beyond a headless launch attempt**.
  - In a headless Windows subprocess without an interactive TTY console, the process hung indefinitely waiting for terminal dimension/stream configuration. Pi does not expose an in-process async Python SDK for FastAPI.

---

## 3. Decision & Application Integration
1. **Decision**:
   - The application integrates Candidate 1a: the **Anthropic Python SDK tool-use API** (`anthropic==1.13.0`) connected to local Ollama (`http://localhost:11434/v1/messages`).
   - We honestly label this as Anthropic Python SDK tool use against Ollama; `claude-agent-sdk` and Pi were attempted and documented above.
2. **Runtime Integration in `backend/app/agents/orchestrator.py`**:
   - `invoke_retrieval_tool_agent()` runs the `retrieve_transcripts` tool-calling loop using the Anthropic client against Ollama.
   - The tool call executes real pgvector vector search (`search_transcripts`).
   - Emits structured log line: `Agent SDK tool call invoked: retrieve_transcripts with query='...'`.
   - If retrieval returns empty results, the orchestrator immediately yields a refusal without calling `provider.chat` (no model hallucinations).
   - If the SDK path fails (e.g. connection timeout), it logs a warning and gracefully falls back to direct vector search, maintaining system resilience.
