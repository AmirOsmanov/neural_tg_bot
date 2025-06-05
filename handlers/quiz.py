import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    CommandHandler,
    filters,
)

from services.ui import get_main_menu_keyboard
from services.openai_client import get_quiz_question, check_quiz_answer

logger = logging.getLogger(__name__)

CHOOSE_THEME, WAIT_ANSWER = range(2)

QUIZ_THEMES = ["История", "Наука", "Кино"]

def themes_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(t, callback_data=f"theme_{t}")] for t in QUIZ_THEMES] +
        [[InlineKeyboardButton("🏠 Главное меню", callback_data="quiz_exit")]]
    )

def quiz_nav_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("❓ Следующий вопрос", callback_data="quiz_next"),
            InlineKeyboardButton("🔄 Сменить тему", callback_data="quiz_change")
        ],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="quiz_exit")]
    ])

async def start_quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info("%s запустил /quiz", user.first_name)

    if update.message:
        await update.message.delete()

    with open("images/quiz.jpg", "rb") as img:
        await context.bot.send_photo(chat_id=user.id, photo=img)

    await context.bot.send_message(
        chat_id=user.id,
        text="🧠 Выбери тему квиза:",
        reply_markup=themes_keyboard()
    )

    context.user_data["quiz_score"] = 0
    return CHOOSE_THEME

async def choose_theme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "quiz_exit":
        await query.message.delete()
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Вы вернулись в меню.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END

    if data == "quiz_change":
        await query.message.edit_text("🧠 Выбери новую тему:", reply_markup=themes_keyboard())
        return CHOOSE_THEME

    if data == "quiz_next":
        return await ask_question(query, context)

    if data.startswith("theme_"):
        context.user_data["quiz_theme"] = data.replace("theme_", "")
        await query.message.delete()
        return await ask_question(query, context)

async def ask_question(query, context):
    theme = context.user_data["quiz_theme"]
    question_text, correct = await get_quiz_question(theme)
    context.user_data["correct_answer"] = correct

    await context.bot.send_message(
        chat_id=query.from_user.id,
        text=f"🧐 <b>Вопрос по теме «{theme}»:</b>\n{question_text}",
        parse_mode="HTML"
    )
    return WAIT_ANSWER

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_answer = update.message.text
    correct_answer = context.user_data.get("correct_answer", "")
    is_right = await check_quiz_answer(user_answer, correct_answer)

    if is_right:
        context.user_data["quiz_score"] += 1

    score = context.user_data["quiz_score"]
    reply = "✅ Правильно!" if is_right else f"❌ Неправильно. Правильный ответ: {correct_answer}"

    await update.message.reply_text(
        f"{reply}\n\nТвой счёт: {score}",
        reply_markup=quiz_nav_keyboard()
    )
    return CHOOSE_THEME

async def cancel_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Квиз прерван.",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END

def build_quiz_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("quiz", start_quiz_command),
            CallbackQueryHandler(start_quiz_command, pattern="^quiz_run$"),
        ],
        states={
            CHOOSE_THEME: [CallbackQueryHandler(choose_theme)],
            WAIT_ANSWER:  [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer)],
        },
        fallbacks=[CommandHandler("cancel", cancel_quiz)],
    )
