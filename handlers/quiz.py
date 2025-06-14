"""
handlers.quiz
=============

Динамический «Квиз» (викторина), в которой вопросы на лету
генерирует ChatGPT.

Алгоритм работы модуля
----------------------
1. Пользователь вызывает `/quiz` **или** нажимает кнопку «❓ Квиз»
   в главном меню.
2. Боту показывается изображение-обложка и клавиатура с выбором темы.
3. После выбора темы бот запрашивает у ChatGPT один вопрос
   (`services.openai_client.get_quiz_question`) и предлагает три варианта ответа.
4. Пользователь выбирает вариант:
   • бот сообщает, правильный ли ответ;
   • предлагает «➕ Ещё вопрос» (та же тема) или «🔙 Главное меню».
5. При необходимости пользователь может вернуться в меню и начать сначала.

Внутри реализовано два состояния ConversationHandler:

* **TOPIC**  – выбор темы;
* **ASK**    – показ вопроса и ожидание ответа.
"""

from __future__ import annotations
import logging
from telegram import (
    Update, InlineKeyboardMarkup as Mk, InlineKeyboardButton as Btn,
)
from telegram.ext import (
    ContextTypes, ConversationHandler,
    CommandHandler, CallbackQueryHandler,
)
from services.ui import CB_QUIZ_RUN
from services.openai_client import get_quiz_question

logger = logging.getLogger(__name__)
IMAGE = "images/quiz.jpg"

TOPIC, ASK = range(2)

TOPICS = {
    "hist": "История",
    "sci":  "Наука",
    "mov":  "Кино",
}

def _topics_kb() -> Mk:
    """
        Сформировать клавиатуру выбора темы викторины.

        Returns
        -------
        telegram.InlineKeyboardMarkup
            Кнопки-строки вида «История», «Наука», … с callback-датой
            `quiz_topic:<код_темы>`.
    """
    return Mk([
        [Btn(name, callback_data=f"quiz_topic:{code}")]
        for code, name in TOPICS.items()
    ])


def _ans_kb(topic: str, q_id: int, options: list[str]) -> Mk:
    """
        Создать клавиатуру с вариантами ответа на вопрос.

        Parameters
        ----------
        topic : str
            Код выбранной темы (hist/sci/mov) — нужен, чтобы затем
            задавать дополнительные вопросы той же категории.
        q_id : int
            Произвольный идентификатор вопроса (используем `id(text)`),
            включается в callback-data, чтобы различать разные вопросы.
        options : list[str]
            Список из трёх строк-вариантов ответа.

        Returns
        -------
        telegram.InlineKeyboardMarkup
            Три вертикальные кнопки-варианта (`quiz_ans:<q_id>:<idx>`).
    """
    return Mk([
        [Btn(txt, callback_data=f"quiz_ans:{q_id}:{i}")]
        for i, txt in enumerate(options)
    ])


def _after_kb(topic: str) -> Mk:
    """
        Клавиатура, показываемая после ответа пользователя.

        Parameters
        ----------
        topic : str
            Код текущей темы, чтобы «➕ Ещё вопрос» оставался в рамках
            того же раздела.

        Returns
        -------
        telegram.InlineKeyboardMarkup
            • «➕ Ещё вопрос» (`quiz_next:<topic>`)
            • «🔙 Главное меню» (`quiz_finish`)
    """
    return Mk([
        [Btn("➕ Ещё вопрос", callback_data=f"quiz_next:{topic}")],
        [Btn("🔙 Главное меню", callback_data="quiz_finish")],
    ])


async def start_quiz_command(update: Update,
                             context: ContextTypes.DEFAULT_TYPE) -> int:
    """
        Точка входа для `/quiz` или кнопки из главного меню.

        Показывает обложку и клавиатуру с темами викторины.

        Returns
        -------
        int
            Состояние **TOPIC** (ожидаем выбор темы).
    """
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.delete()
    await update.effective_message.reply_photo(
        IMAGE,
        caption="📚 Выберите тему квиза:",
        reply_markup=_topics_kb(),
    )
    return TOPIC


async def choose_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
        Обработать кнопку выбора темы.

        Сохраняет выбранный `topic_code` в `context.user_data`
        и сразу же генерирует первый вопрос, вызывая `_ask_question`.

        Returns
        -------
        int
            Состояние **ASK** (показ вопроса).
    """
    q = update.callback_query
    await q.answer()
    topic_code = q.data.split(":")[1]
    context.user_data["topic"] = topic_code
    return await _ask_question(q, context)


async def _ask_question(target, context) -> int:
    """
        Запросить у ChatGPT вопрос и отобразить его пользователю.

        Parameters
        ----------
        target : telegram.CallbackQuery | telegram.Message
            Объект, с помощью которого следует отправить/отредактировать
            сообщение (может быть как `CallbackQuery`, так и `Message`).
        context : telegram.ext.CallbackContext
            PTB-контекст; используются `context.user_data['topic']`
            и запись правильного ответа в `context.user_data['right']`.

        Returns
        -------
        int
            Состояние **ASK** — остаёмся на этапе ответов.
    """
    topic_code = context.user_data["topic"]
    topic_ru   = TOPICS[topic_code]

    q_text, options, right = await get_quiz_question(topic_ru)

    context.user_data["right"] = right

    kb = _ans_kb(topic_code, id(q_text), options)

    try:
        await target.edit_message_caption(q_text, reply_markup=kb)
    except Exception:                               # noqa: BLE001
        await target.message.reply_photo(IMAGE, caption=q_text, reply_markup=kb)

    return ASK


async def handle_answer(update: Update,
                        context: ContextTypes.DEFAULT_TYPE) -> int:
    """
        Обработать выбор варианта ответа пользователем.

        • Сравнивает выбранный индекс с сохранённым `right`.
        • Сообщает «✅ Верно!» или «❌ Неверно!».
        • Показывает клавиатуру `_after_kb()`.

        Returns
        -------
        int
            Состояние **ASK** — пользователь может запросить новый вопрос
            той же темы или вернуться в меню.
    """
    q = update.callback_query
    await q.answer()

    chosen = int(q.data.split(":")[-1])
    right  = context.user_data.get("right", -1)

    msg = "✅ Верно!" if chosen == right else "❌ Неверно!"
    topic_code = context.user_data["topic"]
    await q.message.reply_text(msg, reply_markup=_after_kb(topic_code))
    return ASK


async def next_or_finish(update: Update,
                         context: ContextTypes.DEFAULT_TYPE) -> int:
    """
        Переключатель между «➕ Ещё вопрос» и «🔙 Главное меню».

        • Если callback-data начинается с `quiz_next:` —
          запускаем `_ask_question` для той же темы.
        • Иначе (`quiz_finish`) выходим из ConversationHandler
          и показываем главное меню.

        Returns
        -------
        int
            Либо **ASK** (новый вопрос), либо `ConversationHandler.END`.
    """
    q = update.callback_query
    await q.answer()

    if q.data.startswith("quiz_next:"):
        return await _ask_question(q, context)

    from handlers.basic import show_main_menu
    await show_main_menu(update, context)
    return ConversationHandler.END


def build_quiz_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("quiz", start_quiz_command),
            CallbackQueryHandler(start_quiz_command, pattern=f"^{CB_QUIZ_RUN}$"),
        ],
        states={
            TOPIC: [CallbackQueryHandler(choose_topic, pattern="^quiz_topic:")],
            ASK: [
                CallbackQueryHandler(handle_answer, pattern="^quiz_ans:"),
                CallbackQueryHandler(next_or_finish,
                                     pattern="^quiz_(next|finish)"),
            ],
        },
        fallbacks=[],
        per_chat=True, per_user=False, per_message=False,
    )
