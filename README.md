# Lenny Growth Assistant

> AI-powered growth assistant grounded in Lenny's Podcast & Newsletter transcripts.

## Architecture Overview

- **Backend:** FastAPI + SQLAlchemy 2 (async) + PostgreSQL + pgvector
- **Frontend:** React + Vite
- **Agent:** Pi Coding Agent via provider interface
- **LLM (local):** Ollama `qwen2.5:7b-instruct` + `nomic-embed-text`
- **LLM (cloud):** Any OpenAI-compatible endpoint (optional)

## Docs

- [`docs/schema.sql`](docs/schema.sql) — Locked DB schema
- [`docs/architecture.md`](docs/architecture.md) — System design
- [`docs/design.md`](docs/design.md) — UI/UX decisions
- [`docs/PRD.md`](docs/PRD.md) — Product Requirements Document
- [`agent-transcripts/`](agent-transcripts/) — Agent sessions including failures

## Quick Start

```bash
cp .env.example .env
# Edit .env — set LLM_PROVIDER and any API keys
docker compose up
```

> Full setup instructions coming as build progresses.

## Prerequisites

- Docker + Docker Compose
- ~8 GB RAM free (for Ollama + DB + API)
- Ollama model will auto-pull on first run (~4 GB for 7b Q4)

## Environment Variables

See [`.env.example`](.env.example) for the full list.

| Variable | Required | Default |
|---|---|---|
| `LLM_PROVIDER` | ✅ | `ollama` |
| `OLLAMA_MODEL` | ✅ | `qwen2.5:7b-instruct` |
| `EMBEDDING_MODEL` | ✅ | `nomic-embed-text` |
| `OPENAI_COMPAT_API_KEY` | ❌ | _(empty)_ |
| `DATABASE_URL` | ✅ | set in Compose |

## Known Limitations

- Local model quality is lower than GPT-4 / Claude; router uses rule-based fallback
- No authentication — anonymous sessions only (documented scope choice)
- Cloud LLM path is optional and may be untested on the demo machine
