import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
)
from services import ui
from services.openai_client import get_week_menu

logger = logging.getLogger(__name__)
IMAGE = "images/cook.jpg"
READY = "✅ Меню готово! Смотрите сообщение ниже 👇"


async def _show_limits(update: Update, *, edit: bool = False):
    caption = "📋 Подбор меню на неделю\n\nВыберите дневной лимит ккал:"
    kb = ui.get_cook_kcal_keyboard()

    if edit:
        await update.callback_query.edit_message_caption(
            caption, reply_markup=kb, parse_mode="Markdown"
        )
    else:
        await update.effective_message.reply_photo(
            IMAGE, caption=caption, reply_markup=kb, parse_mode="Markdown"
        )


async def start_cook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _show_limits(update)


async def kcal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    kcal = int(q.data.split(":")[1])

    await q.edit_message_caption(
        f"⏳ Готовлю меню на {kcal} ккал/день…",
        parse_mode="Markdown",
    )

    try:
        menu = await get_week_menu(kcal)
    except Exception as exc:                        # noqa: BLE001
        logger.exception("Menu error: %s", exc)
        menu = "⚠️ Не удалось получить меню."

    await q.edit_message_caption(
        READY, reply_markup=ui.get_cook_result_keyboard(),
        parse_mode="Markdown",
    )
    await q.message.reply_text(menu, parse_mode="Markdown")


async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await _show_limits(update, edit=True)


def register_handlers(app):
    app.add_handler(CommandHandler("cook", start_cook))

    app.add_handler(CallbackQueryHandler(start_cook,
                                         pattern=f"^{ui.CB_COOK}$"))

    app.add_handler(CallbackQueryHandler(kcal,
                                         pattern=rf"^{ui.CB_COOK_PREFIX}:\d+$"))

    app.add_handler(CallbackQueryHandler(back,
                                         pattern=f"^{ui.CB_COOK_BACK}$"))
