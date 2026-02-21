#!/usr/bin/env bash
set -e

export PATH="/home/wooix.linux/.local/bin:/home/wooix.linux/.bun/bin:$PATH"
ROOT="$(cd "$(dirname "$0")" && pwd)"

# 백엔드 시작
echo "[1/2] 백엔드 시작 중 (FastAPI)..."
cd "$ROOT/backend"
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# 백엔드 준비 대기 (최대 10초)
for i in $(seq 1 10); do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "      -> 백엔드 준비 완료 (${i}초)"
    break
  fi
  sleep 1
done

# 프론트엔드 시작
echo "[2/2] 프론트엔드 시작 중..."
cd "$ROOT/frontend"
bun x serve . --port 3000 --no-request-logging &
FRONTEND_PID=$!

echo ""
echo "======================================"
echo "  Blog App 실행 중"
echo "  프론트엔드 : http://localhost:3000"
echo "  API 문서   : http://localhost:8000/docs"
echo "  상태 확인  : http://localhost:8000/health"
echo "======================================"
echo ""
echo "종료하려면 Ctrl+C 를 누르세요."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo '서버가 종료되었습니다.'" INT TERM
wait
