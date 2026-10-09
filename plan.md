# Lenny Growth Assistant — End-to-End Plan & Checklist

## 0. Reality Check: Timeline

Due: **12/10/26 EOD** (read as 12 Oct 2026). Today is 9 Oct, so you have about 3 working days plus the due day. Submit by **Monday afternoon**, not at the last minute.

| Day | Focus | Done when |
|---|---|---|
| Fri 9 Oct | Discovery brief + system design + repo + DB + FastAPI skeleton + provider layer | You can create a session and get a reply from Ollama |
| Sat 10 Oct | Ingestion + retrieval + agent routing + Ship 30 skill + artifacts API | Cited answer, essay, and artifact all work from the API |
| Sun 11 Oct | Frontend + artifact viewer + resilience + tests + docs | Full flow works in the browser; docs drafted |
| Mon 12 Oct | Docker fresh-clone test + agent transcripts + demo video + push + submit | Form submitted by afternoon |

**Cut order if you run behind (drop from the top first):**
1. Fancy UI polish (animations, dark mode)
2. Re-ranking / hybrid search (keep plain vector search)
3. Cloud fallback automation (keep manual toggle only)
4. Extra tests beyond the critical ones

**Never cut:** Ollama demo, citations, artifact sandboxing, README, PRD, design.md, architecture.md, agent transcripts, demo video, Docker startup.

---

## 1. Rules From the Brief (Must Follow)

### Hard requirements
- [ ] Backend is **FastAPI**
- [ ] Agent layer uses **Anthropic Claude Agent SDK** or **Pi Coding Agent**
- [ ] **PostgreSQL** stores conversations, session IDs, timestamps, user metadata (Supabase or Railway allowed)
- [ ] New chat = new session with **independent context**
- [ ] Clear request/response contracts, validation, structured errors, **health endpoints**
- [ ] Model switchable via **config only** (no code change)
- [ ] At least one **cloud LLM** integrated (Anthropic or OpenAI)
- [ ] **Ollama local model is mandatory for the demo**
- [ ] Selected provider **visible in UI or config**; fallback behavior documented
- [ ] Data source is **Lenny's Podcast / Newsletter transcript repository**
- [ ] Ingestion explained: load, chunk/select, index, refresh, trace to source
- [ ] Answers **cite/identify the transcript source**
- [ ] Answers **strictly from transcripts**; says so when material doesn't support an answer
- [ ] Handles follow-ups and keeps session context
- [ ] **Ship 30 for 30 skill/tool** exists (not a one-off prompt)
- [ ] Essay ~**1,250 words**, strong hook, narrative progression, headings + bullets + selective bold, specific takeaway, claims grounded in transcripts
- [ ] Markdown or HTML/CSS artifacts generated on request
- [ ] **Artifact Viewer renders beside the chat** (in-app, not raw code, no redirect)
- [ ] Generated HTML treated as **untrusted**; isolation/sanitization implemented **and explained**
- [ ] One-command startup (Docker Compose or equivalent)
- [ ] `.env.example` with safe defaults; **no secrets committed**
- [ ] Structured logs covering model, retrieval, database, artifact-rendering failures
- [ ] Graceful handling of: missing keys, Ollama down, model timeout, empty retrieval, DB connection failure
- [ ] Handoff docs: how to run, test, troubleshoot, extend
- [ ] Fresh evaluator can clone and run using **only documented steps**

### Deliverables (all 8 required)
- [ ] 1. Public GitHub repo (sensible structure, no secrets)
- [ ] 2. `README.md`
- [ ] 3. PRD
- [ ] 4. `design.md`
- [ ] 5. `architecture.md`
- [ ] 6. Agent transcripts folder (including **failed attempts and fixes**, secrets removed)
- [ ] 7. Tests (critical API, retrieval, routing, persistence) + short manual UI test plan
- [ ] 8. Demo video, 2–3 min, **camera on**, uploaded to **YouTube**

---

## 2. Do NOT Do

- [ ] Don't commit `.env`, API keys, DB passwords, or tokens (check `git log` too, not just the working tree)
- [ ] Don't render generated HTML directly in the main page (no `dangerouslySetInnerHTML` of raw model output)
- [ ] Don't let the assistant answer from the model's own knowledge when retrieval is empty
- [ ] Don't hard-code the model name or provider in application code
- [ ] Don't use a cloud model for the demo instead of Ollama
- [ ] Don't share one global conversation across sessions
- [ ] Don't return raw stack traces to the UI
- [ ] Don't skip the failed-attempts part of agent transcripts (it's explicitly required)
- [ ] Don't write a one-off prompt and call it a "skill"
- [ ] Don't claim features in README/PRD that aren't built (keep claims honest and modest)
- [ ] Don't add large out-of-scope features (auth system, payments, multi-tenant admin, voice, etc.)
- [ ] Don't leave the demo video for the last hour
- [ ] Don't submit without a fresh-clone test
- [ ] Don't copy transcript content into docs beyond short excerpts (the data belongs to its source)

---

## 3. Phase 0 — Discovery Brief (goes inside the PRD)

Write this first, short and sharp (about one page).

- [ ] **User & problem:** Primary user = a PM / growth lead on the client's team. Job = get trustworthy, source-backed answers and turn them into publishable content fast. Pain = searching hours of transcripts manually; generic AI answers that can't be trusted.
- [ ] **Success metrics (pick 2–3, make them measurable):**
  - % of answers with at least one valid citation (target: ≥ 95% on your eval set)
  - % of out-of-scope questions correctly refused (target: ≥ 90%)
  - Median time to first token (target: under X s on local model)
  - Essay word count within ±10% of 1,250
- [ ] **Assumptions** (record at least 6): e.g. single-tenant, no login (session = anonymous user ID), English only, transcripts are text, local model is small so quality is lower, cloud key is optional, embeddings are local for both modes
- [ ] **Scope in / out** with reasons
- [ ] **Risks & trade-offs:** hallucination, latency, cost, local-model quality, data leakage, unsafe artifact rendering — each with a mitigation

---

## 4. Phase 1 — System Design (START HERE)

Do this on paper / in `architecture.md` before writing code. Decide, write down, then build.

### 4.1 Decisions to lock
- [ ] **Stack:** FastAPI + SQLAlchemy/asyncpg, PostgreSQL + **pgvector**, React/Vite (or Next.js) frontend, Ollama
- [ ] **Why pgvector:** one database for chat data and vectors, so the Compose file stays simple
- [ ] **Embeddings:** one local embedding model (e.g. an Ollama embedding model) used for **both** local and cloud modes so the index is the same. Cloud LLM providers like Anthropic don't offer embeddings, so don't depend on them
- [ ] **Agent layer choice:** Claude Agent SDK or Pi. **Run a 30-minute spike**: can it use Ollama? If not, use the SDK for the cloud path and a thin provider interface for local. Document the decision either way
- [ ] **Streaming:** Server-Sent Events for token streaming
- [ ] **Identity:** anonymous user ID stored in browser + user metadata table (no full auth, documented as a scope choice)

### 4.2 Database schema (draft)

| Table | Key columns |
|---|---|
| `users` | id, anon_key, metadata (jsonb), created_at |
| `sessions` | id, user_id, title, provider, model, created_at, updated_at |
| `messages` | id, session_id, role, content, citations (jsonb), provider, model, latency_ms, created_at |
| `artifacts` | id, session_id, message_id, type (markdown/html), title, content, created_at |
| `episodes` | id, title, guest, source_path/url, content_hash, ingested_at |
| `chunks` | id, episode_id, text, speaker, start_time, chunk_index, embedding (vector) |

- [ ] Indexes: `messages(session_id, created_at)`, vector index on `chunks.embedding`
- [ ] Draw an ER diagram for `architecture.md`

### 4.3 API contract (draft)

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness |
| GET | `/health/ready` | DB + Ollama + index status |
| POST | `/sessions` | New chat |
| GET | `/sessions` | List chats |
| GET | `/sessions/{id}` | Messages + artifacts |
| POST | `/sessions/{id}/messages` | Send message (SSE stream) |
| GET | `/config/providers` | Active + available providers |
| GET | `/artifacts/{id}` | Fetch one artifact |
| POST | `/admin/ingest` | Trigger (re)ingestion |

- [ ] Pydantic request/response models for every endpoint
- [ ] One error shape everywhere: `{ "error": { "code", "message", "request_id" } }`
- [ ] Error codes defined: `MODEL_UNAVAILABLE`, `MODEL_TIMEOUT`, `NO_RELEVANT_SOURCES`, `DB_UNAVAILABLE`, `MISSING_API_KEY`, `VALIDATION_ERROR`

### 4.4 Agent routing design
- [ ] Router decides intent: `qa` | `essay` | `artifact` | `out_of_scope`
- [ ] Tools/skills: `retrieve_transcripts`, `ship30_essay` (skill), `create_artifact`
- [ ] Flow for `qa`: rewrite follow-up into standalone query → retrieve → check relevance threshold → answer with citations or refuse
- [ ] Flow for `essay`: retrieve → outline → draft by section → word-count check → grounding check → revise
- [ ] Flow for `artifact`: take current conversation → generate MD/HTML → validate → store → return artifact ID
- [ ] Draw a routing diagram for `architecture.md`

### 4.5 Retrieval design
- [ ] Chunking: split by speaker turns, group to roughly 300–500 tokens, small overlap, keep episode/guest/timestamp metadata
- [ ] Retrieval: top-k vector search (k about 6–8), similarity threshold for "not supported"
- [ ] Refresh: content hash per episode → re-embed only changed/new files
- [ ] Traceability: every chunk links to episode title + source path/URL

### 4.6 Model toggle design
- [ ] `.env`: `LLM_PROVIDER=ollama|anthropic|openai`, `OLLAMA_MODEL`, `ANTHROPIC_API_KEY` (optional), timeouts
- [ ] Provider interface (one class per provider, same method signature)
- [ ] Fallback rule documented (e.g. Ollama down → clear error + suggestion to switch; optional auto-fallback to cloud only if key exists)
- [ ] Active provider shown in UI header/badge

### 4.7 Security design (artifacts)
- [ ] Render HTML in `<iframe sandbox>` **without** `allow-same-origin`
- [ ] Default: **no scripts** (sandbox without `allow-scripts`); document this choice
- [ ] Inject strict CSP into the iframe document: `default-src 'none'; style-src 'unsafe-inline'; img-src data:`
- [ ] Sanitize with DOMPurify (or server-side sanitizer) as a second layer; strip `<script>`, event handlers, `<iframe>`, `<form>`, external URLs
- [ ] Markdown rendered with sanitization too
- [ ] Viewer shows a small "Allowed / Blocked" panel so the evaluator sees it
- [ ] Log blocked content events

### 4.8 Deployment topology
- [ ] Compose services: `frontend`, `api`, `db` (pgvector image), `ollama`, optional `ingest` one-shot job
- [ ] Startup order with health checks (`db` → `ollama` pulls models → `api` → `frontend`)
- [ ] Persistent volumes for DB and Ollama models
- [ ] Draw topology diagram for `architecture.md`

**Phase 1 exit check:** can someone read your design and know every table, endpoint, and flow? If yes, move on.

---

## 5. Phase 2 — Repo Setup

- [ ] Create public GitHub repo; add `.gitignore` (`.env`, `__pycache__`, `node_modules`, DB volumes) **before first commit**
- [ ] Folder structure:
  - `backend/` (app, routers, services, agents, skills, db, tests)
  - `frontend/`
  - `data/` (transcripts or fetch script)
  - `docs/` (PRD, design.md, architecture.md)
  - `agent-transcripts/`
  - `docker-compose.yml`, `.env.example`, `README.md`
- [ ] `.env.example` with safe defaults and comments marking **required** vs **optional**
- [ ] Start saving agent transcripts **from the first prompt** (don't reconstruct later)
- [ ] Commit early and often with clear messages

---

## 6. Phase 3 — Backend Core

- [ ] FastAPI app with routers, settings loaded from env (pydantic-settings)
- [ ] DB connection + migrations (Alembic or init SQL)
- [ ] `/health` and `/health/ready`
- [ ] Session create/list/get endpoints
- [ ] Message persistence with timestamps
- [ ] Global exception handler → structured error shape
- [ ] Request ID middleware + structured JSON logging
- [ ] Test: create two sessions, confirm contexts don't mix

## 7. Phase 4 — LLM Provider Layer

- [ ] Provider interface + Ollama provider + one cloud provider
- [ ] Timeouts and retry (one retry max) per call
- [ ] Missing key → clean `MISSING_API_KEY` error, not a crash
- [ ] Ollama unreachable → `MODEL_UNAVAILABLE` with fix hint
- [ ] `/config/providers` endpoint
- [ ] Switch provider by changing `.env` only; verify
- [ ] Pick a local model that runs comfortably on your machine; note its limits in the README

## 8. Phase 5 — Knowledge Base

- [ ] Get the transcript repo the brief points to (confirm the exact source) and note its license/terms
- [ ] Loader + parser (extract title, guest, speaker turns)
- [ ] Chunker (per design 4.5)
- [ ] Embedding + store in pgvector
- [ ] Incremental refresh via content hash
- [ ] Retrieval function returns chunks + source metadata + scores
- [ ] Empty/low-score retrieval → `NO_RELEVANT_SOURCES` path
- [ ] Build a **small eval set** (15–20 questions: 12 answerable, 5 out-of-scope) so you can measure the success metric
- [ ] Test: known question retrieves the expected episode

## 9. Phase 6 — Agent Layer & Routing

- [ ] Router implemented (intent classification, with a simple rule fallback if the local model misroutes)
- [ ] QA flow with citations in a consistent format (`[Episode title — Guest]`)
- [ ] Follow-up handling via query rewriting using session history
- [ ] History trimming/summarizing so long chats don't overflow the context
- [ ] Out-of-scope / unsupported → explicit "transcripts don't cover this" reply
- [ ] Test: routing returns the correct intent for sample prompts

## 10. Phase 7 — Ship 30 for 30 Skill

- [ ] **Read the Ship 30 for 30 guide** (linked in the brief) and write down its principles
- [ ] Encode them in a `SKILL.md`-style file: structure, hook rules, formatting rules, word target, takeaway rule, grounding rule
- [ ] Skill pipeline: outline → section drafts → word count check → grounding check → revise
- [ ] Output formatting: headings, bullets, selective bold
- [ ] Verify: about 1,250 words (measure it in a test), has hook, has specific takeaway, claims map to retrieved chunks
- [ ] Note in the README how the skill is structured and how to edit it

## 11. Phase 8 — Artifact Generation & Storage

- [ ] `create_artifact` tool: Markdown or complete HTML/CSS from the current conversation
- [ ] Validate output (non-empty, size limit, type)
- [ ] Store in `artifacts` table linked to session and message
- [ ] Return artifact ID + type in the message response
- [ ] Log artifact generation failures

---

## 12. Phase 9 — Frontend

- [ ] Layout: sidebar (sessions) | chat | **artifact viewer beside chat**
- [ ] New chat button; session list persists after refresh
- [ ] Streaming messages with visible states: thinking, retrieving sources, generating, done, error
- [ ] Citations shown as clickable chips/cards with episode + guest
- [ ] Provider badge visible (e.g. "Ollama · model-name")
- [ ] Artifact viewer: Markdown rendered, HTML in the sandbox iframe, tabs for Preview / Code, copy + download
- [ ] "Allowed / Blocked" security note in the viewer
- [ ] Empty states (no chats yet, no sources found) and friendly error messages
- [ ] Responsive: viewer becomes a tab/drawer on small screens
- [ ] Accessibility: keyboard navigation, focus states, labels, contrast, `aria-live` for streaming
- [ ] Look at the "Impeccable" resource from the brief for design guidance, and note which principles you used in `design.md`

---

## 13. Phase 10 — Resilience & Observability

Test each failure by actually causing it:

- [ ] Remove cloud key → friendly error, app keeps working on Ollama
- [ ] Stop Ollama → `MODEL_UNAVAILABLE`, UI message, log entry
- [ ] Force a timeout → `MODEL_TIMEOUT`, no hang
- [ ] Ask something unrelated → empty retrieval path
- [ ] Stop the DB → `DB_UNAVAILABLE`, `/health/ready` reports it
- [ ] Malicious HTML artifact (script tag, onerror, external image) → blocked and logged
- [ ] Logs include request ID, session ID, provider, model, retrieval count/scores, latency, error code

## 14. Phase 11 — Tests

Automated (keep them meaningful, not many):
- [ ] API: health, create session, validation error shape
- [ ] Persistence: messages saved with timestamps; sessions isolated
- [ ] Retrieval: known query returns expected source; empty result path
- [ ] Routing: intents classified correctly for sample prompts
- [ ] Provider config: switching provider via env, missing key behavior
- [ ] Artifact sanitization: script/event handler removed
- [ ] Essay: word count within tolerance (can mock the LLM)

Manual:
- [ ] Short **manual UI test plan** file (steps + expected result): new chat, ask, follow-up, out-of-scope, essay, artifact, provider badge, mobile width, keyboard-only

---

## 15. Phase 12 — Documentation Deliverables

### PRD
- [ ] Discovery brief (Phase 0)
- [ ] User flows (ask → cited answer; essay; artifact)
- [ ] Acceptance criteria (testable, tied to success metrics)
- [ ] Scope in/out with reasons
- [ ] Risks and mitigations
- [ ] Implementation plan

### design.md
- [ ] UI/UX principles
- [ ] Information architecture (sidebar / chat / viewer)
- [ ] Key interaction states (loading, streaming, empty, error, no-source)
- [ ] Responsive behavior
- [ ] Accessibility considerations
- [ ] Design decisions and why

### architecture.md
- [ ] DB schema + ER diagram
- [ ] API endpoints
- [ ] Component boundaries
- [ ] Ingestion/retrieval flow
- [ ] Agent routing
- [ ] Model toggle
- [ ] Security (artifact isolation, secrets)
- [ ] Deployment topology

### README.md
- [ ] Architecture overview (short)
- [ ] Prerequisites (Docker, RAM, Ollama model size)
- [ ] Install + **one-command run**
- [ ] Environment variable table (required / optional)
- [ ] Local (Ollama) setup and cloud setup
- [ ] How to ingest/refresh transcripts
- [ ] Run tests
- [ ] Troubleshooting (Ollama not running, model not pulled, DB errors, port conflicts)
- [ ] How to extend (new provider, new skill, new artifact type)
- [ ] Known limitations (honest)

---

## 16. Phase 13 — Agent Transcripts

- [ ] Dedicated folder `agent-transcripts/`
- [ ] Include real sessions, **including failed attempts and how you fixed them**
- [ ] Add a short index file: what each transcript covers
- [ ] Scrub secrets, keys, personal data
- [ ] Grep the folder for `key`, `token`, `password`, `sk-` before committing

## 17. Phase 14 — Deployment Verification

- [ ] `docker compose up` brings up everything from a clean state
- [ ] Ollama model auto-pulls (or README clearly says how)
- [ ] Transcripts ingest automatically or with one documented command
- [ ] **Fresh-clone test:** clone into a new folder (ideally another machine/user), follow **only** the README, confirm it works
- [ ] Fix anything the README missed

## 18. Phase 15 — Demo Video (2–3 minutes, camera on)

Script outline:
- [ ] 0:00–0:25 Problem and user (who needs this and why)
- [ ] 0:25–1:15 Product demo: new chat, cited answer, follow-up, out-of-scope refusal
- [ ] 1:15–1:45 Essay skill + artifact viewer (show the sandbox blocking a script)
- [ ] 1:45–2:15 **Ollama demo**: show provider badge, run locally, optionally flip config
- [ ] 2:15–2:45 One technical trade-off (e.g. local model quality vs. latency, or no-script sandbox vs. interactivity)
- [ ] Camera enabled throughout; audio clear; under 3:00
- [ ] Upload to YouTube (unlisted/public as the form requires); test the link while logged out

---

## 19. Phase 16 — Git Push & Submission

- [ ] Final secret scan (`git log -p | grep -i key`, check `.env` is not tracked)
- [ ] Repo is **public**; open it in a private window to confirm
- [ ] All 8 deliverables present (see Section 1)
- [ ] README links to PRD, design.md, architecture.md, transcripts, video
- [ ] Tag a release or note the final commit hash
- [ ] Fill the submission form: https://forms.gle/LgotDHNVxW1mbzNE7
- [ ] Save a confirmation screenshot

---

## 20. Challenge Register

| Challenge | Where it hits | Planned mitigation | Status |
|---|---|---|---|
| Hallucination beyond transcripts | QA, essay | Relevance threshold, citation enforcement, grounding check | [ ] |
| Poor chunking of conversational text | Retrieval | Speaker-turn chunking + metadata | [ ] |
| Weak local model quality | Router, essay | Small steps, structured output, rule-based router fallback | [ ] |
| Essay length/style drift | Ship 30 skill | Section-by-section drafting + word-count loop | [ ] |
| Follow-up questions lose context | Agent | Query rewriting + history trimming | [ ] |
| Unsafe HTML | Artifact viewer | Sandbox iframe + CSP + sanitizer | [ ] |
| Agent SDK may not talk to Ollama | Agent layer | 30-min spike; thin provider interface | [ ] |
| Latency on local model | UX | Streaming + progress states | [ ] |
| Cost on cloud model | Ops | Token logging; cloud optional | [ ] |
| Docker setup fails on a fresh machine | Deployment | Fresh-clone test; clear troubleshooting | [ ] |
| Leaked secrets | Git | `.gitignore` first; scan before push | [ ] |
| Running out of time | Everything | Day plan + cut order (Section 0) | [ ] |
| Transcript licensing/data handling | Data | Note source and terms; short excerpts only | [ ] |

---

## 21. Evaluation Self-Check (score yourself before submitting)

| Criterion | Question to ask | Pass? |
|---|---|---|
| Customer & product judgment | Do the PRD metrics, assumptions, and scope choices show real thinking? | [ ] |
| Technical execution | Does UI → FastAPI → Postgres → agent → retrieval → model toggle work end to end? | [ ] |
| Agentic architecture & grounding | Are skills separate, routing reliable, answers cited, failures sensible? | [ ] |
| Deployment & operability | Reproducible, observable, resilient, secure, documented? | [ ] |
| Code quality | Clean separation, validation, error handling, meaningful tests? | [ ] |
| UI/UX quality | Polished chat, clear states, useful viewer, responsive, accessible? | [ ] |
| Communication | Are PRD, architecture, design, README, and demo clear? | [ ] |

---

## 22. Final Pre-Submit Checklist (one last pass)

- [ ] Ollama demo works with the internet off (except the first model pull)
- [ ] Citations appear on every grounded answer
- [ ] Out-of-scope question gets an honest refusal
- [ ] Essay is about 1,250 words with hook, headings, bullets, bold, takeaway
- [ ] Malicious HTML is blocked and the viewer explains why
- [ ] Sessions are independent
- [ ] All failure modes in Phase 10 tested
- [ ] Tests pass
- [ ] Fresh-clone run succeeded
- [ ] No secrets anywhere in the repo or transcripts
- [ ] Video uploaded and link works
- [ ] Submission form filled

---

## 23. Outside-the-Plan Log

Write anything you did that was not in this plan. Ask yourself for each: is it required by the brief, or is it scope creep?

| Date/time | What I did | Why | In the brief? (Y/N) | Keep or drop |
|---|---|---|---|---|
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
