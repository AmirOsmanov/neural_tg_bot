import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from services.openai_client import ask_chatgpt
from services.ui import get_main_menu_keyboard

logger = logging.getLogger(__name__)

GPT_MODE = 1

async def start_gpt(update_or_query, context: ContextTypes.DEFAULT_TYPE) -> int:

    if hasattr(update_or_query, "message") and update_or_query.message:
        message = update_or_query.message
        user = update_or_query.effective_user
        chat_id = message.chat_id

        try:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=open("images/chatgpt.jpg", "rb")
            )
        except Exception as e:
            logger.error(f"Не удалось отправить chatgpt.jpg: {e}")

        await context.bot.send_message(
            chat_id=chat_id,
            text="🧠 ChatGPT активен.\n\nНапишите ваш вопрос:",
            parse_mode="HTML"
        )

    else:
        query = update_or_query.callback_query
        await query.answer()
        user = query.from_user
        chat_id = query.from_user.id

        await query.message.delete()

        try:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=open("images/chatgpt.jpg", "rb")
            )
        except Exception as e:
            logger.error(f"Не удалось отправить chatgpt.jpg: {e}")

        await context.bot.send_message(
            chat_id=chat_id,
            text="🧠 ChatGPT активен.\n\nНапишите ваш вопрос:",
            parse_mode="HTML"
        )

    logger.info(f"{user.first_name} ({user.id}) начал общение с ChatGPT")
    return GPT_MODE


async def handle_gpt_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    user_input = update.message.text.strip()
    logger.info(f"{user.first_name} ({user.id}) написал: {user_input}")

    try:
        response = await ask_chatgpt([
            {"role": "system", "content": "Ты умный и вежливый помощник. Отвечай на русском языке."},
            {"role": "user", "content": user_input}
        ])
    except Exception as e:
        logger.error(f"Ошибка при обращении к ChatGPT: {e}")
        response = "😔 К сожалению, не удалось получить ответ от ChatGPT. Попробуйте позже."

    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="gpt_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        response,
        reply_markup=reply_markup
    )

    return GPT_MODE


async def return_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(
        "🎉 <b>Добро пожаловать в ChatGPT бота!</b>\n\n"
        "Выберите одну из доступных функций:",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработчик команды /cancel в режиме ChatGPT.
    Просто уведомляет пользователя и завершает разговор.
    """
    user = update.effective_user
    logger.info(f"{user.first_name} ({user.id}) вышел из режима ChatGPT")
    await update.message.reply_text("❌ Вы вышли из режима ChatGPT.")
    return ConversationHandler.END
