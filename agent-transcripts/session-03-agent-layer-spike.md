# Agent Session 03: Agent Layer Spike (Claude Agent SDK vs Pi Coding Agent)

**Date**: 2026-10-12
**Focus**: Phase 1 — Agent Layer Spike against Local Ollama (qwen2.5:7b-instruct)

---

## 1. What Was Asked
The brief requires that the agent layer use either the **Anthropic Claude Agent SDK** or the **Pi Coding Agent**, integrated with the local Ollama instance (`qwen2.5:7b-instruct`) for offline demo execution. Prior documentation had an untested placeholder claiming Pi Coding Agent had been selected without any empirical spike.
Task:
1. Research official documentation and interfaces for both candidates.
2. Build standalone spike scripts in `scripts/spike/` evaluating tool calling (`retrieve_transcripts`) across 5 iterations.
3. Quantify pass/fail results (>= 4 of 5 passes required).
4. Author `docs/decisions/agent-layer.md` and correct architecture documentation.

---

## 2. What We Tried

### Candidate 1: Anthropic Claude Agent SDK (Python)
- **Attempt**: Connected `Anthropic(base_url="http://localhost:11434", api_key="ollama")` to Ollama's Messages API compatibility layer.
- **Tool Schema**: Defined `retrieve_transcripts(query: str)` tool schema.
- **Execution**: Evaluated across 5 consecutive runs with the prompt *"What did Ada Chen Rekhi say about leaving a job?"*.
- **Result**: **5/5 PASS (100%)**.
  - All 5 runs invoked `retrieve_transcripts`.
  - All 5 final answers cited returned chunks (Energy & Learning Matrix, 60-day window, financial runway).
  - Median TTFT: 3.28s.

### Candidate 2: Pi Coding Agent (@earendil-works/pi-coding-agent)
- **Attempt**: Created extension `scripts/spike/pi_tool_ext.mjs` registering `retrieve_transcripts` via `pi.registerTool()`.
- **Execution**: Ran `pi.cmd --provider ollama --model qwen2.5:7b-instruct -e scripts/spike/pi_tool_ext.mjs --tools retrieve_transcripts -p "..."`.
- **What FAILED**:
  - The CLI process hung indefinitely (timed out after 10s per trial across all 5 runs).
- **Root-Cause Analysis**:
  - Pi Coding Agent is packaged as an interactive terminal CLI using Node.js terminal/ink abstractions. In headless or programmatic execution on Windows without an active interactive TTY console, it waits on terminal dimension discovery or stdin streams.
  - Furthermore, it does not provide an async Python API, making it unviable for embedding directly into an async FastAPI web server.
- **Result**: **0/5 PASS (0%)**.

---

## 3. Decision & Resolution
- **Selected**: Anthropic Claude Agent SDK pattern for tool-calling agent workflows.
- Documented in `docs/decisions/agent-layer.md`.
- Corrected false claim in `docs/architecture.md` and updated `docs/PLAN.md`.
