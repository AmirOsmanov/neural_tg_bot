"""
handlers.gpt
============

Модуль «🤖 ChatGPT-диалог».

Позволяет пользователю вести свободную переписку с ChatGPT прямо
внутри Telegram чата.  Реализован как `ConversationHandler`
с единственным состоянием **ASK**:

1. `/gpt` **или** кнопка «ChatGPT» в главном меню → отправляется
   картинка-обложка и клавиатура с кнопками «🚪 Закончить» / «🔙 Главное меню».
2. Пользователь шлёт текстовые сообщения — каждый запрос передаётся
   в OpenAI (`services.openai_client.ask_chatgpt`), ответ отображается
   тем же сообщением бота и сопровождается той же клавиатурой.
3. Нажатие «Закончить» или «Главное меню» завершает диалог
   (`ConversationHandler.END`) и возвращает пользователя в основное меню.

Все переходы работают *per-chat* (одна сессия на чат),
а не *per-user*, чтобы не плодить лишние состояния.
"""

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
    """
        Сформировать inline-клавиатуру, прикрепляемую
        **к каждому** ответу ChatGPT.

        Returns
        -------
        telegram.InlineKeyboardMarkup
            Клавиатура с двумя строками:
            1. «🚪 Закончить» — прерывает диалог (CB_STOP).
            2. «🔙 Главное меню» — тоже завершает диалог, но дополнительно
               выводит главное меню (ui.CB_MAIN_MENU).
    """
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🚪 Закончить",   callback_data=CB_STOP),
        InlineKeyboardButton("🔙 Главное меню", callback_data=ui.CB_MAIN_MENU),
    ]])


async def _end_and_menu(update: Update,
                        context: ContextTypes.DEFAULT_TYPE) -> int:
    """
        Унифицированное завершение диалога.

        • Подтверждает callback (если есть).
        • Пытается удалить сообщение-карточку с обложкой.
        • Показывает главное меню.
        • Завершает разговор с помощью `ConversationHandler.END`.

        Parameters
        ----------
        update : telegram.Update
            CallbackQuery / Message, инициировавший выход.
        context : telegram.ext.ContextTypes.DEFAULT_TYPE
            PTB-контекст (не используется, но нужен по сигнатуре).

        Returns
        -------
        int
            Константа `ConversationHandler.END` для корректного выхода
            из машины состояний.
    """
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
    """
        Запустить «режим ChatGPT».

        Срабатывает на `/gpt` **или** на inline-кнопку из главного меню.
        Отправляет картинку-обложку (`IMAGE`) с подписью и клавиатурой `_kb()`.

        Returns
        -------
        int
            Состояние **ASK** для перехода в приём пользовательских сообщений.
    """
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
    """
        Отправить пользовательский запрос в ChatGPT и показать ответ.

        Пайплайн:
        1. Берём `update.message.text` — текст вопроса.
        2. Вызываем `services.openai_client.ask_chatgpt`.
        3. В случае исключения логируем и отправляем сообщение об ошибке.
        4. Отправляем ответ вместе с клавиатурой `_kb()`.

        Returns
        -------
        int
            Состояние **ASK** — остаёмся в текущем режиме.
    """
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
