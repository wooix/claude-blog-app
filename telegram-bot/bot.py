"""
ClaudeCoevolution Telegram 봇
아이디어를 Telegram으로 받아 Gemini CLI로 정제 후 GitHub Issue를 생성합니다.

API 키 불필요 — Gemini CLI OAuth 인증 사용 (gemini --yolo -p)
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
GITHUB_OWNER = os.environ.get("GITHUB_OWNER", "wooix")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "claude-blog-app")
GITHUB_PROJECT_NUMBER = os.environ.get("GITHUB_PROJECT_NUMBER", "11")

# Gemini CLI 경로
GEMINI_BIN = "gemini"

# 임시 저장소: user_id → 이슈 초안
pending_issues: dict[int, dict] = {}


def is_allowed(user_id: int) -> bool:
    if not ALLOWED_USER_IDS:
        return True
    return user_id in ALLOWED_USER_IDS


def refine_with_gemini(idea: str) -> dict:
    """Gemini CLI로 아이디어를 GitHub Issue 형식으로 정제"""
    prompt = f"""다음 아이디어를 GitHub Issue 형식으로 정리해줘.

아이디어: {idea}

아래 JSON 형식으로만 응답해줘 (마크다운 코드블록, 설명 텍스트 없이 JSON만):
{{
  "title": "간결한 이슈 제목 (한국어, 50자 이내)",
  "body": "## 목표\\n\\n한 줄 설명\\n\\n## 작업 항목\\n\\n- [ ] 항목1\\n- [ ] 항목2\\n\\n## 완료 조건\\n\\n완료 기준",
  "phase": 1,
  "priority": "P1"
}}"""

    result = subprocess.run(
        [GEMINI_BIN, "--yolo", "-p", prompt],
        capture_output=True,
        text=True,
        timeout=60,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Gemini CLI 오류: {result.stderr[:200]}")

    raw = result.stdout.strip()

    # JSON 블록만 추출
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rstrip("`").strip()

    # 첫 번째 { ... } 블록 추출
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start >= 0 and end > start:
        raw = raw[start:end]

    return json.loads(raw)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("❌ 접근 권한이 없습니다.")
        return
    await update.message.reply_text(
        "👋 ClaudeCoevolution 봇입니다.\n\n"
        "아이디어나 개선 사항을 자유롭게 입력하면\n"
        "Gemini CLI가 정리해서 GitHub Issue로 등록해 드립니다.\n\n"
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

        emoji_map = {
            "Backlog": "📥", "In progress": "🔵",
            "In review": "🟡", "Done": "✅",
        }
        lines = [f"📋 *ClaudeCoevolution 현황* ({len(items)}건)\n"]
        for item in items:
            status = item.get("status", "?")
            title = item.get("title", "제목 없음")
            lines.append(f"{emoji_map.get(status, '⬜')} {title}")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"status 조회 실패: {e}")
        await update.message.reply_text("❌ 조회 중 오류가 발생했습니다.")


async def handle_idea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """텍스트 메시지 → Gemini CLI 정제 → 이슈 초안 미리보기"""
    if not is_allowed(update.effective_user.id):
        return

    idea = update.message.text.strip()
    if not idea:
        return

    await update.message.reply_text("🤖 Gemini가 아이디어를 정리하고 있습니다...")

    try:
        draft = await context.application.run_in_executor(
            None, refine_with_gemini, idea
        )
    except Exception as e:
        logger.error(f"Gemini 정제 실패: {e}")
        await update.message.reply_text(
            "❌ 아이디어 정제 중 오류가 발생했습니다. 다시 시도해주세요."
        )
        return

    user_id = update.effective_user.id
    pending_issues[user_id] = {"draft": draft, "original": idea}

    preview = (
        f"📝 *이슈 초안*\n\n"
        f"*제목*: {draft['title']}\n"
        f"*우선순위*: {draft.get('priority', 'P2')}  "
        f"*Phase*: {draft.get('phase', 1)}\n\n"
        f"{draft['body'][:500]}{'...' if len(draft['body']) > 500 else ''}"
    )

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ 등록", callback_data=f"create_{user_id}"),
        InlineKeyboardButton("✏️ 수정", callback_data=f"revise_{user_id}"),
        InlineKeyboardButton("❌ 취소", callback_data=f"cancel_{user_id}"),
    ]])

    await update.message.reply_text(preview, reply_markup=keyboard, parse_mode="Markdown")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """인라인 버튼 콜백"""
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
            "✏️ 수정 내용을 다시 입력해주세요.\n"
            "아이디어를 다시 보내주셔도 됩니다."
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

            subprocess.run(
                ["gh", "project", "item-add", GITHUB_PROJECT_NUMBER,
                 "--owner", GITHUB_OWNER, "--url", issue_url],
                capture_output=True, check=True
            )

            pending_issues.pop(user_id, None)
            await query.edit_message_text(
                f"✅ *Issue #{issue_number} 생성 완료\\!*\n\n"
                f"📌 {draft['title']}\n\n"
                f"🔗 {issue_url}\n\n"
                f"Project Inbox에 추가되었습니다\\.",
                parse_mode="MarkdownV2"
            )

        except subprocess.CalledProcessError as e:
            logger.error(f"Issue 생성 실패: {e.stderr}")
            await query.edit_message_text(f"❌ Issue 생성 실패:\n{e.stderr[:200]}")


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_idea))

    logger.info("🤖 ClaudeCoevolution Telegram 봇 시작됨 (Polling / Gemini CLI 모드)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
