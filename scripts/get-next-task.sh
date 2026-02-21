#!/usr/bin/env bash
# 다음 작업 조회 — GitHub Project #11 (ClaudeCoevolution) Inbox 이슈 반환
# 사용법: ./get-next-task.sh
# 출력: JSON (이슈 번호, 제목, 본문, URL)

set -e

OWNER="wooix"
PROJECT_NUMBER="11"
REPO="claude-blog-app"

# Project에서 Inbox 상태(Backlog) 아이템 조회
ITEMS=$(gh api graphql -f query='
{
  user(login: "'"$OWNER"'") {
    projectV2(number: '"$PROJECT_NUMBER"') {
      items(first: 20) {
        nodes {
          id
          fieldValues(first: 10) {
            nodes {
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                field { ... on ProjectV2SingleSelectField { name } }
              }
            }
          }
          content {
            ... on Issue {
              number
              title
              body
              url
              state
            }
          }
        }
      }
    }
  }
}')

# Backlog(=Inbox) 상태이며 Open인 이슈만 필터링
NEXT=$(echo "$ITEMS" | python3 -c "
import sys, json

data = json.load(sys.stdin)
nodes = data['data']['user']['projectV2']['items']['nodes']

for node in nodes:
    content = node.get('content', {})
    if not content or content.get('state') != 'OPEN':
        continue

    status = None
    for fv in node.get('fieldValues', {}).get('nodes', []):
        if fv.get('field', {}).get('name') == 'Status':
            status = fv.get('name')

    if status in ('Backlog', 'Inbox', None):
        print(json.dumps({
            'item_id': node['id'],
            'number': content['number'],
            'title': content['title'],
            'body': content.get('body', ''),
            'url': content['url'],
            'status': status
        }, ensure_ascii=False))
        break
" 2>/dev/null)

if [ -z "$NEXT" ]; then
  echo '{"error": "Inbox에 처리할 이슈가 없습니다."}'
  exit 0
fi

echo "$NEXT"
