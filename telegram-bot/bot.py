"""
ClaudeCoevolution Telegram 봇
아이디어를 Telegram으로 받아 Gemini CLI로 정제 후 GitHub Issue를 생성합니다.

API 키 불필요 — Gemini CLI OAuth 인증 사용 (gemini --yolo -p)
실행: uv run python bot.py
"""

import asyncio
import json
import logging
import os
import subprocess
import textwrap
from datetime import datetime

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

# ─── 로깅 설정 ──────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("bot")

# ─── 환경 변수 ───────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ALLOWED_USER_IDS = {
    int(uid.strip())
    for uid in os.environ.get("ALLOWED_USER_IDS", "").split(",")
    if uid.strip()
}
GITHUB_OWNER          = os.environ.get("GITHUB_OWNER", "wooix")
GITHUB_REPO           = os.environ.get("GITHUB_REPO", "claude-blog-app")
GITHUB_PROJECT_NUMBER = os.environ.get("GITHUB_PROJECT_NUMBER", "11")
GEMINI_BIN            = "gemini"

# ─── 임시 저장소 ─────────────────────────────────────────────────────────────
pending_issues: dict[int, dict] = {}

# ─── Issue 타입 정의 ─────────────────────────────────────────────────────────
ISSUE_TYPES = {
    "feat":     {"label": "type:feat",     "emoji": "✨", "name": "새 기능"},
    "fix":      {"label": "type:fix",      "emoji": "🐛", "name": "버그 수정"},
    "refactor": {"label": "type:refactor", "emoji": "♻️", "name": "리팩토링"},
    "docs":     {"label": "type:docs",     "emoji": "📝", "name": "문서"},
    "chore":    {"label": "type:chore",    "emoji": "🔧", "name": "유지보수"},
    "test":     {"label": "type:test",     "emoji": "🧪", "name": "테스트"},
}

# ─── Issue 본문 템플릿 ────────────────────────────────────────────────────────
TEMPLATES = {
    "feat": """\
## 목표
{goal}

## 배경 / 동기
{background}

## 작업 항목
{tasks}

## 완료 조건
{acceptance}
""",
    "fix": """\
## 버그 설명
{description}

## 재현 방법
{steps}

## 기대 동작
{expected}

## 실제 동작
{actual}

## 영향 범위
{impact}
""",
    "refactor": """\
## 목적
{goal}

## 현재 문제점
{problems}

## 개선 방향
{approach}

## 주의 사항
{caution}
""",
    "docs": """\
## 목적
{goal}

## 작업 항목
{tasks}
""",
    "chore": """\
## 목적
{goal}

## 작업 항목
{tasks}
""",
    "test": """\
## 테스트 대상
{target}

## 작업 항목
{tasks}

## 완료 조건
{acceptance}
""",
}

GEMINI_PROMPT_TEMPLATE = """\
다음 아이디어를 GitHub Issue JSON으로 정리해줘.

아이디어: {idea}

반드시 아래 JSON 형식으로만 응답해 (코드블록·설명 텍스트 없이 JSON만):
{{
  "type": "<feat|fix|refactor|docs|chore|test>",
  "title": "<타입 prefix 없이 제목만, 한국어, 60자 이내>",
  "phase": <1~4, 해당 없으면 1>,
  "priority": "<P0|P1|P2>",
  "fields": {{
    {field_hints}
  }}
}}

타입별 fields 설명:
- feat:     goal(목표), background(배경), tasks(작업항목 마크다운 체크리스트), acceptance(완료조건)
- fix:      description(버그설명), steps(재현방법), expected(기대동작), actual(실제동작), impact(영향범위)
- refactor: goal(목적), problems(현재문제점), approach(개선방향), caution(주의사항)
- docs/chore: goal(목적), tasks(작업항목 마크다운 체크리스트)
- test:     target(테스트대상), tasks(작업항목 마크다운 체크리스트), acceptance(완료조건)"""


# ─── 유틸리티 ─────────────────────────────────────────────────────────────────
def is_allowed(user_id: int) -> bool:
    return not ALLOWED_USER_IDS or user_id in ALLOWED_USER_IDS


def md_escape(text: str) -> str:
    """Markdown v1에서 안전하게 표시할 수 있도록 최소 이스케이프"""
    return text.replace("*", "\\*").replace("_", "\\_").replace("`", "\\`")


def build_issue_body(issue_type: str, fields: dict) -> str:
    template = TEMPLATES.get(issue_type, TEMPLATES["feat"])
    # 필드 값이 없으면 'N/A' 대체
    safe = {k: v or "N/A" for k, v in fields.items()}
    try:
        return template.format_map(safe)
    except KeyError:
        return "\n".join(f"**{k}**: {v}" for k, v in fields.items())


def call_gemini(prompt: str) -> str:
    """Gemini CLI 동기 호출 — asyncio.to_thread 로 비동기 래핑하여 사용"""
    log.info("[GEMINI PROMPT]\n%s", textwrap.indent(prompt, "  "))
    result = subprocess.run(
        [GEMINI_BIN, "--yolo", "-p", prompt],
        capture_output=True, text=True, timeout=90,
    )
    response = result.stdout.strip()
    log.info("[GEMINI RESPONSE]\n%s", textwrap.indent(response[:800], "  "))
    if result.returncode != 0:
        raise RuntimeError(f"Gemini CLI 오류 (rc={result.returncode}): {result.stderr[:200]}")
    return response


def parse_gemini_json(raw: str) -> dict:
    """Gemini 응답에서 JSON 추출"""
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rstrip("`").strip()
    start, end = raw.find("{"), raw.rfind("}") + 1
    if start >= 0 and end > start:
        raw = raw[start:end]
    return json.loads(raw)


def refine_idea(idea: str) -> dict:
    """아이디어 → Gemini 정제 → 구조화된 이슈 딕셔너리"""
    prompt = GEMINI_PROMPT_TEMPLATE.format(idea=idea, field_hints="해당 타입에 맞는 필드들")
    raw = call_gemini(prompt)
    data = parse_gemini_json(raw)
    log.info("[ISSUE DRAFT] type=%s title=%s phase=%s priority=%s",
             data.get("type"), data.get("title"), data.get("phase"), data.get("priority"))
    return data


# ─── 핸들러 ───────────────────────────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_allowed(user.id):
        log.warning("[IN] 거부된 사용자: id=%s name=%s", user.id, user.full_name)
        await update.message.reply_text("❌ 접근 권한이 없습니다.")
        return
    log.info("[IN] /start — user=%s(%s)", user.full_name, user.id)
    await update.message.reply_text(
        "👋 ClaudeCoevolution 봇입니다.\n\n"
        "아이디어나 개선 사항을 자유롭게 입력하면\n"
        "Gemini CLI가 분류·정리해서 GitHub Issue로 등록합니다.\n\n"
        "📌 지원 Issue 타입:\n"
        "  ✨ feat — 새 기능\n"
        "  🐛 fix — 버그 수정\n"
        "  ♻️ refactor — 리팩토링\n"
        "  📝 docs — 문서\n"
        "  🔧 chore — 유지보수\n"
        "  🧪 test — 테스트\n\n"
        "📌 명령어:\n"
        "  /start  — 시작\n"
        "  /status — Project 현황 조회\n"
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_allowed(user.id):
        return
    log.info("[IN] /status — user=%s(%s)", user.full_name, user.id)
    await update.message.reply_text("⏳ GitHub Project 조회 중...")
    try:
        result = subprocess.run(
            ["gh", "project", "item-list", GITHUB_PROJECT_NUMBER,
             "--owner", GITHUB_OWNER, "--format", "json", "--limit", "20"],
            capture_output=True, text=True, check=True,
        )
        items = json.loads(result.stdout).get("items", [])
        log.info("[STATUS] %d 건 조회됨", len(items))
        if not items:
            await update.message.reply_text("📋 현재 등록된 작업이 없습니다.")
            return
        emoji_map = {"Backlog": "📥", "In progress": "🔵", "In review": "🟡", "Done": "✅"}
        lines = [f"📋 *ClaudeCoevolution 현황* ({len(items)}건)\n"]
        for item in items:
            status = item.get("status", "?")
            title = md_escape(item.get("title", "제목 없음"))
            lines.append(f"{emoji_map.get(status, '⬜')} {title}")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        log.error("[STATUS] 조회 실패: %s", e)
        await update.message.reply_text("❌ 조회 중 오류가 발생했습니다.")


async def handle_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_allowed(user.id):
        return
    idea = update.message.text.strip()
    if not idea:
        return

    log.info("[IN] 아이디어 수신 — user=%s(%s) text=%r", user.full_name, user.id, idea[:80])
    await update.message.reply_text("🤖 Gemini CLI가 분석 중입니다...")

    try:
        data = await asyncio.to_thread(refine_idea, idea)
    except Exception as e:
        log.error("[GEMINI] 정제 실패: %s", e)
        await update.message.reply_text(f"❌ 정제 실패: {e}\n\n다시 시도해주세요.")
        return

    issue_type = data.get("type", "feat")
    type_info  = ISSUE_TYPES.get(issue_type, ISSUE_TYPES["feat"])
    body       = build_issue_body(issue_type, data.get("fields", {}))

    # 이슈 전체 데이터 임시 저장
    pending_issues[user.id] = {
        "type":     issue_type,
        "title":    data.get("title", "제목 없음"),
        "body":     body,
        "phase":    data.get("phase", 1),
        "priority": data.get("priority", "P2"),
        "original": idea,
    }

    preview = (
        f"{type_info['emoji']} *[{issue_type}] {md_escape(data.get('title',''))}*\n"
        f"Phase {data.get('phase',1)} · {data.get('priority','P2')}\n"
        f"{'─'*30}\n"
        f"{md_escape(body[:500])}{'...' if len(body) > 500 else ''}"
    )

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ 등록", callback_data=f"create_{user.id}"),
        InlineKeyboardButton("✏️ 수정", callback_data=f"revise_{user.id}"),
        InlineKeyboardButton("❌ 취소", callback_data=f"cancel_{user.id}"),
    ]])

    log.info("[OUT] 이슈 초안 전송 — type=%s title=%s", issue_type, data.get("title"))
    await update.message.reply_text(preview, reply_markup=keyboard, parse_mode="Markdown")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, uid_str = query.data.rsplit("_", 1)
    user_id = int(uid_str)
    log.info("[CALLBACK] action=%s user_id=%s", action, user_id)

    if action == "cancel":
        pending_issues.pop(user_id, None)
        await query.edit_message_text("❌ 취소되었습니다.")
        return

    if action == "revise":
        pending_issues.pop(user_id, None)
        await query.edit_message_text("✏️ 아이디어를 다시 입력해주세요.")
        return

    if action == "create":
        entry = pending_issues.get(user_id)
        if not entry:
            await query.edit_message_text("❌ 초안을 찾을 수 없습니다. 다시 시도해주세요.")
            return

        issue_type = entry["type"]
        type_info  = ISSUE_TYPES.get(issue_type, ISSUE_TYPES["feat"])
        title      = f"[{issue_type}] {entry['title']}"

        await query.edit_message_text("⏳ GitHub Issue 생성 중...")
        log.info("[GITHUB] Issue 생성 시작 — title=%s type=%s phase=%s priority=%s",
                 title, issue_type, entry["phase"], entry["priority"])

        try:
            result = subprocess.run(
                [
                    "gh", "issue", "create",
                    "--repo",  f"{GITHUB_OWNER}/{GITHUB_REPO}",
                    "--title", title,
                    "--body",  entry["body"],
                    "--label", f"phase:{entry['phase']}",
                    "--label", type_info["label"],
                ],
                capture_output=True, text=True, check=True,
            )
            issue_url    = result.stdout.strip()
            issue_number = issue_url.split("/")[-1]
            log.info("[GITHUB] Issue 생성 완료 — #%s %s", issue_number, issue_url)

            subprocess.run(
                ["gh", "project", "item-add", GITHUB_PROJECT_NUMBER,
                 "--owner", GITHUB_OWNER, "--url", issue_url],
                capture_output=True, check=True,
            )
            log.info("[GITHUB] Project Inbox 등록 완료 — #%s", issue_number)

            pending_issues.pop(user_id, None)

            msg = (
                f"{type_info['emoji']} *Issue #{issue_number} 생성 완료*\n\n"
                f"*제목*: {md_escape(entry['title'])}\n"
                f"*타입*: {issue_type} ({type_info['name']})\n"
                f"*우선순위*: {entry['priority']}  *Phase*: {entry['phase']}\n\n"
                f"{issue_url}\n\n"
                f"Project Inbox에 추가되었습니다."
            )
            log.info("[OUT] 생성 완료 메시지 전송 — #%s", issue_number)
            await query.edit_message_text(msg, parse_mode="Markdown")

        except subprocess.CalledProcessError as e:
            log.error("[GITHUB] Issue 생성 실패: %s", e.stderr)
            await query.edit_message_text(f"❌ Issue 생성 실패:\n{e.stderr[:300]}")


# ─── 메인 ─────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_idea))

    log.info("🤖 ClaudeCoevolution 봇 시작 (Polling / Gemini CLI)")
    log.info("   허용 사용자: %s", ALLOWED_USER_IDS or "전체")
    log.info("   GitHub: %s/%s  Project #%s", GITHUB_OWNER, GITHUB_REPO, GITHUB_PROJECT_NUMBER)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
