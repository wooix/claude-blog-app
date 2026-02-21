# CLAUDE.md — Workflow Agent 모노레포

이 파일은 이 저장소에서 작업하는 모든 AI 에이전트(Claude, Gemini 등)의 **최초 진입점**입니다.
작업 시작 전 반드시 이 파일을 먼저 읽고, 이어서 `project_doc/PROGRESS.md`와 `project_doc/PLAN.md`를 확인하세요.

> **산출물 언어 규칙**: 모든 문서, 주석, 커밋 메시지, 에이전트 로그는 **한국어**로 작성합니다.
> 코드 식별자(변수명, 함수명 등)와 기술 용어는 영어를 유지합니다.

---

## 1. 프로젝트 개요

이 시스템은 **스스로 개발하고, 비판하고, 개선하는 Claude 공진화(CoEvolution) agent 시스템**입니다.
Claude Code, Gemini CLI 등의 AI 에이전트가 협력하여 소프트웨어를 자율적으로 개발·테스트·개선합니다.

GitHub 프로젝트 보드: https://github.com/users/wooix/projects/11 (ClaudeCoevolution)

### 에이전트 워크플로우 전체 구조

```
[사용자 (Telegram)]
       │ 아이디어 입력
       ▼
[Telegram Polling 봇] → Claude API로 아이디어 정제
       │ 승인 시
       ▼
[GitHub Issue 생성] → Project Board: Inbox
       │
       ▼
[Claude Code] ── Develop: 코드 작성 & 커밋
       │
       ├── Critique: 자체 코드 리뷰 (Gemini CLI 또는 claude -p)
       │
       ├── Improve: 비판 반영 리팩토링 & 재구현
       │
       └── 반복(Iteration++) 또는 Done
       │
       ▼
[Telegram 알림] ← 진행 상황 보고
```

### GitHub Project Board 컬럼 (ClaudeCoevolution)

| 컬럼 | 담당 에이전트 | 설명 |
|------|------------|------|
| **Inbox** | — | 새 아이디어/이슈 대기 |
| **In progress** | Claude Code | 초기 구현 진행 중 |
| **In review** | Gemini CLI | 자체 코드 리뷰 & 비판 |
| **Done** | — | 최종 완료 |

커스텀 필드: `Iteration`(반복 횟수), `Critique Score`(A~D), `Source`(Telegram/Manual/Auto), `Branch`

---

## 2. 작업 전 반드시 확인

| 파일 | 목적 |
|------|------|
| `project_doc/PROGRESS.md` | 완료된 작업, 현재 상태, 알려진 이슈 |
| `project_doc/PLAN.md` | 다음 작업, 단계별 로드맵, 아키텍처 결정 사항 |

**규칙**: 코드 작성 전 PROGRESS.md로 현황을 파악하고, 작업 완료 후 PROGRESS.md와 PLAN.md를 반드시 업데이트합니다.

---

## 3. 저장소 구조

```
project/                        ← 모노레포 루트
├── CLAUDE.md                   ← 현재 파일 (가장 먼저 읽기)
├── project_doc/
│   ├── PROGRESS.md             ← 진행 상황 및 완료 항목
│   └── PLAN.md                 ← 로드맵 및 다음 작업
├── blog-app/                   ← Phase 1: 간단한 CRUD 블로그
│   ├── backend/                ← FastAPI + SQLite (Python/uv)
│   │   └── main.py
│   └── frontend/               ← 순수 HTML/JS
│       └── index.html
└── (이후 프로젝트 추가)
```

---

## 4. 기술 스택

| 계층 | 기술 | 비고 |
|------|------|------|
| Python 런타임 | `uv` | 전체 경로: `/home/wooix.linux/.local/bin/uv` |
| JS/TS 런타임 | `bun` | 전체 경로: `/home/wooix.linux/.bun/bin/bun` |
| AI CLI | Gemini CLI v0.29.5 | 설정: `~/.gemini/settings.json` |
| 백엔드 | FastAPI + SQLite | ORM 미사용, raw sqlite3 |
| 프론트엔드 | 순수 HTML/JS | 프레임워크 없음 |
| 버전 관리 | Git (모노레포) | 브랜치: `main` |

**주의**: `uv`와 `bun`은 비대화형 셸에서 PATH에 자동 등록되지 않습니다.
전체 경로를 사용하거나 `export PATH="/home/wooix.linux/.local/bin:/home/wooix.linux/.bun/bin:$PATH"`를 앞에 추가하세요.

---

## 5. 프로젝트 실행

### blog-app
```bash
cd /home/wooix.linux/project/blog-app
./start.sh
# 백엔드 API : http://localhost:8000
# API 문서   : http://localhost:8000/docs
# 프론트엔드 : http://localhost:3000
```

수동 실행:
```bash
# 백엔드
export PATH="/home/wooix.linux/.local/bin:$PATH"
cd blog-app/backend && uv run uvicorn main:app --reload --port 8000

# 프론트엔드 (정적 파일)
cd blog-app/frontend && bun x serve . --port 3000
```

---

## 6. Gemini CLI 사용법

```bash
# 대화형 (TUI)
gemini

# 헤드리스
gemini -p "프롬프트"

# 헤드리스 + 자동 승인 (yolo 모드)
gemini --yolo -p "프롬프트"
```

MCP 서버는 `~/.gemini/settings.json`에 설정되어 있습니다:
- `blog-filesystem`: 이 저장소 파일 읽기/쓰기 접근
- `blog-fetch`: HTTP 요청 (`uvx mcp-server-fetch`)

---

## 7. 에이전트 작업 규칙

1. **읽고 나서 수정**: 파일 수정 전 반드시 해당 파일을 먼저 읽습니다.
2. **작업 후 문서 갱신**: 의미 있는 변경 후에는 `PROGRESS.md`와 `PLAN.md`를 업데이트합니다.
3. **작은 단위 커밋**: 논리적 작업 단위마다 커밋합니다.
4. **고립 작업 금지**: 모든 작업은 `PLAN.md` 항목 및 GitHub Issue와 연결되어야 합니다.
5. **완료 전 검증**: 동작을 확인한 후 PROGRESS.md에 완료로 기록합니다.
6. **한국어 산출물**: 문서, 주석, 커밋 메시지는 모두 한국어로 작성합니다.
7. **Issue 상태 동기화**: 작업 시작 시 Issue를 `In progress`로, 리뷰 시 `In review`로, 완료 시 `Done`으로 변경합니다.
8. **Critique 필수**: 모든 구현은 최소 1회 자체 리뷰(Critique) 단계를 거칩니다.

---

## 8. 환경 정보

- OS: Linux (Lima 컨테이너)
- 셸: bash
- 이 환경에서는 브라우저 UI 확인 불가 — UI 변경 사항은 GitHub에 푸시 후 외부 환경에서 검증합니다.
