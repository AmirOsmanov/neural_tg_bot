import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from services.openai_client import ask_chatgpt
from handlers.basic import get_main_menu_keyboard

logger = logging.getLogger(__name__)

GPT_MODE = range(1)

async def start_gpt(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    """Запуск диалога с ChatGPT"""
    user = update_or_query.effective_user
    logger.info(f"{user.first_name} ({user.id}) начал общение с ChatGPT")

    if hasattr(update_or_query, "message"):  # вызов через /gpt
        message = update_or_query.message
        await message.reply_text(
            "🧠 ChatGPT активен.\n\nНапиши свой вопрос или сообщение:",
            parse_mode='HTML'
        )
    else:  # вызов через кнопку
        await update_or_query.message.delete()
        await context.bot.send_message(
            chat_id=user.id,
            text="🧠 ChatGPT активен.\n\nНапиши свой вопрос или сообщение:",
            parse_mode='HTML'
        )

    return GPT_MODE

async def handle_gpt_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений пользователя в режиме ChatGPT"""
    user = update.effective_user
    user_input = update.message.text
    logger.info(f"{user.first_name} ({user.id}) написал: {user_input}")

    response = await ask_chatgpt(user_input)

    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="gpt_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        response,
        reply_markup=reply_markup
    )

    return GPT_MODE

async def return_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в главное меню из режима ChatGPT"""
    query = update.callback_query
    await query.answer()

    logger.info(f"{query.from_user.first_name} ({query.from_user.id}) вернулся в главное меню из ChatGPT")

    await query.edit_message_text(
        text="🎉 <b>Добро пожаловать в ChatGPT бота!</b>\n\nВыберите одну из доступных функций:",
        parse_mode='HTML',
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выход из режима ChatGPT по команде /cancel"""
    user = update.effective_user
    logger.info(f"{user.first_name} ({user.id}) вышел из режима ChatGPT")

    await update.message.reply_text("❌ Вы вышли из режима ChatGPT.")
    return ConversationHandler.END
