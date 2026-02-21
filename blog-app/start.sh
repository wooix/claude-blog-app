#!/usr/bin/env bash
set -e

export PATH="$HOME/.local/bin:$HOME/.bun/bin:$PATH"
ROOT="$(cd "$(dirname "$0")" && pwd)"

# Backend
echo "[1/2] Starting backend (FastAPI)..."
cd "$ROOT/backend"
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend
sleep 2
echo "      -> http://localhost:8000/docs"

# Frontend (simple static server via bun)
echo "[2/2] Starting frontend..."
cd "$ROOT/frontend"
bun x serve . --port 3000 --no-request-logging &
FRONTEND_PID=$!

echo ""
echo "======================================"
echo "  Blog App is running!"
echo "  Frontend : http://localhost:3000"
echo "  API Docs : http://localhost:8000/docs"
echo "======================================"
echo ""
echo "Press Ctrl+C to stop."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo Stopped." INT TERM
wait
