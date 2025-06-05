from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🎲 Рандомный факт", callback_data="random_fact")],
        [InlineKeyboardButton("🤖 ChatGPT", callback_data="gpt_run")],
        [InlineKeyboardButton("👥 Диалог с личностью", callback_data="talk_run")],
        [InlineKeyboardButton("🧠 Квиз", callback_data="quiz_run")],
        [InlineKeyboardButton("👨‍🍳 Подготовка меню (скоро)", callback_data="cook_coming_soon")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_persona_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("👤 Альберт Эйнштейн", callback_data="persona_einstein")],
        [InlineKeyboardButton("👥 Дж. Опенгеймер", callback_data="persona_oppenheimer")],
        [InlineKeyboardButton("⚛️ Игорь Курчатов", callback_data="persona_kurchatov")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_end_talk_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🏠 Закончить", callback_data="end_talk")]
    ]
    return InlineKeyboardMarkup(keyboard)
