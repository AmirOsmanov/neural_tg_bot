"""Файл с хендлерами бота (главное меню)."""

import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from services.ui import get_main_menu_keyboard

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /start — показать главное меню."""
    reply_markup = get_main_menu_keyboard()
    welcome_text = (
        "🎉 <b>Добро пожаловать в ChatGPT бота!</b>\n\n"
        "🚀 <b>Доступные функции:</b>\n"
        "• Рандомный факт — получи интересный факт\n"
        "• ChatGPT — общение с ИИ\n"
        "• Диалог с личностью — говори с известными людьми (в разработке)\n"
        "• Квиз — проверь свои знания (в разработке)\n"
        "• Подготовка меню — генерация недельной подборки (в разработке)\n\n"
        "Выберите функцию из меню ниже:"
    )
    await update.message.reply_text(welcome_text, parse_mode="HTML", reply_markup=reply_markup)


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий кнопок «в разработке» из главного меню."""
    query = update.callback_query
    await query.answer()

    # 1) Если нажали «Рандомный факт» — уходим в random_fact_callback, а здесь просто return
    if query.data == "random_fact":
        return

    # 2) Если нажали «ChatGPT» — ConversationHandler сам перехватит этот callback (мы не обрабатываем здесь)
    if query.data == "gpt_run":
        return

    # 3) Если ‟в разработке” (talk, quiz, cook) — показываем заглушку и возвращаем меню спустя 2 сек
    if query.data in ["talk_coming_soon", "quiz_coming_soon", "cook_coming_soon"]:
        await query.edit_message_text(
            "🚧 <b>Функция в разработке!</b>\n\n"
            "Эта функция будет добавлена на следующих этапах.\n"
            "Пока что попробуйте 'Рандомный факт'!",
            parse_mode="HTML",
        )
        await asyncio.sleep(2)
        await start_menu_again(query)


async def start_menu_again(query):
    """Возвращает главное меню (заменяем текущее сообщение)."""
    reply_markup = get_main_menu_keyboard()
    await query.edit_message_text(
        "🎉 <b>Добро пожаловать в ChatGPT бота!</b>\n\n"
        "Выберите одну из доступных функций:",
        parse_mode="HTML",
        reply_markup=reply_markup,
    )
