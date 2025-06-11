from __future__ import annotations
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
)
from services import ui

logger = logging.getLogger(__name__)

IMAGE = "images/bot.jpg"


# клавиатура
def _kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Случайный факт",     callback_data=ui.CB_RANDOM_FACT)],
        [InlineKeyboardButton("🤖 ChatGPT",            callback_data=ui.CB_GPT)],
        [InlineKeyboardButton("🗣️ Диалог с личностью", callback_data=ui.CB_PERSONA_TALK)],
        [InlineKeyboardButton("❓ Квиз",               callback_data=ui.CB_QUIZ_RUN)],
        [InlineKeyboardButton("🍱 Меню на неделю",     callback_data=ui.CB_COOK)],
    ])


# показать меню
async def show_main_menu(update: Update,
                         context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.message.delete()
        except Exception:
            pass

    await update.effective_message.reply_photo(
        IMAGE,
        caption="👋 Привет! Выберите режим работы:",
        reply_markup=_kb(),
    )
    logger.info("Меню показано пользователю %s", update.effective_user.id)


def build_basic_handler() -> list:
    return [
        CommandHandler("start", show_main_menu),
        CallbackQueryHandler(show_main_menu, pattern=f"^{ui.CB_MAIN_MENU}$"),
    ]
