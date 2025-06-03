import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.openai_client import get_random_fact
from services.ui import get_main_menu_keyboard

logger = logging.getLogger(__name__)


async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /random"""
    user = update.effective_user
    logger.info(f"{user.first_name} ({user.id}) вызвал команду /random")
    # Передаём в send_fact: Message, context и пользователя
    await send_fact(update.message, context, user)


async def random_fact_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий кнопок для рандомных фактов"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    logger.info(f"{user.first_name} ({user.id}) нажал кнопку: {query.data}")

    # Сначала удаляем предыдущую фотографию, если она сохранилась
    last_photo_id = context.user_data.get("last_fact_photo_id")
    if last_photo_id:
        try:
            await context.bot.delete_message(chat_id=user.id, message_id=last_photo_id)
        except Exception:
            pass
        # Очистим хранилище
        context.user_data.pop("last_fact_photo_id", None)

    if query.data in ["random_more", "random_fact"]:
        # Передаём в send_fact: CallbackQuery, context и пользователя
        await send_fact(query, context, user)

    elif query.data == "random_finish":
        reply_markup = get_main_menu_keyboard()
        await query.edit_message_text(
            "🎉 <b>Добро пожаловать в ChatGPT бота!</b>\n\n"
            "Выберите одну из доступных функций:",
            parse_mode='HTML',
            reply_markup=reply_markup
        )


async def send_fact(query_or_message, context: ContextTypes.DEFAULT_TYPE, user):
    """
    Общая функция для генерации и отправки факта с картинкой сверху.
    query_or_message может быть либо Message, либо CallbackQuery.
    """
    try:
        # 1) Если у объекта есть метод `reply_text`, считаем, что это Message
        if hasattr(query_or_message, "reply_text"):
            # 1.1) Отправляем картинку random.jpg и сохраняем её message_id
            with open("images/random.jpg", "rb") as img:
                photo_msg = await query_or_message.reply_photo(photo=img)
            context.user_data["last_fact_photo_id"] = photo_msg.message_id

            # 1.2) Отправляем текст «Генерирую факт...»
            loading_msg = await query_or_message.reply_text("🎲 Генерирую интересный факт... ⏳")

        else:
            # 2) Иначе считаем, что это CallbackQuery
            query = query_or_message  # явно называем
            # 2.1) Удаляем предыдущее текстовое сообщение (оно уже не актуально)
            await query.message.delete()

            # 2.2) Отправляем картинку и сохраняем её message_id
            with open("images/random.jpg", "rb") as img:
                photo_msg = await context.bot.send_photo(chat_id=user.id, photo=img)
            context.user_data["last_fact_photo_id"] = photo_msg.message_id

            # 2.3) Отправляем текст «Генерирую факт...»
            loading_msg = await context.bot.send_message(
                chat_id=user.id,
                text="🎲 Генерирую интересный факт... ⏳"
            )

        # 3) Ждём ответ от OpenAI
        fact = await get_random_fact()

        # 4) Формируем keyboard с кнопками «Хочу ещё факт» и «Закончить»
        keyboard = [
            [InlineKeyboardButton("🎲 Хочу ещё факт", callback_data="random_more")],
            [InlineKeyboardButton("🏠 Закончить", callback_data="random_finish")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # 5) Редактируем сообщение loading_msg текстом факта и прикрепляем кнопки
        await loading_msg.edit_text(
            f"🧠 <b>Интересный факт:</b>\n\n{fact}",
            parse_mode='HTML',
            reply_markup=reply_markup
        )

        logger.info(f"{user.first_name} ({user.id}) получил факт")

    except Exception as e:
        logger.error(f"Ошибка при получении факта: {e}")
        # Если упало на любом шаге — сообщаем об ошибке
        if hasattr(query_or_message, "edit_message_text"):
            # Это CallbackQuery (редактируем текст оригинала)
            await query_or_message.edit_message_text(
                "😔 Произошла ошибка. Попробуйте позже.\n"
                "Используйте /start чтобы вернуться в меню."
            )
        else:
            # Это Message (просто отправляем новый текст)
            await query_or_message.reply_text(
                "😔 Произошла ошибка. Попробуйте позже.\n"
                "Используйте /start чтобы вернуться в меню."
            )
