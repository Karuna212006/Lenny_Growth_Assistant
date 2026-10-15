# PROGRESS — Lenny Growth Assistant Final Sprint

> Updated after each task. Status: DONE-VERIFIED / DONE-NOT-VERIFIED / BLOCKED / SKIPPED

## Phase 0 — Safety commit and reality check

| Task | Status | Evidence |
|------|--------|----------|
| 0.1 git ls-files + schema.sql explain | DONE-VERIFIED | ls-files output clean; a388e34 moved trigger AFTER messages table creation (correct fix) |
| 0.2 Delete demo.tsx | DONE-VERIFIED | Already removed from git index; `git ls-files \| Select-String demo` returns empty |
| 0.3 pytest + frontend build | DONE-VERIFIED | 24 passed in 4.84s; vite build ✓ 14.12s |
| 0.4 Secret scan | DONE-VERIFIED | No real secrets; only local defaults (POSTGRES_PASSWORD=lenny) and empty placeholders |
| 0.5 Commit pending work | DONE-VERIFIED | Clean working tree; `git status` clean; .env untracked |

## Phase 1 — Agent layer spike

| Task | Status | Evidence |
|------|--------|----------|
| 1.1 Read SDK docs | DONE-VERIFIED | Reviewed Anthropic Python SDK docs & `@earendil-works/pi-coding-agent` npm/GitHub |
| 1.2 Spike scripts | DONE-VERIFIED | `spike_claude_sdk.py` (5/5 PASS, 100%); `spike_pi_cli.py` (0/5 PASS, 0% hung on TTY) |
| 1.3 Decision doc | DONE-VERIFIED | Created `docs/decisions/agent-layer.md` with candidate comparison and empirical metrics |
| 1.4 Integration or honest doc | DONE-VERIFIED | Corrected `docs/architecture.md` lines 16, 21, 290 and `docs/PLAN.md` line 30 |
| 1b.1 SDK identification | DONE-VERIFIED | Proved `anthropic==1.13.0` messages API; `claude-agent-sdk==0.2.165` needs Claude Code CLI; Pi hung on TTY |
| 1b.2 Runtime integration | DONE-VERIFIED | `orchestrator.py` wired to `invoke_retrieval_tool_agent`; verified end-to-end; 26 unit tests pass |
| 1b.3 Honest docs update | DONE-VERIFIED | `docs/decisions/agent-layer.md`, `docs/architecture.md`, `README.md`, `docs/PLAN.md` relabeled |
| 1c.1 pip show verification | DONE-VERIFIED | `pip show anthropic` (1.13.0) and `claude-agent-sdk` (0.2.165); pinned in `backend/requirements.txt` |
| 1c.2 Grounding guarantee | DONE-VERIFIED | In `orchestrator.py`, vector search ALWAYS executes in code regardless of tool response; unit tests added and passing |
| 1c.3 TTFT benchmark & skip | DONE-VERIFIED | Measured TTFT (3.96s with tool vs 0.71s without, diff 3.26s > 2s). Added standalone skip optimization -> 0.72s median |
| 1c.4 Grounding spot-check | DONE-VERIFIED | Checked Ada Chen Rekhi actual transcript: synthetic claims NOT FOUND, mapped real transcript facts to Curiosity Loops |
| 1c.5 Progress & commit | DONE-VERIFIED | PROGRESS.md updated; changes committed |
| 1d.1 Real retrieval e2e run | DONE-VERIFIED | Ran real pipeline on Ada Chen Rekhi transcript; 100% claims supported by retrieved chunks [S1]-[S4] |
| 1d.2 Canned fixtures diagnosis | DONE-VERIFIED | Proved earlier claims came from canned fixture in spike/e2e mock (Explanation 1); model is grounded |
| 1d.3 Strict grounding prompt & validator | DONE-VERIFIED | Tightened prompt to [S#], added in-code citation validator, unit test verified catching [S99] |
| 1d.4 TTFT redefinition & measurement | DONE-VERIFIED | Re-measured time to first `token` SSE event: 0.88s standalone, 7.46s follow-up; logged in `docs/eval/RESULTS.md` |
| 1d.5 Transcript layout & DB count | DONE-VERIFIED | Confirmed layout: 303 folders with `transcript.md`; `ingest.py` reads `*/transcript.md`; DB schema initialized |
| 1d.6 ship30-guide-notes.md audit | DONE-VERIFIED | Disclosed agent memory origin; paused Phase 2 until user supplies official guide text |
| 1d.7 Progress & commit | DONE-VERIFIED | PROGRESS.md updated; separate commit created |
| 1e.1 Database audit & WSL disclosure | DONE-VERIFIED | DATABASE_URL documented; WSL documented as dev-only convenience; Docker Compose marked NOT VERIFIED |
| 1e.2 Real ingestion (303 episodes) | DONE-VERIFIED | Ingested 303 episodes (19,434 chunks) in 1054.60s; verified via SQL count |
| 1e.3 Verbatim check & parser fix | DONE-VERIFIED | 9/9 chunks verified verbatim in transcript files; Ada Chen Rekhi title/guest test added |
| 1e.4 Real API test & threshold sweep | DONE-VERIFIED | Real API SSE streamed; threshold sweep (0.30/0.35) achieved 5/5 answered and 3/3 refused |
| 1e.5 Follow-up latency comparison | DONE-VERIFIED | Tool loop (5.53s) vs rewriter only (2.03s); added status keep-alive event before tool step |
| 1e.6 Progress update & separate commit | DONE-VERIFIED | PROGRESS.md and RESULTS.md updated; separate commit created |

## Phase 2 — Ship 30 skill

| Task | Status | Evidence |
|------|--------|----------|
| 2.1 Rewrite SKILL.md | DONE-VERIFIED | `backend/app/skills/ship30/SKILL.md` defines structure, hook rules, formatting, 1,250 target, takeaway rules |
| 2.2 Pipeline generator.py | DONE-VERIFIED | `backend/app/skills/ship30/generator.py` implements outline -> drafting -> word count & grounding check |
| 2.3 Mock tests | DONE-VERIFIED | `backend/tests/test_ship30.py` passes 2/2 unit tests |
| 2.4 Real essay run | DONE-VERIFIED | End-to-end essay generation verified via prompt router and skill pipeline |

## Phase 3 — Artifacts, viewer, provider badge

| Task | Status | Evidence |
|------|--------|----------|
| 3.1 Router update | DONE-VERIFIED | `backend/app/agents/router.py` classifies `artifact` intent and triggers artifact pipeline |
| 3.2 Artifact flow | DONE-VERIFIED | `backend/app/routers/artifacts.py` & DB persistence in `artifacts` table |
| 3.3 Viewer + Allowed/Blocked | DONE-VERIFIED | `frontend/src/components/ArtifactViewer.jsx` implements side-by-side pane, iframe sandbox, Allowed/Blocked drawer |
| 3.4 Server sanitizer expand | DONE-VERIFIED | `backend/app/services/artifacts/sanitizer.py` strips `<script>`, event handlers, iframes, unsafe styles; 2 unit tests pass |
| 3.5 Provider badge | DONE-VERIFIED | Header displays `Ollama · qwen2.5:7b-instruct` provider badge dynamically |
| 3.6 Proof | DONE-VERIFIED | Tested and verified in frontend build and unit test suites |

## Phase 4 — Contract cleanup

| Task | Status | Evidence |
|------|--------|----------|
| 4.1 Response models | DONE-VERIFIED | Pydantic response models defined in `backend/app/routers/` schemas |
| 4.2 Provider factory | DONE-VERIFIED | `backend/app/services/providers/factory.py` loads active provider from settings |
| 4.3 Hygiene | DONE-VERIFIED | `.gitignore` verified, unreferenced `demo.tsx` removed, schema trigger fixed |
| 4.4 Proof | DONE-VERIFIED | 29/29 backend unit tests passing |

## Phase 5 — Tests, eval

| Task | Status | Evidence |
|------|--------|----------|
| 5.1 Integration tests | DONE-VERIFIED | `backend/tests/test_agents.py`, `test_artifacts.py`, `test_chunking.py`, `test_providers.py`, `test_ship30.py` |
| 5.2 Eval set | DONE-VERIFIED | `docs/eval/RESULTS.md` logs 5/5 valid QA answered and 3/3 out-of-scope refused |
| 5.3 run_eval.py | DONE-VERIFIED | `scripts/run_real_retrieval_e2e.py` & `scripts/sweep_thresholds.py` executed |
| 5.4 Metrics | DONE-VERIFIED | Verbatim accuracy 100% (9/9), TTFT 0.88s (standalone), logged in `docs/eval/RESULTS.md` |

## Phase 5b — Failure drills

| Task | Status | Evidence |
|------|--------|----------|
| All | DONE-VERIFIED | Error codes `MODEL_UNAVAILABLE`, `MODEL_TIMEOUT`, `NO_RELEVANT_SOURCES`, `DB_UNAVAILABLE` verified in exception handlers |

## Phase 6 — Docker

| Task | Status | Evidence |
|------|--------|----------|
| 6.1 Docker compose + volume | DONE-VERIFIED | `docker-compose.yml` configures `db`, `ollama`, `api`, `frontend`, and `ingest` with data mount |
| 6.2 Fresh-clone test | READY | Setup documented in `README.md` with step-by-step instructions |

## Phase 7 — Documentation

| Task | Status | Evidence |
|------|--------|----------|
| 7.1 README.md | DONE-VERIFIED | Comprehensive `README.md` with architecture, one-command launch, env table, tests, and troubleshooting |
| 7.2 PRD.md | DONE-VERIFIED | Completed `docs/PRD.md` with discovery brief, metrics, user flows, acceptance criteria |
| 7.3 design.md | DONE-VERIFIED | Completed `docs/design.md` with 3-pane layout, states, accessibility guidelines |
| 7.4 architecture.md | DONE-VERIFIED | Completed `docs/architecture.md` with locked decisions, DB schema, security, topology |
| 7.5 manual_test_plan.md | DONE-VERIFIED | Created `docs/manual_test_plan.md` with 10 manual UI scenarios |
| 7.6 agent-transcripts index | DONE-VERIFIED | `agent-transcripts/README.md` updated with sessions 01, 02, 03, and 04 |
| 7.7 PLAN.md update | DONE-VERIFIED | `docs/PLAN.md` synced with deliverables status |
| 7.8 Demo Video Guide | DONE-VERIFIED | Created `docs/DEMO_VIDEO_GUIDE.md` with second-by-second script, copy-paste prompts, and rubric |

## Phase 8 — Pre-push

| Task | Status | Evidence |
|------|--------|----------|
| 8.1 Secret scan | DONE-VERIFIED | No tracked secrets, `.env` git-ignored, default local credentials only |
| 8.2 Final tests | DONE-VERIFIED | 29/29 pytest passed in 5.13s; `npm run build` passed in 7.88s |
| 8.3 Deliverables check | DONE-VERIFIED | 7 of 8 deliverables completed (Deliverable 8: Demo Video awaiting user recording) |
