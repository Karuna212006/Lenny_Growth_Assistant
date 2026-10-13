# Session 04 — Agent SDK Integration, Grounding Verification, and 303-Episode Ingestion

> Timestamp: 2026-10-12
> Focus: Phase 1b (Tool Calling Loop), Phase 1c/1d (Grounding Guarantees & Real Benchmarks), Phase 1e (Full Corpus Ingestion & Latency Profiling).

---

## 1. Objectives & Context

Following the spike in Session 03 (which demonstrated that the Anthropic Python SDK `1.13.0` was compatible with Ollama's Messages API compatibility layer, while Pi Coding Agent hung on Windows TTY and `claude-agent-sdk` required Claude Code CLI with cloud authentication), Session 04 focused on:
1. Wiring `anthropic` tool-use loop directly into the backend runtime orchestrator (`backend/app/agents/orchestrator.py`).
2. Guaranteeing strict grounding (ensuring vector search always executes regardless of LLM tool miscalls).
3. Verifying verbatim ground truth against real source Markdown transcripts.
4. Executing full corpus ingestion across all 303 episodes (19,434 chunks) into PostgreSQL 18 with pgvector.
5. Performing retrieval threshold sweeps (testing 0.30/0.35 similarity thresholds for answering vs refusing).
6. Benchmarking empirical Time to First Token (TTFT) and follow-up query rewriting latencies.

---

## 2. Failed Attempts & Iterations

### Failure 1: Canned Fixtures vs Ground Truth Drift
- **Issue**: Early e2e tests passed assertions using synthetic test fixtures ("Curiosity Loops" attributed to Ada Chen Rekhi). When inspecting the real source transcript `data/transcripts/ada-chen-rekhi/transcript.md`, the phrase "Curiosity Loops" did not exist in Ada's episode.
- **Root Cause**: An earlier spike mock used synthetic sample chunks instead of loading real database chunks.
- **Resolution**: Implemented `scripts/run_real_retrieval_e2e.py` querying PostgreSQL directly. Grounded Ada Chen Rekhi's actual advice on leaving a job, executive coaching, and the "explore vs exploit" framework directly from retrieved chunks `[S1]`–`[S4]`.

### Failure 2: LLM Inventing Synthetic Citation Indexes
- **Issue**: In initial prompt experiments, the local 7B model occasionally output citations like `[S99]` or omitted citations altogether when summarizing long chunks.
- **Root Cause**: Overly generic system prompts allowed the LLM to format source attribution loosely.
- **Resolution**: Tightened the system prompt with strict citation constraints (`[S#]` matching retrieved chunks). Added an in-code citation validator (`validate_citations()`) in `orchestrator.py` that strips hallucinated citation indexes and guarantees citation chips only correspond to real retrieved chunks.

### Failure 3: Standalone TTFT Tool-Calling Overhead
- **Issue**: Passing tool schemas to the local 7B model on every query caused an unnecessary tool-invocation roundtrip, adding ~3.2s of latency on straightforward standalone queries (TTFT 3.96s vs 0.71s).
- **Root Cause**: The LLM had to output a tool call JSON object, parse it, execute vector search, and then call the model a second time to stream the answer.
- **Resolution**: Implemented standalone skip optimization: on the first turn of a conversation, the orchestrator retrieves chunks directly in Python, bypassing the extra LLM tool step. This reduced median TTFT to 0.72s–0.88s. For follow-up turns, query rewriting retains full conversational context.

---

## 3. Full Ingestion & Verification

### Ingestion Metrics
- **Episodes Scanned**: 303 / 303 (100% of corpus)
- **Chunks Persisted**: 19,434 chunks (768-dimensional `nomic-embed-text` embeddings)
- **Ingestion Time**: 1,054.60 seconds (~17.5 minutes)
- **Verification**:
  ```sql
  SELECT count(*) FROM episodes; -- 303
  SELECT count(*) FROM chunks;   -- 19434
  ```

### Verbatim Verification
Audited 9 chunks (Ada Chen Rekhi chunks 22–25 and 5 random chunks across other guests) against the source Markdown transcript files:
- 9/9 chunks matched 100% verbatim against the source markdown files.

### Threshold Sweep
- Evaluated similarity threshold sweep at `0.30` and `0.35`:
  - 5 out of 5 valid podcast growth queries answered with grounded citations.
  - 3 out of 3 out-of-scope queries (e.g. quantum computing, recipes) explicitly refused with zero hallucinations.

---

## 4. Deliverables & Results
- All findings, verbatim audit tables, threshold results, and latency charts logged in [`docs/eval/RESULTS.md`](../docs/eval/RESULTS.md).
- Decision document updated in [`docs/decisions/agent-layer.md`](../docs/decisions/agent-layer.md).
- 29/29 backend test suite passing.
