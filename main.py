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
from handlers.gpt import start_gpt, handle_gpt_message, cancel, return_to_menu
from config import TG_BOT_TOKEN

# Настройка логирования
os.makedirs("logs", exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/bot.log", encoding="utf-8"),
        logging.StreamHandler()  # Для вывода в консоль
    ]
)

logger = logging.getLogger(__name__)

# Состояния для ChatGPT
from handlers.gpt import GPT_MODE

def main():
    application = Application.builder().token(TG_BOT_TOKEN).build()

    # Обработка команды /start
    application.add_handler(CommandHandler("start", start))

    # Обработка команды /random
    application.add_handler(CommandHandler("random", random_fact))

    # Обработка кнопок (в том числе gpt_run и random_finish)
    application.add_handler(CallbackQueryHandler(menu_callback, pattern="^gpt_run$"))
    application.add_handler(
        CallbackQueryHandler(random_fact_callback, pattern="^(random_fact|random_more|random_finish)$"))

    # ChatGPT ConversationHandler
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
    )
    application.add_handler(gpt_handler)

    # Запуск бота
    logger.info("Бот запущен успешно!")
    application.run_polling()

if __name__ == "__main__":
    main()
