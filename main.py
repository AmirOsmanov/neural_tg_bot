# main.py

import logging
import os
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters
)
from handlers.basic import start, menu_callback
from handlers.random import random_fact, random_fact_callback
from handlers.gpt import start_gpt, handle_gpt_message, cancel, return_to_menu, GPT_MODE
from handlers.talk import (
    start_talk,
    choose_persona,
    handle_talk_message,
    return_to_menu_talk,
    cancel_talk,
    TALK_PERSONA,
    TALK_MODE
)
from config import TG_BOT_TOKEN

# ─── Настройка логирования ─────────────────────────────────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    application = Application.builder().token(TG_BOT_TOKEN).build()

    # ─── Команда /start ─────────────────────────────────────────────────────────────────────────────────────
    application.add_handler(CommandHandler("start", start))

    # ─── Команда /random и кнопки «random_more», «random_finish» ─────────────────────────────────────────────
    application.add_handler(CommandHandler("random", random_fact))
    application.add_handler(
        CallbackQueryHandler(
            random_fact_callback,
            pattern="^(random_fact|random_more|random_finish)$"
        )
    )

    # ─── Обработка кнопок главного меню (кроме gpt_run) ───────────────────────────────────────────────────
    application.add_handler(
        CallbackQueryHandler(
            menu_callback,
            pattern="^(random_fact|talk_coming_soon|quiz_coming_soon|cook_coming_soon)$"
        )
    )

    # ─── ConversationHandler для ChatGPT ────────────────────────────────────────────────────────────────────
    gpt_handler = ConversationHandler(
        entry_points=[
            CommandHandler("gpt", start_gpt),
            CallbackQueryHandler(start_gpt, pattern="^gpt_run$")
        ],
        states={
            GPT_MODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_gpt_message),
                CallbackQueryHandler(return_to_menu, pattern="^gpt_to_menu$")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )
    application.add_handler(gpt_handler)

    # ─── ConversationHandler для /talk ──────────────────────────────────────────────────────────────────────
    talk_handler = ConversationHandler(
        entry_points=[
            CommandHandler("talk", start_talk),
            CallbackQueryHandler(start_talk, pattern="^talk_run$")
        ],
        states={
            # После того как пользователь нажал /talk, он выбирает личность
            TALK_PERSONA: [
                CallbackQueryHandler(choose_persona, pattern="^persona_")
            ],
            # После выбора личности пользователь пишет текстовые сообщения
            TALK_MODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_talk_message),
                CallbackQueryHandler(return_to_menu_talk, pattern="^end_talk$")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel_talk)],
        per_message=False
    )
    application.add_handler(talk_handler)

    # ─── Запуск бота ────────────────────────────────────────────────────────────────────────────────────────
    logger.info("Бот запущен успешно!")
    application.run_polling()


if __name__ == "__main__":
    main()
