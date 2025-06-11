from __future__ import annotations
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters,
)
from services import ui
from services.openai_client import ask_chatgpt
from handlers import basic

logger = logging.getLogger(__name__)

IMAGE = "images/translator.jpg"

CHOOSE_LANG, TRANSLATE = range(2)

LANG_MAP = {
    "lang_en": ("английский", "English"),
    "lang_es": ("испанский",  "Spanish"),
    "lang_zh": ("китайский",  "Chinese"),
}


def _lang_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(name.capitalize(), callback_data=code)]
        for code, (name, _) in LANG_MAP.items()
    ]
    rows.append([InlineKeyboardButton("🔙 Главное меню",
                                      callback_data=ui.CB_MAIN_MENU)])
    return InlineKeyboardMarkup(rows)


def _after_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🌐 Сменить язык", callback_data="translator_change"),
        InlineKeyboardButton("🔙 Главное меню", callback_data=ui.CB_MAIN_MENU),
    ]])


async def _end(update: Update,
               context: ContextTypes.DEFAULT_TYPE):
    """Закрытие перевода → главное меню."""
    await basic.show_main_menu(update, context)
    return ConversationHandler.END


async def start(update: Update,
                context: ContextTypes.DEFAULT_TYPE) -> int:
    """Экран выбора языка (с картинкой)."""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.delete()

    await update.effective_message.reply_photo(
        IMAGE,
        caption="🌐 Выберите язык, на который нужно перевести:",
        reply_markup=_lang_kb(),
    )
    return CHOOSE_LANG


async def choose_lang(update: Update,
                      context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == ui.CB_MAIN_MENU:
        return await _end(update, context)

    context.user_data["lang_code"] = query.data
    lang_ru, _ = LANG_MAP[query.data]

    await query.edit_message_caption(
        f"✏️ Отправьте текст, который нужно перевести на *{lang_ru}*.",
        parse_mode="Markdown",
        reply_markup=_after_kb(),
    )
    return TRANSLATE


async def do_translate(update: Update,
                       context: ContextTypes.DEFAULT_TYPE) -> int:
    # ► Нажали inline-кнопку
    if update.callback_query:
        cb = update.callback_query
        await cb.answer()

        if cb.data == "translator_change":
            return await start(update, context)
        return await _end(update, context)

    lang_code = context.user_data.get("lang_code")
    if not lang_code:                           # вдруг обошли логику
        return await start(update, context)

    lang_ru, lang_en = LANG_MAP[lang_code]
    prompt = (
        f"Переведи следующий текст на {lang_ru} без добавления пояснений.\n\n"
        f"Текст: «{update.message.text}»"
    )

    try:
        translation = await ask_chatgpt(prompt, temperature=0.3)
    except Exception as exc:
        logger.exception("Translator error: %s", exc)
        translation = "⚠️ Не удалось перевести, попробуйте ещё."

    await update.message.reply_text(translation, reply_markup=_after_kb())
    return TRANSLATE


def build_translator_handler() -> ConversationHandler:
    """ConversationHandler, который нужно добавить в Application."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("translator", start),
            CallbackQueryHandler(start, pattern=f"^{ui.CB_TRANSLATOR}$"),
        ],
        states={
            CHOOSE_LANG: [
                CallbackQueryHandler(choose_lang,
                                     pattern="^(lang_en|lang_es|lang_zh)$"),
                CallbackQueryHandler(_end, pattern=f"^{ui.CB_MAIN_MENU}$"),
            ],
            TRANSLATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, do_translate),
                CallbackQueryHandler(do_translate,
                                     pattern="^(translator_change|" +
                                             f"{ui.CB_MAIN_MENU})$"),
            ],
        },
        fallbacks=[CallbackQueryHandler(_end,
                                       pattern=f"^{ui.CB_MAIN_MENU}$")],
        per_chat=True,
        per_user=False,
    )
