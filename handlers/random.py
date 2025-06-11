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
    return Mk([
        [Btn("🧠 Ещё факт",  callback_data="random_more")],
        [Btn("🔚 Закончить", callback_data="random_finish")],
    ])


async def _send_fact(target, fact: str):
    await target.send_photo(
        IMAGE,
        caption=fact[:1024],
        reply_markup=_kb(),
        parse_mode="Markdown",
    )
    logger.info("Факт отправлен")


async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        target_chat = update.effective_chat
    else:
        target_chat = update.effective_message

    await _send_fact(target_chat, await get_random_fact())


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
