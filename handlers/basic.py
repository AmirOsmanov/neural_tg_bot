import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import asyncio
from services.ui import get_main_menu_keyboard
from handlers.quiz import start_quiz_command

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = get_main_menu_keyboard()
    welcome_text = (
        "🎉 <b>Добро пожаловать в ChatGPT бота!</b>\n\n"
        "🚀 <b>Доступные функции:</b>\n"
        "• Рандомный факт — получи интересный факт\n"
        "• ChatGPT — общение с ИИ\n"
        "• Диалог с личностью — говори с известными людьми\n"
        "• Квиз — проверь свои знания\n"
        "• Подготовка меню — генерация недельной подборки (в разработке)\n\n"
        "Выберите функцию из меню ниже:"
    )
    await update.message.reply_text(
        welcome_text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "random_fact":
        # Этот случай переходит в random.py
        return

    if query.data == "quiz_run":
        # удаляем меню и запускаем квиз
        await query.message.delete()
        return await start_quiz_command(query, context)

    if query.data in ["cook_coming_soon"]:
        await query.edit_message_text(
            "🚧 <b>Функция в разработке!</b>\n\n"
            "Эта функция будет добавлена позднее.\n"
            "Пока что попробуйте другие функции!",
            parse_mode='HTML'
        )
        await asyncio.sleep(2)
        await start_menu_again(query)


async def start_menu_again(query):
    reply_markup = get_main_menu_keyboard()
    await query.edit_message_text(
        "🎉 <b>Добро пожаловать в ChatGPT бота!</b>\n\n"
        "Выберите одну из доступных функций:",
        parse_mode='HTML',
        reply_markup=reply_markup
    )
