# PLAN.md

Last updated: 2026-02-21

---

## Vision

Build a **self-developing, self-diagnosing, self-improving workflow agent system** that:
1. Tracks its own tasks via GitHub Projects (#11)
2. Writes and tests code autonomously
3. Diagnoses failures and iterates
4. Documents its own progress

---

## Phase Overview

| Phase | Name | Status |
|-------|------|--------|
| 1 | Simple Blog CRUD | 🔄 In Progress |
| 2 | GitHub Integration | ⬜ Planned |
| 3 | Agent Loop (self-develop) | ⬜ Planned |
| 4 | Self-diagnosis & Auto-fix | ⬜ Planned |

---

## Phase 1 — Blog App (Remaining Tasks)

### Immediate
- [ ] Push monorepo to GitHub (new remote repo)
- [ ] Verify frontend UI from external environment (non-Lima)
- [ ] Add `uv.lock` to git tracking (reproducible installs)
- [ ] Test `start.sh` end-to-end in clean environment

### Nice to Have (Phase 1 polish)
- [ ] Add `GET /health` endpoint for readiness checks
- [ ] Simple pagination on `GET /posts`
- [ ] Post update (`PATCH /posts/{id}`)

---

## Phase 2 — GitHub Integration

**Goal**: Agent reads GitHub Project #11 board and executes tasks from it.

- [ ] GitHub CLI (`gh`) setup and auth
- [ ] Script to read open issues/cards from Project #11
- [ ] Map GitHub Project items → local task queue
- [ ] Agent picks up task → implements → commits → updates issue

**Key decision**: How to represent agent tasks in GitHub Projects
- Option A: GitHub Issues as task cards (recommended — natural, auditable)
- Option B: Custom JSON task file in repo

---

## Phase 3 — Agent Loop

**Goal**: Agent autonomously develops features end-to-end.

```
GitHub Issue → Agent reads → Plans → Implements → Tests → Commits → Closes Issue
```

- [ ] Claude Code as primary coding agent
- [ ] Gemini CLI as secondary reviewer / UI verifier
- [ ] Trigger: manual (`gemini -p "run next task"`) or cron
- [ ] Success criteria: agent closes its own GitHub issue

---

## Phase 4 — Self-diagnosis & Auto-fix

**Goal**: Agent detects its own failures and recovers.

- [ ] Run tests after each change
- [ ] On failure: agent reads error, proposes fix, retries (max 3)
- [ ] Log all agent actions to `project_doc/agent-log.md`
- [ ] Weekly self-review: compare PLAN vs PROGRESS, identify drift

---

## Architectural Decisions Log

| Date | Decision | Rationale |
|------|---------|-----------|
| 2026-02-21 | Monorepo | Single context for all agents, easy cross-project reference |
| 2026-02-21 | FastAPI + raw sqlite3 | Minimal deps, easy to inspect/debug |
| 2026-02-21 | Plain HTML/JS frontend | No build step, Gemini can read/modify directly |
| 2026-02-21 | Gemini CLI as UI agent | MCP filesystem access, can read code + call APIs |
| 2026-02-21 | uv for Python | Fast, lockfile reproducibility, no venv management |
