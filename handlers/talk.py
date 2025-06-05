import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from services.openai_client import ask_chatgpt
from services.ui import get_persona_keyboard, get_end_talk_keyboard, get_main_menu_keyboard

logger = logging.getLogger(__name__)

TALK_PERSONA, TALK_MODE = range(2)

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
    user = update.effective_user
    logger.info(f"{user.first_name} ({user.id}) вызвал команду /talk")

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.delete()

    chat_id = update.effective_chat.id

    photo_path = "images/talk.jpg"
    try:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=open(photo_path, "rb")
        )
    except Exception as e:
        logger.error(f"Не удалось отправить talk.jpg: {e}")

    text = "👥 С кем хотите поговорить? Выберите из списка:"
    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="HTML",
        reply_markup=get_persona_keyboard()
    )

    return TALK_PERSONA


async def choose_persona(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    persona_key = query.data  # например, "persona_einstein"
    user = query.from_user

    context.user_data["persona_prompt"] = PERSONA_PROMPTS.get(persona_key)
    logger.info(f"{user.first_name} ({user.id}) выбрал личность: {persona_key}")

    await query.message.delete()

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
