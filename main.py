import logging
from pathlib import Path
from os import getenv

from dotenv import load_dotenv
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
)
from handlers import basic, random, gpt, talk, quiz, cook, translator
from services.ui import CB_MAIN_MENU

# токен и логирование
load_dotenv()
TOKEN = getenv("TG_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("TG_BOT_TOKEN отсутствует в .env")

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# запуск бота
def build_app() -> Application:
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", basic.show_main_menu))

    random.register_handlers(app)
    cook.register_handlers(app)
    app.add_handler(gpt.build_gpt_handler())
    app.add_handler(translator.build_translator_handler())
    app.add_handler(talk.build_talk_handler())
    app.add_handler(quiz.build_quiz_handler())

    app.add_handler(
        CallbackQueryHandler(basic.show_main_menu, pattern=f"^{CB_MAIN_MENU}$")
    )

    return app


if __name__ == "__main__":
    logger.info("Бот запускается…")
    build_app().run_polling(allowed_updates=["message", "callback_query"])
