from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Задачи", callback_data="tasks")
    kb.button(text="📅 Календарь", callback_data="calendar_open")
    kb.button(text="📌 План дня", callback_data="day")
    kb.button(text="📊 Статистика", callback_data="stats") # <--- НОВАЯ КНОПКА
    kb.button(text="🤖 ИИ ассистент", callback_data="ai")
    kb.adjust(2)
    return kb.as_markup()


def ai_exit_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅ Выйти", callback_data="ai_stop")
    return kb.as_markup()

