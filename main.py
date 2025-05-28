import os
from dotenv import load_dotenv
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from handlers import basic, random

load_dotenv()

TG_BOT_TOKEN = os.getenv('BOT_TOKEN')
CHATGPT_TOKEN = os.getenv('OPENAI_API_KEY')

if not all([TG_BOT_TOKEN, CHATGPT_TOKEN]):
    raise ValueError("Didn't find tokens in .env")

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler("logs/bot.log", encoding="utf-8"),
        logging.StreamHandler()
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

        logger.info("Бот запущен успешно!")
        application.run_polling()

    except Exception as e:
        logger.error('Ошибка при запуске', e)

if __name__ == "__main__":
    main()