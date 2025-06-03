import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from services.openai_client import ask_chatgpt
from services.ui import get_main_menu_keyboard

logger = logging.getLogger(__name__)

# Единственное состояние «ChatGPT-режима» — просто число 0
GPT_MODE = 0


async def start_gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Запуск диалога с ChatGPT: сначала показываем изображение, потом приглашаем
    пользователя задать вопрос.
    """
    img_path = os.path.join("images", "chatgpt.jpg")

    # Если пришёл CallbackQuery (нажатие на кнопку «ChatGPT»)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.delete()

        # 1) Отправляем картинку
        with open(img_path, "rb") as photo:
            await context.bot.send_photo(chat_id=query.from_user.id, photo=photo)

        # 2) Отправляем приглашение к вводу
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="🧠 ChatGPT активен.\n\nНапиши свой вопрос или сообщение:",
            parse_mode="HTML"
        )

        user = query.from_user

    # Если пришёл обычный /gpt (Update.message)
    elif update.message:
        message = update.message
        user = update.effective_user

        # 1) Отправляем картинку
        with open(img_path, "rb") as photo:
            await message.reply_photo(photo=photo)

        # 2) Приглашение к вводу
        await message.reply_text(
            "🧠 ChatGPT активен.\n\nНапиши свой вопрос или сообщение:",
            parse_mode="HTML"
        )

    else:
        # На всякий случай, если вдруг ни callback_query, ни message нет
        return ConversationHandler.END

    logger.info(f"{user.first_name} ({user.id}) начал общение с ChatGPT")
    return GPT_MODE  # возвращаем 0, и это совпадает с ключом в states


async def handle_gpt_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка сообщения пользователя в режиме ChatGPT: шлём ask_chatgpt и
    возвращаем ответ с кнопкой «Главное меню».
    """
    user = update.effective_user
    user_input = update.message.text
    logger.info(f"{user.first_name} ({user.id}) написал в ChatGPT: {user_input}")

    try:
        response = await ask_chatgpt(user_input)
    except Exception as e:
        logger.error(f"Ошибка при обращении к ChatGPT: {e}")
        response = "😔 Произошла ошибка. Попробуйте позже."

    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="gpt_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        response,
        reply_markup=reply_markup
    )
    return GPT_MODE  # снова возвращаем 0


async def return_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки «🏠 Главное меню» внутри ChatGPT."""
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(
        "🎉 <b>Добро пожаловать в ChatGPT бота!</b>\n\nВыберите одну из доступных функций:",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /cancel во время ChatGPT-режима."""
    user = update.effective_user
    logger.info(f"{user.first_name} ({user.id}) вышел из ChatGPT")
    await update.message.reply_text("❌ Вы вышли из режима ChatGPT.")
    return ConversationHandler.END
