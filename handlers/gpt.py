from __future__ import annotations
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from services.openai_client import ask_chatgpt
from services import ui
from handlers import basic

logger = logging.getLogger(__name__)

# константы
IMAGE = "images/chatgpt.jpg"
ASK   = 0
CB_STOP = "gpt_stop"

# клавиатура под ответами
def _kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🚪 Закончить",   callback_data=CB_STOP),
        InlineKeyboardButton("🔙 Главное меню", callback_data=ui.CB_MAIN_MENU),
    ]])


async def _end_and_menu(update: Update,
                        context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.message.delete()
        except Exception:
            pass
    await basic.show_main_menu(update, context)
    return ConversationHandler.END


async def start(update: Update,
                context: ContextTypes.DEFAULT_TYPE) -> int:
    """Точка входа (команда /gpt или кнопка из главного меню)."""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.delete()

    await update.effective_message.reply_photo(
        IMAGE,
        caption="Спросите меня о чём-нибудь!",
        reply_markup=_kb(),
    )
    return ASK


async def reply(update: Update,
                context: ContextTypes.DEFAULT_TYPE) -> int:
    question = update.message.text
    try:
        answer = await ask_chatgpt(question)
    except Exception as exc:                  # noqa: BLE001
        logger.exception("GPT error: %s", exc)
        answer = "⚠️ Не удалось получить ответ. Попробуйте ещё раз."

    await update.message.reply_text(answer, reply_markup=_kb())
    return ASK


def build_gpt_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("gpt", start),
            CallbackQueryHandler(start, pattern=f"^{ui.CB_GPT}$"),
        ],
        states={
            ASK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, reply),
                CallbackQueryHandler(_end_and_menu, pattern=f"^{CB_STOP}$"),
                CallbackQueryHandler(_end_and_menu,
                                    pattern=f"^{ui.CB_MAIN_MENU}$"),
            ]
        },
        fallbacks=[CallbackQueryHandler(
            _end_and_menu,
            pattern=f"^({CB_STOP}|{ui.CB_MAIN_MENU})$",
        )],
        per_chat=True,
        per_user=False,
    )
