from __future__ import annotations
import logging
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from services import ui
from services.openai_client import ask_chatgpt
from handlers import basic

logger = logging.getLogger(__name__)

CHOOSE_PERSONA, CHAT = range(2)

def _chat_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔚 Закончить диалог", callback_data=ui.CB_END_TALK),
        InlineKeyboardButton("🔙 Главное меню",     callback_data=ui.CB_MAIN_MENU),
    ]])


async def _end_and_menu(update: Update,
                        context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.message.delete()
        except Exception:        # noqa: BLE001
            pass
    await basic.show_main_menu(update, context)
    return ConversationHandler.END


async def start_talk(update: Update,
                     context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.delete()

    await update.effective_message.reply_text(
        "Выберите собеседника:",
        reply_markup=ui.get_persona_keyboard(),
    )
    return CHOOSE_PERSONA


async def choose_persona(update: Update,
                         context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    persona_map = {
        ui.CB_P_EINSTEIN:    "Альберт Эйнштейн",
        ui.CB_P_OPPENHEIMER: "Роберт Оппенгеймер",
        ui.CB_P_KURCHATOV:   "Игорь Курчатов",
    }
    persona = persona_map.get(query.data)
    if not persona:
        # Нажали «Главное меню»
        return await _end_and_menu(update, context)

    context.user_data["persona"] = persona
    await query.message.edit_text(
        f"Вы начали беседу с {persona}. Задайте вопрос!",
        reply_markup=_chat_kb(),
    )
    return CHAT

async def talk_msg(update: Update,
                   context: ContextTypes.DEFAULT_TYPE) -> int:
    persona = context.user_data.get("persona", "Собеседник")
    prompt = (
        f"Ты выступаешь в роли {persona}. "
        "Отвечай дружелюбно и по-русски. "
        f"Вопрос пользователя: «{update.message.text}»"
    )

    try:
        answer = await ask_chatgpt(prompt)
    except Exception as exc:
        logger.exception("Persona error: %s", exc)
        answer = "⚠️ Не удалось получить ответ. Попробуйте ещё раз."

    await update.message.reply_text(answer, reply_markup=_chat_kb())
    return CHAT


def build_talk_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("talk", start_talk),
            CallbackQueryHandler(start_talk, pattern=f"^{ui.CB_PERSONA_TALK}$"),
        ],
        states={
            CHOOSE_PERSONA: [
                CallbackQueryHandler(choose_persona, pattern=f"^{ui.CB_P_EINSTEIN}$"),
                CallbackQueryHandler(choose_persona, pattern=f"^{ui.CB_P_OPPENHEIMER}$"),
                CallbackQueryHandler(choose_persona, pattern=f"^{ui.CB_P_KURCHATOV}$"),
                CallbackQueryHandler(_end_and_menu, pattern=f"^{ui.CB_MAIN_MENU}$"),
            ],
            CHAT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, talk_msg),
                CallbackQueryHandler(_end_and_menu, pattern=f"^{ui.CB_END_TALK}$"),
                CallbackQueryHandler(_end_and_menu, pattern=f"^{ui.CB_MAIN_MENU}$"),
            ],
        },
        fallbacks=[CallbackQueryHandler(
            _end_and_menu,
            pattern=f"^({ui.CB_END_TALK}|{ui.CB_MAIN_MENU})$"
        )],
        per_chat=True,
        per_user=False,
    )
