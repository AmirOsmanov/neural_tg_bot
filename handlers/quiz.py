from __future__ import annotations
import logging
from telegram import (
    Update, InlineKeyboardMarkup as Mk, InlineKeyboardButton as Btn,
)
from telegram.ext import (
    ContextTypes, ConversationHandler,
    CommandHandler, CallbackQueryHandler,
)
from services.ui import CB_QUIZ_RUN
from services.openai_client import get_quiz_question

logger = logging.getLogger(__name__)
IMAGE = "images/quiz.jpg"

TOPIC, ASK = range(2)

TOPICS = {
    "hist": "История",
    "sci":  "Наука",
    "mov":  "Кино",
}

def _topics_kb() -> Mk:
    return Mk([
        [Btn(name, callback_data=f"quiz_topic:{code}")]
        for code, name in TOPICS.items()
    ])


def _ans_kb(topic: str, q_id: int, options: list[str]) -> Mk:
    return Mk([
        [Btn(txt, callback_data=f"quiz_ans:{q_id}:{i}")]
        for i, txt in enumerate(options)
    ])


def _after_kb(topic: str) -> Mk:
    return Mk([
        [Btn("➕ Ещё вопрос", callback_data=f"quiz_next:{topic}")],
        [Btn("🔙 Главное меню", callback_data="quiz_finish")],
    ])


async def start_quiz_command(update: Update,
                             context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.delete()
    await update.effective_message.reply_photo(
        IMAGE,
        caption="📚 Выберите тему квиза:",
        reply_markup=_topics_kb(),
    )
    return TOPIC


async def choose_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    topic_code = q.data.split(":")[1]
    context.user_data["topic"] = topic_code
    return await _ask_question(q, context)


async def _ask_question(target, context) -> int:
    topic_code = context.user_data["topic"]
    topic_ru   = TOPICS[topic_code]

    q_text, options, right = await get_quiz_question(topic_ru)

    context.user_data["right"] = right

    kb = _ans_kb(topic_code, id(q_text), options)

    try:
        await target.edit_message_caption(q_text, reply_markup=kb)
    except Exception:                               # noqa: BLE001
        await target.message.reply_photo(IMAGE, caption=q_text, reply_markup=kb)

    return ASK


async def handle_answer(update: Update,
                        context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()

    chosen = int(q.data.split(":")[-1])
    right  = context.user_data.get("right", -1)

    msg = "✅ Верно!" if chosen == right else "❌ Неверно!"
    topic_code = context.user_data["topic"]
    await q.message.reply_text(msg, reply_markup=_after_kb(topic_code))
    return ASK


async def next_or_finish(update: Update,
                         context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()

    if q.data.startswith("quiz_next:"):
        return await _ask_question(q, context)

    from handlers.basic import show_main_menu
    await show_main_menu(update, context)
    return ConversationHandler.END


def build_quiz_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("quiz", start_quiz_command),
            CallbackQueryHandler(start_quiz_command, pattern=f"^{CB_QUIZ_RUN}$"),
        ],
        states={
            TOPIC: [CallbackQueryHandler(choose_topic, pattern="^quiz_topic:")],
            ASK: [
                CallbackQueryHandler(handle_answer, pattern="^quiz_ans:"),
                CallbackQueryHandler(next_or_finish,
                                     pattern="^quiz_(next|finish)"),
            ],
        },
        fallbacks=[],
        per_chat=True, per_user=False, per_message=False,
    )
