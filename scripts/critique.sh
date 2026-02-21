#!/usr/bin/env bash
# Critique 단계 — Gemini CLI로 코드 리뷰 후 이슈 상태 업데이트
# 사용법: ./critique.sh <issue_number>

set -e
ISSUE_NUMBER="${1:?이슈 번호를 입력하세요}"
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$SCRIPTS_DIR")"

echo "🟡 [Critique] 이슈 #$ISSUE_NUMBER 코드 리뷰 시작..."
"$SCRIPTS_DIR/update-issue-status.sh" "$ISSUE_NUMBER" "In review"

# 변경된 파일 목록 수집
CHANGED=$(git -C "$ROOT" diff --name-only HEAD~1 HEAD 2>/dev/null || git -C "$ROOT" diff --name-only 2>/dev/null || echo "")

PROMPT="GitHub Issue #$ISSUE_NUMBER 구현 코드를 리뷰해줘.

저장소 경로: $ROOT
최근 변경 파일: $CHANGED

다음 관점에서 리뷰해줘:
1. 코드 품질 (가독성, 단순성)
2. 버그 또는 엣지 케이스 누락
3. 보안 문제
4. 개선 제안 (최대 3가지)

마지막에 종합 평가를 A/B/C/D로 내려줘:
- A: 즉시 Done 가능
- B: 사소한 개선 권장
- C: 중요한 개선 필요
- D: 재작업 필요"

echo ""
echo "🤖 Gemini CLI 리뷰 중..."
REVIEW=$(gemini --yolo -p "$PROMPT" 2>&1)
echo "$REVIEW"

# 리뷰 결과를 GitHub Issue 코멘트로 등록
echo ""
echo "💬 리뷰 결과를 Issue #$ISSUE_NUMBER 에 코멘트로 등록 중..."
gh issue comment "$ISSUE_NUMBER" \
  --repo wooix/claude-blog-app \
  --body "## 🤖 Critique 리뷰 (Gemini CLI)

$REVIEW

---
*자동 생성된 코드 리뷰입니다. \`scripts/critique.sh\`에 의해 실행됨.*"

echo ""
echo "✅ Critique 완료. 결과를 확인하고 다음 단계를 선택하세요:"
echo "  - 개선 필요 시: claude -p '리뷰 결과 반영해줘' 후 git commit"
echo "  - 완료 시:      $SCRIPTS_DIR/update-issue-status.sh $ISSUE_NUMBER Done"
