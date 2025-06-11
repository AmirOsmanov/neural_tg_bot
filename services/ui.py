from telegram import InlineKeyboardButton as Btn, InlineKeyboardMarkup as Mk

CB_MAIN_MENU     = "main_menu"          # 🔙 «Главное меню»
CB_GPT           = "main_gpt"           # 🤖 ChatGPT-диалог
CB_RANDOM_FACT   = "main_rand_fact"     # 🧠 Случайный факт
CB_PERSONA_TALK  = "main_talk"          # 🗣️ Диалог с личностью
CB_QUIZ          = "main_quiz"          # ❓ Квиз
CB_COOK          = "main_cook"          # 👨‍🍳 Подготовка меню

CB_QUIZ_RUN      = "quiz_run"

CB_P_EINSTEIN    = "persona_einstein"
CB_P_OPPENHEIMER = "persona_oppenheimer"
CB_P_KURCHATOV   = "persona_kurchatov"
CB_END_TALK      = "end_talk"

CB_COOK_PREFIX   = "cook_kcal"          # Префикс: cook_kcal:<n>
CB_COOK_BACK     = "cook_back"          # «Выбрать другой лимит»


def get_main_menu_keyboard() -> Mk:
    return Mk([
        [Btn("🧠 Рандом-факт",        callback_data=CB_RANDOM_FACT)],
        [Btn("🤖 ChatGPT",            callback_data=CB_GPT)],
        [Btn("🗣️ Диалог с личностью", callback_data=CB_PERSONA_TALK)],
        [Btn("❓ Квиз",               callback_data=CB_QUIZ_RUN)],
        [Btn("👨‍🍳 Подготовка меню",   callback_data=CB_COOK)],
    ])


def get_persona_keyboard() -> Mk:
    return Mk([
        [Btn("Альберт Эйнштейн",   callback_data=CB_P_EINSTEIN)],
        [Btn("Роберт Оппенгеймер", callback_data=CB_P_OPPENHEIMER)],
        [Btn("Игорь Курчатов",     callback_data=CB_P_KURCHATOV)],
        [Btn("🔙 Главное меню",    callback_data=CB_MAIN_MENU)],
    ])


def get_end_talk_keyboard() -> Mk:
    return Mk([
        [Btn("🔚 Закончить диалог", callback_data=CB_END_TALK)],
        [Btn("🔙 Главное меню",     callback_data=CB_MAIN_MENU)],
    ])


def get_cook_kcal_keyboard() -> Mk:
    return Mk([
        [Btn("1000 ккал", callback_data=f"{CB_COOK_PREFIX}:1000"),
         Btn("1500 ккал", callback_data=f"{CB_COOK_PREFIX}:1500")],
        [Btn("2000 ккал", callback_data=f"{CB_COOK_PREFIX}:2000"),
         Btn("2500 ккал", callback_data=f"{CB_COOK_PREFIX}:2500")],
        [Btn("3000 ккал", callback_data=f"{CB_COOK_PREFIX}:3000")],
        [Btn("🔙 Главное меню", callback_data=CB_MAIN_MENU)],
    ])


def get_cook_result_keyboard() -> Mk:
    return Mk([
        [Btn("🔄 Выбрать другой лимит", callback_data=CB_COOK_BACK)],
        [Btn("🔙 Главное меню",         callback_data=CB_MAIN_MENU)],
    ])
