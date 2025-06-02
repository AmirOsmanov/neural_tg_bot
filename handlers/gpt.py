import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from services.openai_client import ask_chatgpt

logger = logging.getLogger(__name__)

GPT_MODE = range(1)


async def start_gpt(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    """Запуск диалога с ChatGPT"""
    user = update_or_query.effective_user
    logger.info(f"{user.first_name} ({user.id}) начал общение с ChatGPT")

    if hasattr(update_or_query, "message"):  # вызов через /gpt
        message = update_or_query.message
    else:  # вызов через кнопку
        await update_or_query.message.delete()
        message = await context.bot.send_message(
            chat_id=update_or_query.from_user.id,
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

    # Сохраняем сообщение с кнопкой для последующего удаления
    msg = await update.message.reply_text(
        response,
        reply_markup=reply_markup
    )
    context.user_data["last_gpt_msg_id"] = msg.message_id

    return GPT_MODE


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выход из режима ChatGPT"""
    user = update.effective_user
    logger.info(f"{user.first_name} ({user.id}) вышел из ChatGPT")
    await update.message.reply_text("❌ Вы вышли из режима ChatGPT.")
    return ConversationHandler.END


async def return_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в главное меню по кнопке"""
    from handlers.basic import get_main_menu_keyboard

    query = update.callback_query
    await query.answer()

    try:
        msg_id = context.user_data.get("last_gpt_msg_id")
        if msg_id:
            await context.bot.delete_message(chat_id=query.message.chat_id, message_id=msg_id)
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение ChatGPT: {e}")

    await context.bot.send_message(
        chat_id=query.from_user.id,
        text="🎉 <b>Добро пожаловать в ChatGPT бота!</b>\n\nВыберите одну из доступных функций:",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )

    return ConversationHandler.END
