"""
ClaudeCoevolution Telegram 봇
아이디어를 Telegram으로 받아 Claude API로 정제 후 GitHub Issue를 생성합니다.

실행: uv run python bot.py
"""

import os
import json
import logging
import subprocess
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import anthropic

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ALLOWED_USER_IDS = {
    int(uid.strip())
    for uid in os.environ.get("ALLOWED_USER_IDS", "").split(",")
    if uid.strip()
}
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GITHUB_OWNER = os.environ.get("GITHUB_OWNER", "wooix")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "claude-blog-app")
GITHUB_PROJECT_NUMBER = os.environ.get("GITHUB_PROJECT_NUMBER", "11")

claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# 임시 저장소: user_id → 생성된 이슈 초안
pending_issues: dict[int, dict] = {}


def is_allowed(user_id: int) -> bool:
    if not ALLOWED_USER_IDS:
        return True  # 허용 목록이 비어있으면 전체 허용
    return user_id in ALLOWED_USER_IDS


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("❌ 접근 권한이 없습니다.")
        return
    await update.message.reply_text(
        "👋 ClaudeCoevolution 봇입니다.\n\n"
        "아이디어나 개선 사항을 자유롭게 입력하면\n"
        "GitHub Issue로 정리해 드립니다.\n\n"
        "📌 명령어:\n"
        "  /start  — 시작\n"
        "  /status — Project 현황 조회\n"
        "  /help   — 도움말"
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("❌ 접근 권한이 없습니다.")
        return
    await update.message.reply_text("⏳ GitHub Project 조회 중...")
    try:
        result = subprocess.run(
            ["gh", "project", "item-list", GITHUB_PROJECT_NUMBER,
             "--owner", GITHUB_OWNER, "--format", "json", "--limit", "20"],
            capture_output=True, text=True, check=True
        )
        items = json.loads(result.stdout).get("items", [])
        if not items:
            await update.message.reply_text("📋 현재 등록된 작업이 없습니다.")
            return

        lines = [f"📋 *ClaudeCoevolution 현황* ({len(items)}건)\n"]
        for item in items:
            status = item.get("status", "?")
            title = item.get("title", "제목 없음")
            emoji = {"Backlog": "📥", "In progress": "🔵", "In review": "🟡", "Done": "✅"}.get(status, "⬜")
            lines.append(f"{emoji} {title}")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"status 조회 실패: {e}")
        await update.message.reply_text("❌ 조회 중 오류가 발생했습니다.")


async def handle_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """일반 텍스트 메시지 → 아이디어 정제 → 이슈 초안 생성"""
    if not is_allowed(update.effective_user.id):
        return

    idea = update.message.text.strip()
    if not idea:
        return

    await update.message.reply_text("🤔 Claude가 아이디어를 정리하고 있습니다...")

    try:
        # Claude API로 GitHub Issue 형식 생성
        response = claude.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": f"""다음 아이디어를 GitHub Issue 형식으로 정리해줘.

아이디어: {idea}

다음 JSON 형식으로만 응답해줘 (다른 텍스트 없이):
{{
  "title": "간결한 이슈 제목 (한국어, 50자 이내)",
  "body": "## 목표\\n\\n내용\\n\\n## 작업 항목\\n\\n- [ ] 항목1\\n\\n## 완료 조건\\n\\n내용",
  "phase": "해당 Phase 번호 (1~4, 모르면 1)",
  "priority": "P0/P1/P2 중 하나"
}}"""
            }]
        )

        raw = response.content[0].text.strip()
        # JSON 블록 추출
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        draft = json.loads(raw)

    except Exception as e:
        logger.error(f"Claude API 오류: {e}")
        await update.message.reply_text("❌ 아이디어 정제 중 오류가 발생했습니다. 다시 시도해주세요.")
        return

    # 초안 저장
    user_id = update.effective_user.id
    pending_issues[user_id] = {"draft": draft, "original": idea}

    # 미리보기 전송
    preview = (
        f"📝 *이슈 초안*\n\n"
        f"**제목**: {draft['title']}\n"
        f"**우선순위**: {draft.get('priority', 'P2')}\n\n"
        f"{draft['body'][:400]}{'...' if len(draft['body']) > 400 else ''}"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ 등록", callback_data=f"create_{user_id}"),
            InlineKeyboardButton("✏️ 수정 요청", callback_data=f"revise_{user_id}"),
            InlineKeyboardButton("❌ 취소", callback_data=f"cancel_{user_id}"),
        ]
    ])

    await update.message.reply_text(preview, reply_markup=keyboard, parse_mode="Markdown")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """인라인 버튼 콜백 처리"""
    query = update.callback_query
    await query.answer()

    action, user_id_str = query.data.rsplit("_", 1)
    user_id = int(user_id_str)

    if action == "cancel":
        pending_issues.pop(user_id, None)
        await query.edit_message_text("❌ 취소되었습니다.")
        return

    if action == "revise":
        await query.edit_message_text(
            "✏️ 수정하고 싶은 내용을 입력해주세요.\n"
            "원본 아이디어를 다시 보내주셔도 됩니다."
        )
        return

    if action == "create":
        entry = pending_issues.get(user_id)
        if not entry:
            await query.edit_message_text("❌ 초안을 찾을 수 없습니다. 다시 시도해주세요.")
            return

        draft = entry["draft"]
        await query.edit_message_text("⏳ GitHub Issue 생성 중...")

        try:
            # GitHub Issue 생성
            result = subprocess.run(
                [
                    "gh", "issue", "create",
                    "--repo", f"{GITHUB_OWNER}/{GITHUB_REPO}",
                    "--title", draft["title"],
                    "--body", draft["body"],
                    "--label", f"phase:{draft.get('phase', 1)}",
                ],
                capture_output=True, text=True, check=True
            )
            issue_url = result.stdout.strip()
            issue_number = issue_url.split("/")[-1]

            # Project에 추가
            subprocess.run(
                ["gh", "project", "item-add", GITHUB_PROJECT_NUMBER,
                 "--owner", GITHUB_OWNER, "--url", issue_url],
                capture_output=True, check=True
            )

            pending_issues.pop(user_id, None)
            await query.edit_message_text(
                f"✅ *Issue #{issue_number} 생성 완료!*\n\n"
                f"📌 {draft['title']}\n\n"
                f"🔗 {issue_url}\n\n"
                f"Project Inbox에 추가되었습니다.",
                parse_mode="Markdown"
            )

        except subprocess.CalledProcessError as e:
            logger.error(f"GitHub Issue 생성 실패: {e.stderr}")
            await query.edit_message_text(
                f"❌ Issue 생성 실패:\n{e.stderr[:200]}"
            )


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_idea))

    logger.info("🤖 ClaudeCoevolution Telegram 봇 시작됨 (Polling 모드)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
