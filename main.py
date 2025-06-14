"""
main.py — точка входа Telegram-бота «neural_tg_bot».

Функции:
    build_app() -> telegram.ext.Application:
        Создаёт и настраивает объект Application:
        • читает токен из переменных окружения;
        • настраивает логирование;
        • регистрирует все модульные Conversation/Command-handlers;
        • возвращает готовый к запуску экземпляр Application.

Сценарии запуска:
    • При импорте — код только объявляет функции/константы.
    • При вызове как «python main.py» выполняется блок
      `if __name__ == "__main__":`, который логирует старт и
      запускает polling-цикл через Application.run_polling().
"""

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


def build_app() -> Application:
    """Собирает и возвращает готовый объект `Application`.

        Шаги:
            1. Создаёт экземпляр `Application` с токеном из .env.
            2. Регистрирует:
               – /start-команду (`basic.show_main_menu`);
               – модульные обработчики «random», «cook»;
               – Conversation-обработчики GPT, Talk, Quiz, Translator;
               – CallbackQuery-обработчик «Главное меню».
            3. Отдаёт настроенный объект без запуска polling-цикла.
    """
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
