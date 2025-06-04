# services/ui.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру главного меню:
      • Рандомный факт
      • ChatGPT
      • Диалог с личностью
      • Квиз (скоро)
      • Подготовка меню (скоро)
    """
    keyboard = [
        [InlineKeyboardButton("🎲 Рандомный факт", callback_data="random_fact")],
        [InlineKeyboardButton("🤖 ChatGPT", callback_data="gpt_run")],
        [InlineKeyboardButton("👥 Диалог с личностью", callback_data="talk_run")],
        [InlineKeyboardButton("🧠 Квиз (скоро)", callback_data="quiz_coming_soon")],
        [InlineKeyboardButton("👨‍🍳 Подготовка меню (скоро)", callback_data="cook_coming_soon")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_persona_keyboard() -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру выбора личности для /talk:
      • Альберт Эйнштейн
      • Опенгеймер
      • Курчатов
    """
    keyboard = [
        [InlineKeyboardButton("👤 Альберт Эйнштейн", callback_data="persona_einstein")],
        [InlineKeyboardButton("👥 Дж. Опенгеймер", callback_data="persona_oppenheimer")],
        [InlineKeyboardButton("⚛️ Игорь Курчатов", callback_data="persona_kurchatov")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_end_talk_keyboard() -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру «Закончить» для чата /talk.
    Кнопка отправляет callback_data="end_talk".
    """
    keyboard = [
        [InlineKeyboardButton("🏠 Закончить", callback_data="end_talk")]
    ]
    return InlineKeyboardMarkup(keyboard)
