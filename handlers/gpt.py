"""Файл с хендлерами для режима ChatGPT."""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from services.openai_client import ask_chatgpt
from services.ui import get_main_menu_keyboard

logger = logging.getLogger(__name__)

# Состояние «находимся в режиме ChatGPT»
GPT_MODE = range(1)


async def start_gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Запуск режима ChatGPT.
    Может вызываться и через команду /gpt, и через кнопку с callback_data="gpt_run".
    """
    if update.message:
        # Вызвано командой /gpt
        user = update.effective_user
        await update.message.reply_text(
            "🧠 ChatGPT активен.\n\nНапиши свой вопрос или сообщение:",
            parse_mode="HTML",
        )

    elif update.callback_query:
        # Вызвано нажатием кнопки ChatGPT
        query = update.callback_query
        user = query.from_user
        await query.answer()
        await query.message.delete()

        await context.bot.send_message(
            chat_id=user.id,
            text="🧠 ChatGPT активен.\n\nНапиши свой вопрос или сообщение:",
            parse_mode="HTML",
        )

    logger.info(f"{user.first_name} ({user.id}) начал общение с ChatGPT")
    # Возвращаем конкретное состояние (GPT_MODE[0]), а не весь range
    return GPT_MODE[0]


async def handle_gpt_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка входящих текстовых сообщений пользователя в режиме ChatGPT."""
    user = update.effective_user
    user_input = update.message.text
    logger.info(f"{user.first_name} ({user.id}) написал: {user_input}")

    try:
        response = await ask_chatgpt(user_input)
    except Exception as e:
        logger.error(f"Ошибка при обращении к ChatGPT: {e}")
        response = "😔 Произошла ошибка. Попробуйте позже."

    # Кнопка для возврата в главное меню
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="gpt_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(response, reply_markup=reply_markup)
    return GPT_MODE[0]


async def return_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Нажали «Главное меню» — вернуть главное меню."""
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(
        "🎉 <b>Добро пожаловать в ChatGPT бота!</b>\n\nВыберите одну из доступных функций:",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(),
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /cancel — выход из режима ChatGPT."""
    user = update.effective_user
    logger.info(f"{user.first_name} ({user.id}) вышел из ChatGPT")
    await update.message.reply_text("❌ Вы вышли из режима ChatGPT.")
    return ConversationHandler.END
