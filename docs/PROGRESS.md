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
| 2.1 Rewrite SKILL.md | PENDING | |
| 2.2 Pipeline generator.py | PENDING | |
| 2.3 Mock tests | PENDING | |
| 2.4 Real essay run | PENDING | |

## Phase 3 — Artifacts, viewer, provider badge

| Task | Status | Evidence |
|------|--------|----------|
| 3.1 Router update | PENDING | |
| 3.2 Artifact flow | PENDING | |
| 3.3 Viewer + Allowed/Blocked | PENDING | |
| 3.4 Server sanitizer expand | PENDING | |
| 3.5 Provider badge | PENDING | |
| 3.6 Proof | PENDING | |

## Phase 4 — Contract cleanup

| Task | Status | Evidence |
|------|--------|----------|
| 4.1 Response models | PENDING | |
| 4.2 Provider factory | PENDING | |
| 4.3 Hygiene | SKIPPED | Per priority instructions |
| 4.4 Proof | PENDING | |

## Phase 5 — Tests, eval

| Task | Status | Evidence |
|------|--------|----------|
| 5.1 Integration tests | PENDING | |
| 5.2 Eval set | PENDING | |
| 5.3 run_eval.py | PENDING | |
| 5.4 Metrics | PENDING | |

## Phase 5b — Failure drills

| Task | Status | Evidence |
|------|--------|----------|
| All | SKIPPED | Per priority instructions |

## Phase 6 — Docker

| Task | Status | Evidence |
|------|--------|----------|
| 6.1 Docker compose + gpu | PENDING | |
| 6.2 Fresh-clone test | PENDING | |

## Phase 7 — Documentation

| Task | Status | Evidence |
|------|--------|----------|
| 7.1 README.md | PENDING | |
| 7.2 PRD.md | PENDING | |
| 7.3 design.md | PENDING | |
| 7.4 architecture.md | PENDING | |
| 7.5 manual_test_plan.md | PENDING | |
| 7.6 agent-transcripts index | PENDING | |
| 7.7 PLAN.md update | PENDING | |

## Phase 8 — Pre-push

| Task | Status | Evidence |
|------|--------|----------|
| 8.1 Secret scan | PENDING | |
| 8.2 Final tests | PENDING | |
| 8.3 Deliverables check | PENDING | |
