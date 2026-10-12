# Decision Record: Agent Layer Implementation (Spike Results)

## 1. Context & Assignment Requirement
The assignment brief mandates either the **Anthropic Claude Agent SDK** or the **Pi Coding Agent** for agentic tool orchestration, coupled with the mandatory requirement that the demo runs against a local **Ollama** instance (`qwen2.5:7b-instruct`).

Prior commits claimed "Pi Coding Agent chosen after spike", but no spike had actually been conducted. On Day 4 (Sprint Finish), an empirical spike was executed testing both candidates against local Ollama.

## 2. Spike Methodology
- **Goal**: Evaluate whether each candidate can reliably execute tool calling (`retrieve_transcripts(query)`) and ground its final response in the returned chunks when querying: *"What did Ada Chen Rekhi say about leaving a job?"*
- **Acceptance Criterion**: Tool invoked correctly and chunks cited in at least 4 out of 5 consecutive runs (>= 80% pass rate).
- **Environment**: Local Ollama v0.5+ running `qwen2.5:7b-instruct` on `http://localhost:11434`.

---

## 3. Candidate 1: Anthropic Claude Agent SDK (Python)
- **Official Documentation**:
  - `https://github.com/anthropics/anthropic-sdk-python`
  - `https://docs.anthropic.com/en/docs/build-with-claude/tool-use`
  - `https://docs.anthropic.com/en/api/client-sdks` (Custom Base URL configuration)
- **Mechanism**:
  - Configured `Anthropic(base_url="http://localhost:11434", api_key="ollama")`.
  - Defined `retrieve_transcripts` tool schema and passed via `tools=TOOLS` on `client.messages.create()`.
  - Fed returned tool result back to the model as `role="user"` with `type="tool_result"`.
- **Results Across 5 Consecutive Runs**:
  - Run 1: **PASS** (Tool invoked: `retrieve_transcripts`, cited Energy & Learning Matrix + 6 months runway, TTFT: 3.49s)
  - Run 2: **PASS** (Tool invoked: `retrieve_transcripts`, cited 60-day window + financial runway, TTFT: 3.24s)
  - Run 3: **PASS** (Tool invoked: `retrieve_transcripts`, cited Energy & Learning Matrix + diagnostic checks, TTFT: 3.30s)
  - Run 4: **PASS** (Tool invoked: `retrieve_transcripts`, cited Energy & Learning Matrix + 4 consecutive weeks, TTFT: 3.22s)
  - Run 5: **PASS** (Tool invoked: `retrieve_transcripts`, cited Energy & Learning Matrix + 6 months runway, TTFT: 3.17s)
- **Score**: **5/5 PASS (100%)**

---

## 4. Candidate 2: Pi Coding Agent (@earendil-works/pi-coding-agent)
- **Official Documentation**:
  - `https://www.npmjs.com/package/@earendil-works/pi-coding-agent`
  - `https://github.com/earendil-works/pi` / `https://pi.dev`
- **Mechanism**:
  - Pi is a standalone Node.js / TypeScript interactive terminal coding assistant.
  - Implemented custom extension `scripts/spike/pi_tool_ext.mjs` registering `retrieve_transcripts`.
  - Invoked `pi --provider ollama --model qwen2.5:7b-instruct -e scripts/spike/pi_tool_ext.mjs --tools retrieve_transcripts -p "..."`.
- **Results Across 5 Consecutive Runs**:
  - Runs 1–5: **FAIL (0/5)**.
  - Root Cause: Pi is architected strictly as an interactive terminal CLI using TUI / ink / blessed console abstractions. In headless or programmatic subprocess environments without an active Windows TTY console, it hangs indefinitely waiting for terminal input and dimensions. It provides no Python API or async bindings for FastAPI.
- **Score**: **0/5 PASS (0%)**

---

## 5. Decision & Architecture Integration
1. **Selected Agent Layer**: **Anthropic Claude Agent SDK** (`anthropic` Python SDK).
2. **Integration Plan**:
   - Claude Agent SDK handles tool-calling and conversation routing for the grounded QA pipeline.
   - Decoupled provider interface remains in place underneath for streaming SSE token generation.
   - The false claim regarding Pi Coding Agent in `docs/architecture.md` is removed and corrected to reflect the empirical spike outcome.
