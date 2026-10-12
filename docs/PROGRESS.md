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
