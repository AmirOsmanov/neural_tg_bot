"""
services.ui
===========

Единое место, где **объявляются** все callback-идентификаторы (`callback_data`)
и **строятся** Inline-клавиатуры Telegram-бота.

Зачем выносить всё сюда
-----------------------
* ▸ _Нет «магических строк»_ — каждая кнопка объявлена единожды.
* ▸ Проще отлавливать коллизии: если два модуля случайно выберут один
  и тот же `callback_data`, это будет видно сразу.
* ▸ Любые будущие изменения (переименование кнопки, добавление новой)
  происходят в одном месте, а не разбросаны по проекту.

Содержимое
----------
* **Константы** ― публичные и внутренние callback'и.
* **Фабрики клавиатур** ― функции, которые возвращают
  `telegram.InlineKeyboardMarkup` для разных сценариев бота.

> ❗ *Важно*: модуль не зависит от файлов handlers — обратный импорт
> отсутствует, что упрощает тестирование.
"""

from telegram import InlineKeyboardButton as Btn, InlineKeyboardMarkup as Mk

CB_MAIN_MENU     = "main_menu"          # 🔙 «Главное меню»
CB_GPT           = "main_gpt"           # 🤖 ChatGPT-диалог
CB_RANDOM_FACT   = "main_rand_fact"     # 🧠 Случайный факт
CB_PERSONA_TALK  = "main_talk"          # 🗣️ Диалог с личностью
CB_QUIZ          = "main_quiz"          # ❓ Квиз
CB_COOK          = "main_cook"          # 👨‍🍳 Подготовка меню

CB_TRANSLATOR    = "main_translator"    # 🈂️ Переводчик

CB_QUIZ_RUN      = "quiz_run"

CB_P_EINSTEIN    = "persona_einstein"
CB_P_OPPENHEIMER = "persona_oppenheimer"
CB_P_KURCHATOV   = "persona_kurchatov"
CB_END_TALK      = "end_talk"

CB_COOK_PREFIX   = "cook_kcal"          # Префикс: cook_kcal:<n>
CB_COOK_BACK     = "cook_back"          # «Выбрать другой лимит»


def get_main_menu_keyboard() -> Mk:
    """
    Главная клавиатура бота.

    Возвращает список кнопок-действий, которые пользователь видит
    после команды `/start` или из любого места через «Главное меню».

    Returns
    -------
    telegram.InlineKeyboardMarkup
        Структура вида:
        🧠 Рандом-факт
        🤖 ChatGPT
        🗣️ Диалог с личностью
        ❓ Квиз
        👨‍🍳 Подготовка меню
        🌐 Переводчик
    """
    return Mk([
        [Btn("🎲 Случайный факт",        callback_data=CB_RANDOM_FACT)],
        [Btn("🤖 ChatGPT",            callback_data=CB_GPT)],
        [Btn("🈂️ Переводчик", callback_data=CB_TRANSLATOR)],
        [Btn("🗣️ Диалог с личностью", callback_data=CB_PERSONA_TALK)],
        [Btn("❓ Квиз",               callback_data=CB_QUIZ_RUN)],
        [Btn("🍱 Меню на неделю",   callback_data=CB_COOK)],
    ])


def get_persona_keyboard() -> Mk:
    """
        Клавиатура выбора исторической личности для «ролевого» чата.

        Returns
        -------
        telegram.InlineKeyboardMarkup
            Три личности + кнопка возврата в меню.
    """
    return Mk([
        [Btn("Альберт Эйнштейн",   callback_data=CB_P_EINSTEIN)],
        [Btn("Роберт Оппенгеймер", callback_data=CB_P_OPPENHEIMER)],
        [Btn("Игорь Курчатов",     callback_data=CB_P_KURCHATOV)],
        [Btn("🔙 Главное меню",    callback_data=CB_MAIN_MENU)],
    ])


def get_end_talk_keyboard() -> Mk:
    """
        Клавиатура, располагающаяся под каждым ответом «персоны».

        Состоит из двух действий:
        * 🔚 Закончить диалог ― завершает `ConversationHandler`;
        * 🔙 Главное меню.

        Returns
        -------
        telegram.InlineKeyboardMarkup
    """
    return Mk([
        [Btn("🔚 Закончить диалог", callback_data=CB_END_TALK)],
        [Btn("🔙 Главное меню",     callback_data=CB_MAIN_MENU)],
    ])


def get_cook_kcal_keyboard() -> Mk:
    """
        Пять вариантов суточного лимита ккал для генерации недельного меню.

        Returns
        -------
        telegram.InlineKeyboardMarkup
            * 1000 ккал, 1500 ккал, 2000 ккал, 2500 ккал, 3000 ккал
            * Плюс кнопка возврата в «Главное меню».
    """
    return Mk([
        [Btn("1000 ккал", callback_data=f"{CB_COOK_PREFIX}:1000"),
         Btn("1500 ккал", callback_data=f"{CB_COOK_PREFIX}:1500")],
        [Btn("2000 ккал", callback_data=f"{CB_COOK_PREFIX}:2000"),
         Btn("2500 ккал", callback_data=f"{CB_COOK_PREFIX}:2500")],
        [Btn("3000 ккал", callback_data=f"{CB_COOK_PREFIX}:3000")],
        [Btn("🔙 Главное меню", callback_data=CB_MAIN_MENU)],
    ])


def get_cook_result_keyboard() -> Mk:
    """
        Клавиатура, размещаемая сразу под сообщением «✅ Меню готово!».

        Позволяет:
        * «🔄 Выбрать другой лимит» — вернуться к выбору ккал;
        * «🔙 Главное меню».

        Returns
        -------
        telegram.InlineKeyboardMarkup
    """
    return Mk([
        [Btn("🔄 Выбрать другой лимит", callback_data=CB_COOK_BACK)],
        [Btn("🔙 Главное меню",         callback_data=CB_MAIN_MENU)],
    ])
