"""Файл с хендлерами для «Рандомных фактов»."""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.ui import get_main_menu_keyboard
from services.openai_client import get_random_fact

logger = logging.getLogger(__name__)


async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /random."""
    user = update.effective_user
    logger.info(f"{user.first_name} ({user.id}) вызвал команду /random")
    await send_fact(update.message, user)


async def random_fact_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий кнопок для «Рандомного факта»."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    logger.info(f"{user.first_name} ({user.id}) нажал кнопку: {query.data}")

    if query.data in ["random_more", "random_fact"]:
        # И «первый запуск» (callback_data="random_fact"), и «ещё факт» (random_more)
        await send_fact(query, user)

    elif query.data == "random_finish":
        # Вернуться в главное меню
        reply_markup = get_main_menu_keyboard()
        await query.edit_message_text(
            "🎉 <b>Добро пожаловать в ChatGPT бота!</b>\n\n"
            "Выберите одну из доступных функций:",
            parse_mode="HTML",
            reply_markup=reply_markup,
        )


async def send_fact(query_or_message, user):
    """Служебная функция: генерируем факт и отправляем его."""
    try:
        # 1) Если это CallbackQuery (edit_message_text), то редактируем текущее сообщение
        if hasattr(query_or_message, "edit_message_text"):
            await query_or_message.edit_message_text("🎲 Генерирую интересный факт... ⏳")
        else:
            # 2) Иначе (Message), просто отправляем новое
            await query_or_message.reply_text("🎲 Генерирую интересный факт... ⏳")

        # 3) Получаем факт через OpenAI
        fact = await get_random_fact()

        keyboard = [
            [InlineKeyboardButton("🎲 Хочу ещё факт", callback_data="random_more")],
            [InlineKeyboardButton("🏠 Закончить", callback_data="random_finish")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # 4) Редактируем (или отправляем) текст с фактом и кнопками
        await query_or_message.edit_message_text(
            f"🧠 <b>Интересный факт:</b>\n\n{fact}",
            parse_mode="HTML",
            reply_markup=reply_markup,
        )
        logger.info(f"{user.first_name} ({user.id}) получил факт")

    except Exception as e:
        logger.error(f"Ошибка при получении факта: {e}")
        # В случае ошибки, показываем сообщение об этом и предлагаем вернуться в меню
        await query_or_message.edit_message_text(
            "😔 Произошла ошибка. Попробуйте позже.\n"
            "Используйте /start, чтобы вернуться в меню."
        )
