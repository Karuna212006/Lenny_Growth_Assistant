# Lenny Growth Assistant

> AI-powered growth assistant grounded in Lenny Rachitsky's Podcast & Newsletter transcripts (303 episodes, 19,434 chunks). Features strict citation attribution, Ship 30 for 30 essay generation, and a sandboxed side-by-side artifact viewer.

[![Tests](https://img.shields.io/badge/tests-29%20passed-brightgreen.svg)](#running-tests)
[![Corpus](https://img.shields.io/badge/corpus-303%20episodes%20%7C%2019%2C434%20chunks-blue.svg)](docs/eval/RESULTS.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 1. Architecture Overview

```
[Frontend: React + Vite]
        │  (REST + SSE Token Streaming)
        ▼
[FastAPI Backend Application]
   ├── routers/     ── HTTP Contracts (sessions, messages, config, artifacts, admin, health)
   ├── agents/      ── Intent Router + Anthropic SDK Tool-Use Loop + Standalone TTFT Optimizer
   ├── skills/      ── Ship 30 for 30 Essay Skill (SKILL.md, outline -> section drafts -> grounding)
   ├── services/
   │     ├── retrieval  ── Speaker-turn chunking, nomic-embed-text, pgvector similarity search
   │     ├── providers  ── Provider interface (Ollama local / OpenAI-compatible cloud)
   │     └── artifacts  ── Generation, validation, DOMPurify server sanitizer, storage
   └── db/          ── SQLAlchemy 2 (async) + PostgreSQL 16/18 with pgvector
        │
        ├── [PostgreSQL + pgvector] (Stores episodes, chunks, sessions, messages, artifacts)
        ├── [Ollama (Local, Port 11434)] (qwen2.5:7b-instruct + nomic-embed-text)
        └── [Optional Cloud Provider] (OpenAI-compatible endpoints via config)
```

- **Backend:** FastAPI + SQLAlchemy 2 (async) + PostgreSQL + pgvector
- **Frontend:** React + Vite (Side-by-side chat and sandboxed artifact viewer)
- **Agent Layer:** Anthropic Python SDK (`anthropic==1.13.0`) tool-use API against Ollama's Messages endpoint with zero-cost dummy key (`api_key="ollama"`)
- **LLM (local):** Ollama `qwen2.5:7b-instruct` (4-bit quant) + `nomic-embed-text` (768 dimensions)
- **LLM (cloud):** Any OpenAI-compatible endpoint (optional, switchable via config only)

---

## 2. Documentation Directory

- [`docs/PRD.md`](docs/PRD.md) — Product Requirements Document (Discovery brief, user flows, acceptance criteria)
- [`docs/architecture.md`](docs/architecture.md) — System design, DB schema, ER diagram, contracts, security topology
- [`docs/design.md`](docs/design.md) — UI/UX specification, 3-pane layout, states, accessibility
- [`docs/manual_test_plan.md`](docs/manual_test_plan.md) — Step-by-step manual UI verification scenarios
- [`docs/eval/RESULTS.md`](docs/eval/RESULTS.md) — Empirical benchmarks (verbatim checks, threshold sweep, TTFT profiles)
- [`docs/decisions/agent-layer.md`](docs/decisions/agent-layer.md) — Spike results comparing Anthropic SDK vs Pi Coding Agent vs Claude Agent SDK
- [`agent-transcripts/`](agent-transcripts/) — Chronological record of all agent pair-programming sessions including failed attempts

---

## 3. Quick Start (One-Command Startup)

### Prerequisites
- Docker & Docker Compose installed and running
- ~8 GB RAM free (for Ollama model execution + PostgreSQL pgvector + FastAPI)
- NVIDIA GPU recommended but not required (CPU inference supported)

### One-Command Launch

```bash
# 1. Clone repository
git clone https://github.com/Karuna212006/Lenny_Growth_Assistant.git
cd Lenny_Growth_Assistant

# 2. Configure environment from example
cp .env.example .env

# 3. Pull required Ollama models locally (if running Ollama host)
ollama pull qwen2.5:7b-instruct
ollama pull nomic-embed-text

# 4. Start all services via Docker Compose
docker compose up
```

Once started:
- **Web UI:** http://localhost:5173
- **FastAPI Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health/ready

---

## 4. Local Development Setup (Without Docker)

If you prefer running services directly on your host machine:

### 1. Database Setup
Ensure PostgreSQL (with the `vector` extension) is running:
```bash
# Run schema migration script
psql -h localhost -U lenny -d lenny_assistant -f docs/schema.sql
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 5. Ingestion Pipeline & Corpus Status

The entire corpus of 303 episodes and 19,434 chunks is indexed in PostgreSQL with 768-dimensional `nomic-embed-text` embeddings.

### Ingestion Status
- **Episodes Ingested:** 303 / 303 (100% of corpus)
- **Chunks Persisted:** 19,434 chunks
- **Verbatim Accuracy:** 100% verified against source transcripts (see [RESULTS.md](docs/eval/RESULTS.md))

### Re-running or Refreshing Ingestion
```bash
# Run incremental ingestion (skips unchanged content hashes):
python -m backend.app.services.retrieval.ingest

# Or via Docker:
docker compose --profile ingest run --rm ingest
```

---

## 6. Environment Variables

All settings are driven via `.env`. No code modifications are required to switch models or toggle cloud fallbacks:

| Variable | Required | Default | Description |
|---|---|---|---|
| `LLM_PROVIDER` | ✅ | `ollama` | Active provider: `ollama` or `openai_compatible` |
| `OLLAMA_BASE_URL` | ✅ | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | ✅ | `qwen2.5:7b-instruct` | Chat completion model |
| `EMBEDDING_MODEL` | ✅ | `nomic-embed-text` | 768-dimension embedding model |
| `DATABASE_URL` | ✅ | `postgresql+asyncpg://...` | Async SQLAlchemy PostgreSQL connection string |
| `OPENAI_COMPAT_BASE_URL` | ❌ | `https://api.openai.com/v1` | Optional cloud API endpoint |
| `OPENAI_COMPAT_API_KEY` | ❌ | _(empty)_ | Optional cloud API key |
| `OPENAI_COMPAT_MODEL` | ❌ | `gpt-4o-mini` | Optional cloud model name |
| `RETRIEVAL_SIMILARITY_THRESHOLD` | ❌ | `0.30` | Minimum cosine similarity to answer (refuses if below) |

---

## 7. Running Tests

### Automated Backend Tests
Runs unit and integration tests covering agent routing, standalone TTFT optimizations, artifact sanitization, and Ship 30 essay generation:

```bash
python -m pytest
```
*Result: 29 passed in ~5 seconds.*

### Frontend Production Build
```bash
cd frontend
npm run build
```
*Result: Vite build completes cleanly.*

### Manual UI Test Plan
See [`docs/manual_test_plan.md`](docs/manual_test_plan.md) for step-by-step validation of sessions, citations, out-of-scope refusals, essays, and the artifact sandbox.

---

## 8. Artifact Sandboxing & Security

Generated HTML/CSS deliverables are treated as untrusted input. The application implements defense-in-depth isolation:
1. **Server-Side Sanitization:** Strips `<script>`, `<iframe>`, `<object>`, `<embed>`, inline event handlers (`onload`, `onerror`), and JavaScript URLs before saving to PostgreSQL.
2. **Iframe Sandboxing:** Rendered inside `<iframe sandbox="allow-downloads">` explicitly omitting `allow-scripts` and `allow-same-origin`.
3. **Content Security Policy (CSP):** Injects `default-src 'none'; style-src 'unsafe-inline'; img-src data:;` preventing external network requests.
4. **Allowed / Blocked Inspector:** A security drawer at the bottom of the artifact viewer transparently shows the user what tags were preserved and what was blocked.

---

## 9. Troubleshooting

| Issue | Root Cause | Solution |
|---|---|---|
| `MODEL_UNAVAILABLE` error | Ollama service is not running | Run `ollama serve` in a terminal or restart the Ollama service. |
| Model not found error | Models haven't been pulled | Run `ollama pull qwen2.5:7b-instruct` and `ollama pull nomic-embed-text`. |
| `DB_UNAVAILABLE` error | PostgreSQL service stopped or wrong port | Verify PostgreSQL is running on port 5432 and credentials match `.env`. |
| Port 5432 or 8000 conflict | Another local service using the port | Stop conflicting services or modify port mappings in `.env` / `docker-compose.yml`. |
| Out of memory during inference | 7B model requires ~4.5 GB RAM | Fallback to `qwen2.5:3b` in `.env` (`OLLAMA_MODEL=qwen2.5:3b`). |

---

## 10. How to Extend

### Adding a New Skill
1. Create a new skill directory in `backend/app/skills/<skill_name>/`.
2. Add a `SKILL.md` specifying principles, prompt structure, and output constraints.
3. Implement a generator in `generator.py` adhering to the standard skill interface.
4. Register the skill in `backend/app/agents/orchestrator.py`.

### Adding a New LLM Provider
1. Inherit from `BaseProvider` in `backend/app/services/providers/base.py`.
2. Implement `chat_stream()` and `is_available()`.
3. Register the provider in `backend/app/services/providers/factory.py`.

---

## 11. Known Limitations & Trade-Offs

1. **Local Model Capacity:** `qwen2.5:7b-instruct` is an efficient 7B parameter model. While it performs well on grounded extraction and structured synthesis, complex multi-step reasoning may occasionally require explicit query formulation.
2. **Interactive Scripts in Artifacts:** Because generated HTML is strictly sandboxed without `allow-scripts`, interactive JavaScript widgets are intentionally not executed to eliminate XSS risks.
3. **Single-Tenant Anonymous Sessions:** Authentication uses client-side anonymous session UUIDs stored in `localStorage` rather than multi-tenant JWT auth.
4. **Demo Video:** See link below for the 2–3 minute video walkthrough.

---

## 12. Demo Video

- **Video Walkthrough (2–3 mins, camera on):** *[Link to YouTube Video — To be added]*
