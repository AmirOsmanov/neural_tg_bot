"""
handlers.basic
==============

Базовый («root») модуль бота, отвечающий за отображение **главного меню**.

* Реагирует на команду `/start`.
* Показывает картинку `images/menu.jpg` и набор inline-кнопок,
  сконструированный локальной фабрикой `_kb()`.
* Предоставляет функцию-builder `build_basic_handler`, которую
  регистрирует `main.py`.

Любые другие обработчики (random-факт, ChatGPT-диалог и т.д.) могут
вызывать `show_main_menu` для возврата пользователя в начальное состояние.
"""

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
    """
        Сформировать inline-клавиатуру главного меню.

        Кнопки:
        ▸ 💬 ChatGPT — открывает диалог с GPT
        ▸ 🎲 Случайный факт
        ▸ 🧑‍🎤 Персона-диалог
        ▸ ❓ Квиз
        ▸ 🍱 Меню на неделю (прямой вызов cook-модуля с лимитом 1200 ккал)

        Returns
        -------
        telegram.InlineKeyboardMarkup
            Объект, пригодный для передачи в `reply_markup`.
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Случайный факт",     callback_data=ui.CB_RANDOM_FACT)],
        [InlineKeyboardButton("🤖 ChatGPT",            callback_data=ui.CB_GPT)],
        [InlineKeyboardButton("🈂️ Переводчик",         callback_data=ui.CB_TRANSLATOR)],
        [InlineKeyboardButton("🗣️ Диалог с личностью", callback_data=ui.CB_PERSONA_TALK)],
        [InlineKeyboardButton("❓ Квиз",               callback_data=ui.CB_QUIZ_RUN)],
        [InlineKeyboardButton("🍱 Меню на неделю",     callback_data=ui.CB_COOK)],
    ])


# показать меню
async def show_main_menu(update: Update,
                         context: ContextTypes.DEFAULT_TYPE) -> None:
    """
        Показать (или обновить) главное меню.

        Работает как обработчик **команды** `/start` и **callback-кнопки**
        «🔙 Главное меню». Универсален: сам определяет, приходит ли запрос
        через `CallbackQuery` или обычное сообщение.

        Parameters
        ----------
        update : telegram.Update
            Объект события Telegram (сообщение или нажатие кнопки).
        context : telegram.ext.ContextTypes.DEFAULT_TYPE
            Контекст выполнения; хранит, например, `bot`, `user_data` и др.

        Side Effects
        ------------
        • Отправляет/редактирует сообщение-картинку с клавиатурой.
        • Логирует факт показа меню.
    """
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
