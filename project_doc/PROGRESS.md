# PROGRESS.md — 진행 상황

최종 업데이트: 2026-02-21

---

## Phase 1 — 블로그 앱 (간단한 CRUD)

### 상태: ✅ 백엔드 완료 / 🔲 UI 미검증 (외부 환경 필요)

### 완료 항목
- [x] 모노레포 초기화 (`/home/wooix.linux/project/`)
- [x] `CLAUDE.md` 생성 (에이전트 진입점)
- [x] `project_doc/PROGRESS.md` + `PLAN.md` 작성
- [x] **백엔드**: FastAPI + SQLite (`blog-app/backend/main.py`)
  - `GET    /posts`       — 전체 목록 조회 (최신순)
  - `GET    /posts/{id}`  — 단일 게시글 조회
  - `POST   /posts`       — 게시글 등록 `{title, content}`
  - `DELETE /posts/{id}`  — 게시글 삭제
  - 서버 시작 시 `blog.db` 자동 생성
- [x] **프론트엔드**: `blog-app/frontend/index.html`
  - 글 작성 및 등록 폼
  - 목록 조회 (클릭 시 본문 펼치기)
  - 게시글별 삭제 버튼
  - 성공/오류 메시지 표시
- [x] `blog-app/start.sh` — 원커맨드 실행 스크립트
- [x] Gemini CLI MCP 서버 설정 (`~/.gemini/settings.json`)
  - `blog-filesystem` (npx @modelcontextprotocol/server-filesystem)
  - `blog-fetch` (uvx mcp-server-fetch)
- [x] Gemini CLI `--yolo` 모드 검증: `GET /posts` 정상 호출 확인
- [x] GitHub 원격 저장소 연결: https://github.com/wooix/claude-blog-app
- [x] 산출물 한국어 작성 규칙 CLAUDE.md에 명시
- [x] GitHub Project #11 (ClaudeCoevolution) 보드 구성
  - 커스텀 필드 추가: Iteration, Critique Score, Source, Branch
  - repo → Project 연결 완료
  - Phase별 GitHub Issues 생성 (#1~#4) 및 Project 등록
- [x] CLAUDE.md에 전체 에이전트 워크플로우 아키텍처 반영
- [x] PLAN.md에 Telegram 봇 + D→C→I 루프 상세 계획 반영

### 알려진 이슈 / 제한 사항
- `blog-fetch` MCP 서버(`uvx mcp-server-fetch`) 로드 후 Gemini가 curl 대체 사용 — 기능상 문제 없음
- UI 미검증 — Lima 컨테이너 환경으로 브라우저 접근 불가, GitHub 푸시 후 외부 환경에서 확인 필요
- `start.sh` 프론트엔드 구동 시 `bun`이 PATH에 있어야 함
- `uv.lock` git 제외 중 — 재현 가능성을 위해 추적 고려 필요

### 테스트 결과 (2026-02-21)
```
GET  /posts       → 200 [] (빈 목록)
POST /posts       → 201 {id:1, title:"Hello World", ...}
GET  /posts       → 200 [{id:1, ...}]
GET  /posts/1     → 200 {id:1, ...}
Gemini --yolo GET → ✅ JSON 정상 반환
```

---

## 환경 정보

| 항목 | 값 |
|------|-----|
| 호스트 | Lima 컨테이너 (Linux) |
| Python | 3.13.7 (uv 0.10.4) |
| Node | v20.19.4 |
| Bun | 1.3.9 |
| Gemini CLI | 0.29.5 |
| Git 원격 | https://github.com/wooix/claude-blog-app |
