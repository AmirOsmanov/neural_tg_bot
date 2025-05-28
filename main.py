import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from config import TG_BOT_TOKEN
from handlers import basic, random

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    try:
        application = Application.builder().token(TG_BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", basic.start))

        application.add_handler(CommandHandler("random", random.random_fact))
        application.add_handler(CallbackQueryHandler(random.random_fact_callback, pattern="^random_"))

        application.add_handler(CallbackQueryHandler(basic.menu_callback))

        logger.info("Бот запущен успешно!")
        application.run_polling()

    except Exception as e:
        logger.error('Ошибка при запуске', e)


if __name__ == "__main__":
    main()

[InlineKeyboardButton("👨‍🍳 Подготовка меню (скоро)", callback_data="cook_coming_soon")]