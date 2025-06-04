# handlers/talk.py

import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from services.openai_client import ask_chatgpt
from services.ui import get_persona_keyboard, get_end_talk_keyboard, get_main_menu_keyboard

logger = logging.getLogger(__name__)

# ─── Состояния ConversationHandler ──────────────────────────────────────────────────────────────────────────
TALK_PERSONA, TALK_MODE = range(2)

# Словарь с системными промптами для каждой личности
PERSONA_PROMPTS = {
    "persona_einstein": (
        "Ты Альберт Эйнштейн — величайший физик-теоретик. "
        "Отвечай в его стиле: кратко, умно, с ноткой юмора, на русском языке."
    ),
    "persona_oppenheimer": (
        "Ты Дж. Р. Опенгеймер — американский физик, «отец атомной бомбы». "
        "Отвечай как Оппенгеймер: вдумчиво, немного философски, на русском языке."
    ),
    "persona_kurchatov": (
        "Ты Игорь Васильевич Курчатов — советский учёный-физик, руководитель ядерного проекта СССР. "
        "Отвечай как Курчатов: серьёзно, по делу, на русском языке."
    ),
}


async def start_talk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Запуск диалога с личностью:
    1) Если вызвано через /talk (Message), сразу отправляем картинку+кнопки выбора личности.
    2) Если через кнопку talk_run (CallbackQuery), удаляем меню, потом отправляем картинку+кнопки.
    """
    user = update.effective_user
    logger.info(f"{user.first_name} ({user.id}) вызвал команду /talk")

    # Если это CallbackQuery, удаляем старое меню
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.delete()

    chat_id = update.effective_chat.id

    # Отправляем файл images/talk.jpg
    photo_path = "images/talk.jpg"
    try:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=open(photo_path, "rb")
        )
    except Exception as e:
        logger.error(f"Не удалось отправить talk.jpg: {e}")

    # Предлагаем выбрать одну из личностей
    text = "👥 С кем хотите поговорить? Выберите из списка:"
    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="HTML",
        reply_markup=get_persona_keyboard()
    )

    return TALK_PERSONA


async def choose_persona(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработчик нажатия кнопок persona_*:
    Сохраняем выбранный промпт и переходим к вводу вопросов.
    """
    query = update.callback_query
    await query.answer()
    persona_key = query.data  # например, "persona_einstein"
    user = query.from_user

    # Сохраняем соответствующий системный промпт
    context.user_data["persona_prompt"] = PERSONA_PROMPTS.get(persona_key)
    logger.info(f"{user.first_name} ({user.id}) выбрал личность: {persona_key}")

    # Удаляем сообщение с картинкой и кнопками
    await query.message.delete()

    # Отправляем короткое вступительное сообщение + кнопку «Закончить»
    persona_name = persona_key.split("_")[1].capitalize()
    welcome = (
        f"🗣 Вы общаетесь с <b>{persona_name}</b>.\n"
        "Задайте ваш вопрос:"
    )
    await context.bot.send_message(
        chat_id=query.from_user.id,
        text=welcome,
        parse_mode="HTML",
        reply_markup=get_end_talk_keyboard()
    )

    return TALK_MODE


async def handle_talk_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает текст пользователя в режиме TALK_MODE:
    отправляет системный промпт + пользовательский текст в OpenAI, возвращает ответ + кнопку «Закончить».
    """
    user = update.effective_user
    user_input = update.message.text.strip()
    logger.info(f"{user.first_name} ({user.id}) написал в /talk: {user_input}")

    persona_prompt = context.user_data.get("persona_prompt")
    if not persona_prompt:
        # Если по какой-то причине промпт не сохранился
        await update.message.reply_text("⚠️ Что-то пошло не так. Попробуйте /talk еще раз.")
        return ConversationHandler.END

    try:
        response_text = await ask_chatgpt([
            {"role": "system", "content": persona_prompt},
            {"role": "user", "content": user_input}
        ])
    except Exception as e:
        logger.error(f"Ошибка при обращении к OpenAI в /talk: {e}")
        response_text = "😔 К сожалению, не удалось получить ответ. Повторите попытку."

    await update.message.reply_text(
        response_text,
        reply_markup=get_end_talk_keyboard()
    )

    return TALK_MODE


async def return_to_menu_talk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработчик кнопки «Закончить» (end_talk) в диалоге /talk.
    Удаляет текущее сообщение и возвращает пользователя в главное меню.
    """
    query = update.callback_query
    await query.answer()
    await query.message.delete()

    await context.bot.send_message(
        chat_id=query.from_user.id,
        text=(
            "🎉 <b>Добро пожаловать в ChatGPT бота!</b>\n\n"
            "Выберите одну из доступных функций:"
        ),
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END


async def cancel_talk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработчик команды /cancel во время /talk.
    Сообщаем пользователю, что диалог завершён, и возвращаем Главное меню.
    """
    user = update.effective_user
    logger.info(f"{user.first_name} ({user.id}) отменил /talk")
    await update.message.reply_text("❌ Вы вышли из диалога.")
    await update.message.reply_text(
        "🎉 <b>Добро пожаловать в ChatGPT бота!</b>\n\n"
        "Выберите одну из доступных функций:",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END
