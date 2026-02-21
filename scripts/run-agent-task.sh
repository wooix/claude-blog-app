#!/usr/bin/env bash
# 에이전트 작업 실행 — Inbox 이슈를 가져와 D→C→I 루프 실행
# 사용법: ./run-agent-task.sh [--issue <번호>]
#
# 동작 흐름:
#   1. Inbox에서 다음 이슈 조회 (또는 --issue로 지정)
#   2. 상태 → "In progress" (Develop 단계)
#   3. Claude Code로 구현 프롬프트 출력 (수동 실행용)
#   4. 완료 후 상태 → "In review" (Critique 단계)
#   5. Gemini CLI로 코드 리뷰
#   6. 상태 → "Done"

set -e
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$SCRIPTS_DIR")"

# 인자 파싱
ISSUE_NUMBER=""
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --issue) ISSUE_NUMBER="$2"; shift ;;
  esac
  shift
done

# 1) 다음 이슈 조회
if [ -z "$ISSUE_NUMBER" ]; then
  echo "📋 Inbox에서 다음 작업 조회 중..."
  TASK=$("$SCRIPTS_DIR/get-next-task.sh")
  ERROR=$(echo "$TASK" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error',''))" 2>/dev/null)
  if [ -n "$ERROR" ]; then
    echo "ℹ️  $ERROR"
    exit 0
  fi
  ISSUE_NUMBER=$(echo "$TASK" | python3 -c "import sys,json; print(json.load(sys.stdin)['number'])")
  ISSUE_TITLE=$(echo "$TASK" | python3 -c "import sys,json; print(json.load(sys.stdin)['title'])")
  ISSUE_BODY=$(echo "$TASK" | python3 -c "import sys,json; print(json.load(sys.stdin)['body'])")
else
  ISSUE_TITLE=$(gh issue view "$ISSUE_NUMBER" --repo wooix/claude-blog-app --json title -q '.title')
  ISSUE_BODY=$(gh issue view "$ISSUE_NUMBER" --repo wooix/claude-blog-app --json body -q '.body')
fi

echo ""
echo "========================================"
echo "  작업 시작: Issue #$ISSUE_NUMBER"
echo "  제목: $ISSUE_TITLE"
echo "========================================"

# 2) 상태 → In progress
echo ""
echo "🔵 [Develop] 상태를 'In progress'로 변경..."
"$SCRIPTS_DIR/update-issue-status.sh" "$ISSUE_NUMBER" "In progress"

# 3) Claude Code 프롬프트 생성
PROMPT="다음 GitHub Issue를 구현해줘.

Issue #$ISSUE_NUMBER: $ISSUE_TITLE

$ISSUE_BODY

구현 후:
1. 변경된 파일 목록을 알려줘
2. 테스트 방법을 알려줘
3. project_doc/PROGRESS.md 를 업데이트해줘"

echo ""
echo "📝 [Develop] Claude Code 프롬프트:"
echo "---"
echo "$PROMPT"
echo "---"
echo ""
echo "위 프롬프트로 Claude Code에서 구현을 진행하세요."
echo "구현 완료 후 아래 명령으로 Critique 단계를 시작하세요:"
echo ""
echo "  $SCRIPTS_DIR/critique.sh $ISSUE_NUMBER"
