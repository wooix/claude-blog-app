# CLAUDE.md — Workflow Agent Monorepo

This file is the **primary entry point** for any AI agent (Claude, Gemini, etc.) working in this repository.
Read this file first. Then read `project_doc/PROGRESS.md` and `project_doc/PLAN.md` before taking any action.

---

## 1. Project Overview

This is a **self-developing, self-diagnosing, self-improving workflow agent system**.
The system uses AI agents (Claude Code, Gemini CLI) to autonomously develop, test, and improve software projects.

GitHub Project Board: https://github.com/users/wooix/projects/11

---

## 2. Always Read First

| File | Purpose |
|------|---------|
| `project_doc/PROGRESS.md` | What has been done, current state, known issues |
| `project_doc/PLAN.md` | Upcoming tasks, phases, architectural decisions |

**Rule**: Before writing any code, verify your understanding against PROGRESS.md.
After completing work, update both PROGRESS.md and PLAN.md to reflect the new state.

---

## 3. Repository Structure

```
project/                        ← monorepo root
├── CLAUDE.md                   ← YOU ARE HERE (read first)
├── project_doc/
│   ├── PROGRESS.md             ← current state & done items
│   └── PLAN.md                 ← roadmap & next actions
├── blog-app/                   ← Phase 1: simple CRUD blog
│   ├── backend/                ← FastAPI + SQLite (Python/uv)
│   │   └── main.py
│   └── frontend/               ← Plain HTML/JS
│       └── index.html
└── (future projects added here)
```

---

## 4. Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Python runtime | `uv` | Full path: `/home/wooix.linux/.local/bin/uv` |
| JS/TS runtime | `bun` | Full path: `/home/wooix.linux/.bun/bin/bun` |
| AI CLI | Gemini CLI v0.29.5 | Config: `~/.gemini/settings.json` |
| Backend | FastAPI + SQLite | No ORM, raw sqlite3 |
| Frontend | Plain HTML/JS | No framework |
| Version control | Git (monorepo) | Branch: `main` |

**Important**: `uv` and `bun` are not in PATH by default in non-interactive shells.
Always use full paths or prepend `export PATH="/home/wooix.linux/.local/bin:/home/wooix.linux/.bun/bin:$PATH"`.

---

## 5. Running Projects

### blog-app
```bash
cd /home/wooix.linux/project/blog-app
./start.sh
# Backend API : http://localhost:8000
# API Docs    : http://localhost:8000/docs
# Frontend    : http://localhost:3000
```

Manual start:
```bash
# Backend
export PATH="/home/wooix.linux/.local/bin:$PATH"
cd blog-app/backend && uv run uvicorn main:app --reload --port 8000

# Frontend (static)
cd blog-app/frontend && bun x serve . --port 3000
```

---

## 6. Gemini CLI Usage

```bash
# Interactive (TUI)
gemini

# Headless
gemini -p "your prompt"

# Headless with auto-approve (yolo)
gemini --yolo -p "your prompt"
```

MCP servers are configured in `~/.gemini/settings.json`:
- `blog-filesystem`: read/write access to this repo
- `blog-fetch`: HTTP fetch via `uvx mcp-server-fetch`

---

## 7. Agent Workflow Rules

1. **Read before write**: Always read relevant files before modifying them.
2. **Update docs after work**: After any meaningful change, update `PROGRESS.md` and `PLAN.md`.
3. **Small commits**: Commit after each logical unit of work.
4. **No orphan work**: Every task must be traceable to a PLAN.md entry.
5. **Test before marking done**: Verify changes work before updating PROGRESS.md.

---

## 8. Environment Notes

- OS: Linux (Lima container)
- Shell: bash
- UI cannot be verified in this environment — UI changes must be pushed to GitHub and tested externally.
