#!/usr/bin/env bash
# 이슈 상태 업데이트 — GitHub Project #11 컬럼 이동
# 사용법: ./update-issue-status.sh <issue_number> <status>
# status 값: Backlog | In progress | In review | Done
#
# 예시:
#   ./update-issue-status.sh 1 "In progress"   # Develop 시작
#   ./update-issue-status.sh 1 "In review"     # Critique 단계
#   ./update-issue-status.sh 1 "Done"          # 완료

set -e

ISSUE_NUMBER="${1:?이슈 번호를 입력하세요 (예: 1)}"
NEW_STATUS="${2:?상태를 입력하세요 (Backlog|In progress|In review|Done)}"
OWNER="wooix"
PROJECT_NUMBER="11"
REPO="claude-blog-app"

# 1) Project 메타데이터 조회 (프로젝트 ID, Status 필드 ID, 옵션 ID)
META=$(gh api graphql -f query='
{
  user(login: "'"$OWNER"'") {
    projectV2(number: '"$PROJECT_NUMBER"') {
      id
      fields(first: 20) {
        nodes {
          ... on ProjectV2SingleSelectField {
            id
            name
            options { id name }
          }
        }
      }
    }
  }
}')

PROJECT_ID=$(echo "$META" | python3 -c "
import sys,json; d=json.load(sys.stdin)
print(d['data']['user']['projectV2']['id'])")

STATUS_FIELD_ID=$(echo "$META" | python3 -c "
import sys,json; d=json.load(sys.stdin)
for f in d['data']['user']['projectV2']['fields']['nodes']:
    if f.get('name')=='Status': print(f['id']); break")

OPTION_ID=$(echo "$META" | python3 -c "
import sys,json; d=json.load(sys.stdin)
target='$NEW_STATUS'
for f in d['data']['user']['projectV2']['fields']['nodes']:
    if f.get('name')=='Status':
        for o in f.get('options',[]):
            if o['name']==target: print(o['id']); break")

if [ -z "$OPTION_ID" ]; then
  echo "오류: '$NEW_STATUS' 상태를 찾을 수 없습니다."
  echo "사용 가능한 상태: Backlog, In progress, In review, Done"
  exit 1
fi

# 2) Issue → Project Item ID 조회
ITEM_ID=$(gh api graphql -f query='
{
  user(login: "'"$OWNER"'") {
    projectV2(number: '"$PROJECT_NUMBER"') {
      items(first: 50) {
        nodes {
          id
          content {
            ... on Issue { number }
          }
        }
      }
    }
  }
}' | python3 -c "
import sys,json; d=json.load(sys.stdin)
for n in d['data']['user']['projectV2']['items']['nodes']:
    if n.get('content',{}).get('number')==$ISSUE_NUMBER:
        print(n['id']); break")

if [ -z "$ITEM_ID" ]; then
  echo "오류: 이슈 #$ISSUE_NUMBER 를 Project에서 찾을 수 없습니다."
  exit 1
fi

# 3) 상태 업데이트
gh api graphql -f query='
mutation {
  updateProjectV2ItemFieldValue(input: {
    projectId: "'"$PROJECT_ID"'"
    itemId: "'"$ITEM_ID"'"
    fieldId: "'"$STATUS_FIELD_ID"'"
    value: { singleSelectOptionId: "'"$OPTION_ID"'" }
  }) {
    projectV2Item { id }
  }
}' > /dev/null

echo "✅ 이슈 #$ISSUE_NUMBER 상태 → '$NEW_STATUS' 로 변경되었습니다."
