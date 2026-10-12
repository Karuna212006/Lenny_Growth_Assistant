# Evaluation Results & Latency Benchmarks

> Measured empirically against PostgreSQL 18 + pgvector (303 episodes, 19,434 chunks) and local Ollama running `qwen2.5:7b-instruct` and `nomic-embed-text`.

---

## 1. Corpus Scale & Ingestion Status

- **Episodes Ingested**: 303 / 303 (100% of corpus)
- **Chunks Persisted**: 19,434 chunks with 768-dimensional `nomic-embed-text` embeddings
- **Ingestion Duration**: 1,054.60 seconds (~17.5 minutes)
- **Database Count Verification**:
  ```sql
  SELECT count(*) FROM episodes; -- 303
  SELECT count(*) FROM chunks;   -- 19434
  ```

---

## 2. Verbatim Verification (Ground Truth Check)

Audited 9 chunks (including Ada Chen Rekhi chunks 22 through 25 and 5 random chunks across other guests) against the source Markdown transcript files:

| Target Chunk | Guest / Episode | DB Chunk Index | First 150 Chars in DB | Verbatim in Source File? |
| :--- | :--- | :--- | :--- | :--- |
| **Ada Chen Rekhi** | Ada Chen Rekhi | 22 | `Ada Chen Rekhi (00:26:29): Explore and exploit, if you're familiar with it from growth background...` | **MATCH (100%)** |
| **Ada Chen Rekhi** | Ada Chen Rekhi | 23 | `Lenny (00:28:20): Yeah. It's a beautiful product.\n\nAda Chen Rekhi (00:28:22): Yeah, it's a beautiful...` | **MATCH (100%)** |
| **Ada Chen Rekhi** | Ada Chen Rekhi | 24 | `Ada Chen Rekhi (00:28:22): Yeah, it's a beautiful product, much more beautiful than what we built...` | **MATCH (100%)** |
| **Ada Chen Rekhi** | Ada Chen Rekhi | 25 | `Ada Chen Rekhi (00:28:22): (00:29:53):\nSo I managed to get into this great role leading gross marketing...` | **MATCH (100%)** |
| **Random 1** | Barbra Gago | 28 | `Lenny (36:54): Oh damn.\n\nBarbra Gago (36:54): All the material had been printed with the new URL...` | **MATCH (100%)** |
| **Random 2** | Jason Feifer | 57 | `Jason Feifer (01:11:29): Everyone has a different approach to this. The number one rule here is...` | **MATCH (100%)** |
| **Random 3** | Adam Fishman | 12 | `Adam Fishman (00:16:06): And so when you think about it, there are four main components to the growth...` | **MATCH (100%)** |
| **Random 4** | Ethan Evans | 21 | `Lenny (00:23:00): Yeah, I think that your point about your goal doesn't have to be promotion...` | **MATCH (100%)** |
| **Random 5** | Jessica Hische | 33 | `Jessica Hische (00:39:01): Oh, yeah. I love sharing iterations. It's very fun. Yeah.\n\nLenny...` | **MATCH (100%)** |

**Result**: **9 / 9 chunks verified verbatim**. The conversational dialogue in PostgreSQL pgvector strictly matches the transcript files on disk.

---

## 3. Distance Threshold Sweep

Evaluated cosine distance thresholds across 5 answerable questions and 3 clearly out-of-scope/unrelated questions on the full 19,434 chunk corpus:

### Query Best Distances:
* **Answerable Questions**:
  1. *"What did Ada Chen Rekhi advise about knowing when it's time to leave your job?"* $\rightarrow$ **0.2119** (Similarity 0.7881)
  2. *"How did Adam Fishman describe the core pillars of growth teams?"* $\rightarrow$ **0.2411** (Similarity 0.7589)
  3. *"What did April Dunford say about sales pitch and differentiated value?"* $\rightarrow$ **0.1624** (Similarity 0.8376)
  4. *"What did Ethan Evans advise about career ownership and promotions?"* $\rightarrow$ **0.2267** (Similarity 0.7733)
  5. *"What did Barbra Gago say about category creation and rebranding?"* $\rightarrow$ **0.1436** (Similarity 0.8564)
* **Unrelated Questions**:
  1. *"What is the capital city of Australia and what is its population?"* $\rightarrow$ **0.3901**
  2. *"How do you make authentic Neapolitan pizza dough with double zero flour?"* $\rightarrow$ **0.4335**
  3. *"Who won the FIFA World Cup in 1994 and what was the penalty shootout score?"* $\rightarrow$ **0.4364**

### Threshold Sweep Table:
| Distance Threshold | Answered (of 5 Answerable) | Refused (of 3 Unrelated) | Status |
| :---: | :---: | :---: | :--- |
| **0.30** | **5 / 5** | **3 / 3** | **Optimal** (100% precision, 100% recall) |
| **0.35** | **5 / 5** | **3 / 3** | **Optimal** (safe operating margin) |
| **0.40** | 5 / 5 | 2 / 3 | False positive leak (unrelated Q1 passes at 0.3901) |
| **0.45** | 5 / 5 | 0 / 3 | All unrelated questions leak |
| **0.50** | 5 / 5 | 0 / 3 | All unrelated questions leak |
| **0.55** | 5 / 5 | 0 / 3 | All unrelated questions leak |

**Conclusion**: The default threshold of `0.30` (or `0.35`) provides sharp separation between in-corpus product/growth topics and out-of-scope general queries.

---

## 4. Latency Benchmarks: Standalone vs Follow-up

### A. Standalone Questions (Skip Tool Optimization)
Bypasses the agent tool loop; executes query directly against vector search in code.
- Median TTFT: **0.88s** (Runs: 1.56s [cold], 0.88s, 0.87s, 0.88s, 0.89s).

### B. Follow-up Questions: Tool Loop vs Rewriter Only (5 Consecutive Runs)
Follow-up prompt: *"Can you elaborate on her advice about knowing when to leave your job?"*

| Run # | (a) Follow-up with Tool Loop | (b) Follow-up with Rewriter Only |
| :---: | :---: | :---: |
| Run 1 | 9.862s | 1.923s |
| Run 2 | 5.540s | 2.533s |
| Run 3 | 5.526s | 2.042s |
| Run 4 | 5.369s | 2.032s |
| Run 5 | 5.332s | 1.985s |
| **Median TTFT** | **5.526s** | **2.032s** |
| **Tool Overhead** | — | **-3.494s faster without tool loop** |

### UI Status Keep-Alive Event
To ensure the UI is never silent during the ~5.5s tool roundtrip on follow-up questions, an SSE status event is emitted immediately prior to tool invocation:
```json
event: status
data: {"stage": "retrieving", "message": "understanding your follow-up"}
```
