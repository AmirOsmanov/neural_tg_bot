"""
handlers.cook
=============

Модуль «👨‍🍳 Подготовка меню».

Позволяет пользователю получить сгенерированный ChatGPT-ом **семидневный
рацион** на заданную суточную калорийность. Интерфейс построен на
inline-кнопках:

1. `/cook` или кнопка «Подготовка меню» в главном меню ➜ выбор лимита ккал.
2. После генерации меню появляется клавиатура:
   «🔄 Выбрать другой лимит» или «🔙 Главное меню».

Все пользовательские состояния и вспомогательные данные хранятся
исключительно внутри Telegram CallbackQuery; `context.user_data`
не используется.
"""

import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
)
from services import ui
from services.openai_client import get_week_menu

logger = logging.getLogger(__name__)
IMAGE = "images/cook.jpg"
READY = "✅ Меню готово! Смотрите сообщение ниже 👇"


async def _show_limits(update: Update, *, edit: bool = False):
    """
        Отобразить клавиатуру выбора калорийности.

        Parameters
        ----------
        update : telegram.Update
            Объект события (используется либо `effective_message`, либо
            `callback_query` для редактирования).
        edit : bool, default=False
            * `False` — отправить **новое** сообщение-картинку с клавиатурой.
            * `True`  — **заменить** подпись/клавиатуру у существующего
              сообщения (используется при «🔄 Выбрать другой лимит»).

        Side Effects
        ------------
        • Отправляет или редактирует сообщение с картинкой `IMAGE`.
        • Не возвращает значения — чистый I/O.
    """
    caption = "📋 Подбор меню на неделю\n\nВыберите дневной лимит ккал:"
    kb = ui.get_cook_kcal_keyboard()

    if edit:
        await update.callback_query.edit_message_caption(
            caption, reply_markup=kb, parse_mode="Markdown"
        )
    else:
        await update.effective_message.reply_photo(
            IMAGE, caption=caption, reply_markup=kb, parse_mode="Markdown"
        )


async def start_cook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
        Точка входа команды `/cook` или callback-кнопки «Подготовка меню».

        Фактически просто вызывает `_show_limits`, чтобы показать выбор
        калорийности. Состояние диалога не используется, поэтому функция
        возвращает `None`.

        Parameters
        ----------
        update : telegram.Update
            Событие Telegram (команда или callback).
        context : telegram.ext.ContextTypes.DEFAULT_TYPE
            Контекст PTB. Здесь не используется, но обязателен по сигнатуре.
    """
    await _show_limits(update)


async def kcal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
        Обработчик выбора конкретного лимита калорий.

        • Извлекает число из callback-data (`cook_kcal:<N>`).
        • Показывает «⏳ Готовлю меню…».
        • Запрашивает меню у OpenAI (`services.openai_client.get_week_menu`).
        • Отправляет результат отдельным сообщением.
        • Обновляет исходное сообщение на «✅ Меню готово!».

        Parameters
        ----------
        update : telegram.Update
            Callback с данными вида `cook_kcal:2000`.
        context : telegram.ext.ContextTypes.DEFAULT_TYPE
            Контекст PTB (не используется).
    """
    q = update.callback_query
    await q.answer()
    kcal = int(q.data.split(":")[1])

    await q.edit_message_caption(
        f"⏳ Готовлю меню на {kcal} ккал/день…",
        parse_mode="Markdown",
    )

    try:
        menu = await get_week_menu(kcal)
    except Exception as exc:                        # noqa: BLE001
        logger.exception("Menu error: %s", exc)
        menu = "⚠️ Не удалось получить меню."

    await q.edit_message_caption(
        READY, reply_markup=ui.get_cook_result_keyboard(),
        parse_mode="Markdown",
    )
    await q.message.reply_text(menu, parse_mode="Markdown")


async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
        Callback-обработчик «🔄 Выбрать другой лимит».

        Просто вызывает `_show_limits(edit=True)`, чтобы заменить подпись и
        клавиатуру в том же сообщении, не создавая нового.

        Parameters
        ----------
        update : telegram.Update
            Callback с data = `cook_back`.
        context : telegram.ext.ContextTypes.DEFAULT_TYPE
            PTB-контекст (не используется).
    """
    await update.callback_query.answer()
    await _show_limits(update, edit=True)


def register_handlers(app):
    app.add_handler(CommandHandler("cook", start_cook))

    app.add_handler(CallbackQueryHandler(start_cook,
                                         pattern=f"^{ui.CB_COOK}$"))

    app.add_handler(CallbackQueryHandler(kcal,
                                         pattern=rf"^{ui.CB_COOK_PREFIX}:\d+$"))

    app.add_handler(CallbackQueryHandler(back,
                                         pattern=f"^{ui.CB_COOK_BACK}$"))
