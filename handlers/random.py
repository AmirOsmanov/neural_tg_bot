"""Файл с хендлерами для «Рандомного факта»."""

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

    # 1) И «random_fact» (первый запуск), и «random_more» — просто пересылаем факт
    if query.data in ["random_fact", "random_more"]:
        await send_fact(query, user)

    # 2) Если нажали «random_finish» — вернуться в главное меню
    elif query.data == "random_finish":
        reply_markup = get_main_menu_keyboard()
        await query.edit_message_text(
            "🎉 <b>Добро пожаловать в ChatGPT бота!</b>\n\n"
            "Выберите одну из доступных функций:",
            parse_mode="HTML",
            reply_markup=reply_markup,
        )


async def send_fact(query_or_message, user):
    """Общая служебная функция: запрос к OpenAI + отправка."""
    try:
        # 1) Если query_or_message — CallbackQuery (у него есть метод edit_message_text)
        if hasattr(query_or_message, "edit_message_text"):
            await query_or_message.edit_message_text("🎲 Генерирую интересный факт... ⏳")
        else:
            # 2) Иначе, это текстовое сообщение (CommandHandler "/random")
            await query_or_message.reply_text("🎲 Генерирую интересный факт... ⏳")

        # 3) Получаем факт от OpenAI
        fact = await get_random_fact()

        # 4) Клавиатура «еще факт» / «закончить»
        keyboard = [
            [InlineKeyboardButton("🎲 Хочу ещё факт", callback_data="random_more")],
            [InlineKeyboardButton("🏠 Закончить", callback_data="random_finish")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # 5) Редактируем (или отправляем) текст с фактом
        await query_or_message.edit_message_text(
            f"🧠 <b>Интересный факт:</b>\n\n{fact}",
            parse_mode="HTML",
            reply_markup=reply_markup,
        )
        logger.info(f"{user.first_name} ({user.id}) получил факт")

    except Exception as e:
        logger.error(f"Ошибка при получении факта: {e}")
        await query_or_message.edit_message_text(
            "😔 Произошла ошибка. Попробуйте позже.\n"
            "Используйте /start, чтобы вернуться в меню."
        )
