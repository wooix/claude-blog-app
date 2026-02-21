# PROGRESS.md

Last updated: 2026-02-21

---

## Phase 1 — Blog App (Simple CRUD)

### Status: ✅ Backend Complete / 🔲 UI Not Yet Verified

### Completed
- [x] Monorepo initialized at `/home/wooix.linux/project/`
- [x] `CLAUDE.md` created (agent entry point)
- [x] `project_doc/PROGRESS.md` + `PLAN.md` scaffolded
- [x] **Backend**: FastAPI + SQLite app (`blog-app/backend/main.py`)
  - `GET    /posts`       — list all posts (newest first)
  - `GET    /posts/{id}`  — get single post
  - `POST   /posts`       — create post `{title, content}`
  - `DELETE /posts/{id}`  — delete post
  - Auto-creates `blog.db` on startup
- [x] **Frontend**: `blog-app/frontend/index.html`
  - Write & submit post form
  - Post list with expand-on-click detail
  - Delete button per post
  - Error/success messages
- [x] `blog-app/start.sh` — one-command startup
- [x] Gemini CLI MCP servers configured in `~/.gemini/settings.json`
  - `blog-filesystem` (npx @modelcontextprotocol/server-filesystem)
  - `blog-fetch` (uvx mcp-server-fetch)
- [x] Gemini CLI `--yolo` mode verified: successfully called `GET /posts`

### Known Issues / Limitations
- `blog-fetch` MCP server (`uvx mcp-server-fetch`) loads but Gemini uses curl fallback — acceptable
- UI has **not** been visually verified (Lima container, no browser access)
- `start.sh` frontend uses `bun x serve` — needs bun in PATH
- `uv.lock` excluded from git (added to .gitignore) — consider tracking it for reproducibility

### Test Results (2026-02-21)
```
GET  /posts       → 200 [] (empty)
POST /posts       → 201 {id:1, title:"Hello World", ...}
GET  /posts       → 200 [{id:1, ...}]
GET  /posts/1     → 200 {id:1, ...}
Gemini --yolo GET → ✅ returns JSON correctly
```

---

## Environment

| Item | Value |
|------|-------|
| Host | Lima container (Linux) |
| Python | 3.13.7 via uv 0.10.4 |
| Node | v20.19.4 |
| Bun | 1.3.9 |
| Gemini CLI | 0.29.5 |
| Git remote | Not yet configured |
