from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Задачи", callback_data="tasks")
    kb.button(text="📅 План дня", callback_data="day")
    kb.button(text="⏰ Напоминания", callback_data="reminders")
    kb.button(text="🤖 ИИ ассистент", callback_data="ai")
    kb.adjust(2)
    return kb.as_markup()

def ai_exit_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅ Выйти", callback_data="ai_stop")
    return kb.as_markup()
