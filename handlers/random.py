"""
handlers.random
===============

Модуль «🧠 Рандом-факт».

При вызове команды `/random` или нажатии кнопки «🧠 Рандом-факт»
бот запрашивает у ChatGPT короткий (в одну-две строки) интересный
научный факт, предваряющийся подходящим emoji, и отправляет его
пользователю. Под ответом отображаются две inline-кнопки:

* «🧠 Ещё факт»      → запрашивает и показывает новый факт,
  стараясь отредактировать предыдущее сообщение.
* «🔚 Закончить»     → удаляет карточку со фактом
  и открывает **главное меню**.

Для работы модуль использует:
* `services.openai_client.get_random_fact` — асинхронную обёртку
  над ChatGPT;
* константу `CB_RANDOM_FACT` из `services.ui` — callback-id главной
  кнопки «Рандом-факт».
"""

import logging
from telegram import (
    Update,
    InlineKeyboardMarkup as Mk,
    InlineKeyboardButton as Btn,
)
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
)
from telegram.error import BadRequest

from services.openai_client import get_random_fact
from services.ui import CB_RANDOM_FACT

logger = logging.getLogger(__name__)
IMAGE = "images/random.jpg"


def _kb() -> Mk:
    """
        Сформировать inline-клавиатуру, прикрепляемую к каждому факту.

        Кнопки
        -------
        🧠 Ещё факт   → callback-data `random_more`
        🔚 Закончить  → callback-data `random_finish`
    """
    return Mk([
        [Btn("🧠 Ещё факт",  callback_data="random_more")],
        [Btn("🔚 Закончить", callback_data="random_finish")],
    ])


async def _send_fact(target, fact: str):
    """
        Послать *новое* сообщение-карточку с фактом.

        Parameters
        ----------
        target :
            Объект, имеющий метод `.send_photo()` (обычно экземпляр
            `telegram.Chat` или `telegram.Message`). Позволяет отправить
            изображение с подписью.
        fact : str
            Текст факта (≤ 1024 символов) уже полученный от ChatGPT.
    """
    await target.send_photo(
        IMAGE,
        caption=fact[:1024],
        reply_markup=_kb(),
        parse_mode="Markdown",
    )
    logger.info("Факт отправлен")


async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
        Точка входа: команда `/random` **или** кнопка из главного меню.

        • Если вызов пришёл от callback-кнопки, сначала отвечаем на query
          (`await .answer()`) и используем `update.effective_chat` для
          отправки нового сообщения.
        • В остальных случаях используем `update.effective_message`.
    """
    if update.callback_query:
        await update.callback_query.answer()
        target_chat = update.effective_chat
    else:
        target_chat = update.effective_message

    await _send_fact(target_chat, await get_random_fact())


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
        Универсальный обработчик двух callback-кнопок под фактом.

        * `random_more`   → вытягивает новый факт из OpenAI и, по
          возможности, **редактирует** подпись текущего сообщения
          (`edit_message_caption`).
          Если Telegram не позволяет редактировать (часто из-за
          превышения лимита 1-минуты), просто удаляем сообщение и
          присылаем новое, чтобы интерфейс оставался чистым.
        * `random_finish` → удаляет карточку с фактом и возвращает
          пользователя в главное меню (`handlers.basic.show_main_menu`).
    """
    q = update.callback_query
    await q.answer()

    if q.data == "random_more":
        fact = await get_random_fact()
        try:
            await q.edit_message_caption(fact, reply_markup=_kb(),
                                         parse_mode="Markdown")
        except BadRequest:
            await q.message.delete()
            await _send_fact(q.message, fact)
        return

    await q.message.delete()
    from handlers.basic import show_main_menu
    await show_main_menu(update, context)


def register_handlers(app):
    app.add_handler(CommandHandler("random", random_fact))
    app.add_handler(CallbackQueryHandler(random_fact,
                                         pattern=f"^{CB_RANDOM_FACT}$"))
    app.add_handler(CallbackQueryHandler(buttons,
                                         pattern="^random_(more|finish)$"))
