import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.ui import get_main_menu_keyboard
from services.openai_client import get_random_fact

logger = logging.getLogger(__name__)


async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    logger.info(f"{user.first_name} ({user.id}) вызвал команду /random")

    try:
        photo_message = await context.bot.send_photo(
            chat_id=chat_id,
            photo=open("images/random.jpg", "rb"),
            caption="🎲 Генерирую интересный факт... ⏳"
        )
    except Exception as e:
        logger.error(f"Не удалось отправить random.jpg: {e}")
        # Если фото не отправилось, можно уйти в текстовый режим:
        placeholder = await context.bot.send_message(
            chat_id=chat_id,
            text="🎲 Генерирую интересный факт... ⏳"
        )
        photo_message = None  # помечаем, что не было фото

    try:
        fact = await get_random_fact()
    except Exception as e:
        logger.error(f"Ошибка при получении факта от OpenAI: {e}")
        fact = "😔 К сожалению, не удалось получить факт в данный момент."

    keyboard = [
        [InlineKeyboardButton("🎲 Хочу ещё факт", callback_data="random_more")],
        [InlineKeyboardButton("🏠 Закончить", callback_data="random_finish")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if photo_message:
        await photo_message.edit_caption(
            caption=f"🧠 <b>Интересный факт:</b>\n\n{fact}",
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    else:
        await placeholder.edit_text(
            f"🧠 <b>Интересный факт:</b>\n\n{fact}",
            parse_mode="HTML",
            reply_markup=reply_markup
        )

    logger.info(f"{user.first_name} ({user.id}) получил факт")


async def random_fact_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = query.data
    logger.info(f"{user.first_name} ({user.id}) нажал кнопку: {data}")

    if data in ["random_more", "random_fact"]:
        try:
            await query.message.delete()
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение: {e}")

        chat_id = query.from_user.id

        try:
            photo_message = await context.bot.send_photo(
                chat_id=chat_id,
                photo=open("images/random.jpg", "rb"),
                caption="🎲 Генерирую интересный факт... ⏳"
            )
        except Exception as e:
            logger.error(f"Не удалось отправить random.jpg: {e}")
            placeholder = await context.bot.send_message(
                chat_id=chat_id,
                text="🎲 Генерирую интересный факт... ⏳"
            )
            photo_message = None

        try:
            fact = await get_random_fact()
        except Exception as e:
            logger.error(f"Ошибка при получении факта от OpenAI: {e}")
            fact = "😔 К сожалению, не удалось получить факт в данный момент."

        keyboard = [
            [InlineKeyboardButton("🎲 Хочу ещё факт", callback_data="random_more")],
            [InlineKeyboardButton("🏠 Закончить", callback_data="random_finish")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if photo_message:
            await photo_message.edit_caption(
                caption=f"🧠 <b>Интересный факт:</b>\n\n{fact}",
                parse_mode="HTML",
                reply_markup=reply_markup
            )
        else:
            await placeholder.edit_text(
                f"🧠 <b>Интересный факт:</b>\n\n{fact}",
                parse_mode="HTML",
                reply_markup=reply_markup
            )

        logger.info(f"{user.first_name} ({user.id}) получил факт")

    elif data == "random_finish":
        try:
            await query.message.delete()
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение: {e}")

        reply_markup = get_main_menu_keyboard()
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text=(
                "🎉 <b>Добро пожаловать в ChatGPT бота!</b>\n\n"
                "Выберите одну из доступных функций:"
            ),
            parse_mode='HTML',
            reply_markup=reply_markup
        )
