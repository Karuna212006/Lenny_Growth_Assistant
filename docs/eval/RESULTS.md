# Evaluation Results & Latency Benchmarks

> Measured empirically against local Ollama running `qwen2.5:7b-instruct` and `nomic-embed-text` on Windows host.

## 1. Time-to-First-Token (TTFT) Benchmarks

**Definition**: Elapsed wall-clock time from request initiation to the emission of the first `token` Server-Sent Event (SSE), measured across 5 consecutive runs.

| Run # | Standalone Question (Skip Optimization Active) | Follow-up Question (Conversational Tool Loop Active) |
|---|---|---|
| Run 1 (Cold) | 1.56s | 13.45s |
| Run 2 | 0.88s | 7.46s |
| Run 3 | 0.87s | 7.16s |
| Run 4 | 0.88s | 7.26s |
| Run 5 | 0.89s | 7.50s |
| **Median TTFT** | **0.88s** | **7.46s** |

### Analysis & Technical Trade-Off
- **Standalone Questions**: The skip optimization (`has_earlier_turn_refs = False`) bypasses the extra Anthropic SDK tool roundtrip, achieving a median TTFT of **0.88s**.
- **Follow-up Questions**: When resolving conversational pronouns ("Why did she advise that?"), query rewriting and the agent tool-calling loop run, adding **+6.58s** of processing overhead before the first token streams.
- **Architectural Decision**: Keep tool-calling strictly conditioned on conversational follow-ups. Standalone questions route directly to deterministic vector search in code, protecting interactive responsiveness for primary queries.

## 2. Grounding & Citation Validation

- **Citation Tagging**: All retrieved excerpts are mapped to structured numbered tags (`[S1]`, `[S2]`, etc.).
- **Hallucination Detection**: In-code validator checks all emitted `[S#]` source tags against available retrieved chunks; any citation exceeding the retrieved chunk count is flagged and stripped.
