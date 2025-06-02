import os
import logging
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from config import TG_BOT_TOKEN
from handlers import basic, random, gpt

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/bot.log", encoding="utf-8"),
        logging.StreamHandler()  # также выводим в консоль
    ]
)
logger = logging.getLogger(__name__)


def main():
    try:
        application = Application.builder().token(TG_BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", basic.start))

        application.add_handler(CommandHandler("random", random.random_fact))
        application.add_handler(CallbackQueryHandler(random.random_fact_callback, pattern="^random_"))

        application.add_handler(CallbackQueryHandler(basic.menu_callback))

        conv_gpt = ConversationHandler(
            entry_points=[
                CommandHandler("gpt", gpt.start_gpt),
                CallbackQueryHandler(gpt.start_gpt, pattern="^gpt_run$")
            ],
            states={
                gpt.GPT_MODE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, gpt.handle_gpt_message),
                    CallbackQueryHandler(gpt.return_to_menu, pattern="^gpt_to_menu$")
                ],
            },
            fallbacks=[CommandHandler("cancel", gpt.cancel)],
        )
        application.add_handler(conv_gpt)

        logger.info("Бот запущен успешно!")
        application.run_polling()

    except Exception as e:
        logger.error('Ошибка при запуске', e)


if __name__ == "__main__":
    main()
