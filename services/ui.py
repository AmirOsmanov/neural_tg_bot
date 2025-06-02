from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu_keyboard():
    """Возвращает клавиатуру главного меню"""
    keyboard = [
        [InlineKeyboardButton("🎲 Рандомный факт", callback_data="random_fact")],
        [InlineKeyboardButton("🤖 ChatGPT", callback_data="gpt_run")],
        [InlineKeyboardButton("👥 Диалог с личностью (скоро)", callback_data="talk_coming_soon")],
        [InlineKeyboardButton("🧠 Квиз (скоро)", callback_data="quiz_coming_soon")],
        [InlineKeyboardButton("👨‍🍳 Подготовка меню (скоро)", callback_data="cook_coming_soon")],
    ]
    return InlineKeyboardMarkup(keyboard)
