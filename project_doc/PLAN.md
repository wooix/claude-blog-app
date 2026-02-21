# PLAN.md — 로드맵

최종 업데이트: 2026-02-21

---

## 비전

**Claude 공진화(CoEvolution) 에이전트 시스템** — 스스로 개발하고, 비판하고, 개선하는 자율 루프:

```
[사용자 (Telegram)]
       │ 아이디어 입력
       ▼
[Telegram Polling 봇] → Claude API로 정제 → 승인
       │
       ▼
[GitHub Issue → Project Inbox]
       │
       ▼
[Claude Code] Develop → Critique → Improve → 반복 or Done
       │
       ▼
[Telegram 완료 알림]
```

---

## 단계별 개요

| 단계 | 이름 | GitHub Issue | 상태 |
|------|------|-------------|------|
| 1 | 블로그 CRUD (웹앱 기반 구축) | #1 | 🔄 진행 중 |
| 2 | GitHub Project 연동 | #2 | ⬜ 계획됨 |
| 3 | Telegram 봇 — 아이디어 → Issue | #3 | ⬜ 계획됨 |
| 4 | D→C→I 에이전트 루프 자동화 | #4 | ⬜ 계획됨 |

---

## Phase 1 — 블로그 앱 (Issue #1)

### 잔여 작업
- [ ] 외부 환경에서 프론트엔드 UI 검증 (비 Lima 환경)
- [ ] 클린 환경에서 `start.sh` 전체 흐름 테스트
- [ ] `GET /health` 엔드포인트 추가 (준비 상태 확인용)
- [ ] `uv.lock` git 추적 여부 결정

---

## Phase 2 — GitHub Project 연동 (Issue #2)

**목표**: 에이전트가 GitHub Project #11 보드를 읽고 작업을 자율 실행합니다.

### 작업 항목
- [ ] Project #11 Inbox 이슈 조회 스크립트 (`scripts/get-next-task.sh`)
- [ ] 이슈 상태 자동 업데이트 함수 (Inbox → In progress → In review → Done)
- [ ] Claude Code가 이슈 본문을 읽고 구현 시작하는 프롬프트 템플릿
- [ ] 완료 후 이슈 자동 종료 및 커밋 연결

### 구현 방식
```bash
# 에이전트가 실행할 명령
gh project item-list 11 --owner wooix --format json | \
  jq '[.items[] | select(.status == "Inbox")]'
```

---

## Phase 3 — Telegram 봇 (Issue #3)

**목표**: 아이디어를 Telegram으로 보내면 Claude API가 정제 후 GitHub Issue를 생성합니다.

### 아키텍처
```
[Telegram 앱] → Long Polling (서버 불필요)
     ↓
[bot.py — 로컬 실행]
     ├── Claude API: 아이디어 → 구조화된 Issue 초안 생성
     ├── Telegram으로 초안 회신 + 승인 요청
     └── 승인 시 → GitHub Issue 생성 → Project Inbox 등록
```

### 구현 파일 계획
```
telegram-bot/
├── bot.py          ← 메인 Polling 봇
├── claude_agent.py ← Claude API 연동 (아이디어 정제)
├── github_agent.py ← GitHub Issue 생성
└── .env.example    ← TELEGRAM_TOKEN, ANTHROPIC_API_KEY, GITHUB_TOKEN
```

### 핵심 흐름
1. 사용자가 아이디어 텍스트 전송
2. Claude API: "GitHub Issue 형식으로 정제해줘" 프롬프트
3. 봇이 초안을 Telegram으로 회신 + "등록할까요? (y/n)"
4. `y` 응답 시 `gh issue create` 실행 및 Project Inbox에 추가
5. Issue URL을 Telegram으로 회신

---

## Phase 4 — D→C→I 에이전트 루프 (Issue #4)

**목표**: Develop → Critique → Improve 사이클을 에이전트가 자율 반복합니다.

### 루프 구조
```
Issue 선택 (Inbox)
  → Develop: claude -p "Issue 내용 구현해줘" (Claude Code)
  → Critique: gemini --yolo -p "코드 리뷰해줘" (Gemini CLI)
  → Improve:  claude -p "비판 내용 반영해줘" (Claude Code)
  → Iteration++ → 반복 조건 확인
  → Done: 이슈 종료 + Telegram 알림
```

### 반복 종료 조건
- `Critique Score`가 A 또는 B 이상
- `Iteration` >= 3 (최대 반복 횟수 초과)
- 사용자 수동 종료 명령

### 구현 파일 계획
```
agent-loop/
├── run.sh          ← 루프 진입점
├── develop.sh      ← Claude Code 구현 단계
├── critique.sh     ← Gemini CLI 리뷰 단계
├── improve.sh      ← Claude Code 개선 단계
└── notify.sh       ← Telegram 완료 알림
```

---

## 아키텍처 결정 로그

| 날짜 | 결정 사항 | 근거 |
|------|---------|------|
| 2026-02-21 | 모노레포 채택 | 모든 에이전트가 단일 컨텍스트에서 전체 프로젝트 파악 가능 |
| 2026-02-21 | FastAPI + raw sqlite3 | 의존성 최소화, 직접 검사 및 디버깅 용이 |
| 2026-02-21 | 순수 HTML/JS 프론트엔드 | 빌드 단계 없음, Gemini가 직접 읽고 수정 가능 |
| 2026-02-21 | Gemini CLI를 Critique 에이전트로 활용 | Claude와 다른 관점의 코드 리뷰 제공 |
| 2026-02-21 | uv로 Python 관리 | 빠른 속도, 잠금 파일 재현성, venv 관리 불필요 |
| 2026-02-21 | 산출물 한국어 작성 | 사용자 요구 사항 |
| 2026-02-21 | claude-{프로젝트명} 저장소 명명 규칙 | Claude 생성 프로젝트 식별 용이 |
| 2026-02-21 | Telegram Polling 봇 (서버리스) | 로컬 PC에서 실행, 공개 서버 불필요 |
| 2026-02-21 | Board 뷰 (Inbox→In progress→In review→Done) | 반복 루프의 흐름을 시각적으로 표현 |
