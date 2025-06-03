import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from services.openai_client import ask_chatgpt
from services.ui import get_main_menu_keyboard

logger = logging.getLogger(__name__)

# 1) GPT_MODE задаётся как целое число (не range)
GPT_MODE = 1

async def start_gpt(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    """
    Точка входа в режим ChatGPT:
    - если пришла команда /gpt ➞ update_or_query.message
    - если пришла колбэком кнопка gpt_run ➞ update_or_query.callback_query
    """
    # 1.1) Разбор: это CallbackQuery или Message?
    if hasattr(update_or_query, "message") and update_or_query.message:
        # вызов через /gpt
        message = update_or_query.message
        user = update_or_query.effective_user
        # удаляем исходное «/gpt», чтобы не засорять чат
        await message.delete()
    else:
        # вызов через кнопку (CallbackQuery)
        query = update_or_query.callback_query
        await query.answer()
        await query.message.delete()
        user = query.from_user
        # отправляем пользователю «вводи запрос»
        message = await context.bot.send_message(
            chat_id=query.from_user.id,
            text="🧠 ChatGPT активен.\n\nНапишите свой вопрос:",
            parse_mode="HTML",
        )

    logger.info(f"{user.first_name} ({user.id}) начал общение с ChatGPT")
    # Возвращаем состояние GPT_MODE = 1
    return GPT_MODE

async def handle_gpt_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    В этом состоянии (GPT_MODE) ловим любой текст ➞ передаём в ask_chatgpt ➞ отвечаем
    и показываем кнопку «Главное меню».
    """
    user = update.effective_user
    user_input = update.message.text
    logger.info(f"{user.first_name} ({user.id}) написал в ChatGPT: {user_input}")

    try:
        response = await ask_chatgpt(user_input)
    except Exception as e:
        logger.error(f"Ошибка при обращении к OpenAI: {e}")
        response = "😔 Произошла ошибка. Попробуйте позже."

    # Кнопка «🏠 Главное меню»
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="gpt_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        response,
        reply_markup=reply_markup
    )

    # Остаёмся в том же состоянии — ждём следующего сообщения или «Главное меню»
    return GPT_MODE

async def return_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    При нажатии «🏠 Главное меню» возвращаемся в главное меню
    и завершаем Conversation (возвращаем `ConversationHandler.END`).
    """
    query = update.callback_query
    await query.answer()

    await query.message.edit_text(
        "🎉 <b>Добро пожаловать в ChatGPT бота!</b>\n\n"
        "Выберите одну из доступных функций:",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик /cancel — выходит из режима ChatGPT и завершает ConversationHandler.
    """
    user = update.effective_user
    logger.info(f"{user.first_name} ({user.id}) вышел из режима ChatGPT")
    await update.message.reply_text("❌ Вы вышли из режима ChatGPT.")
    return ConversationHandler.END
