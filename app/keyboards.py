from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- КОНФИГУРАЦИЯ ---
# Ваша ссылка на GitHub Pages
WEB_APP_URL = "https://kakovechkin.github.io/MoyRitm-App/" 

# --- ГЛАВНОЕ МЕНЮ ---
# Переименовали main_keyboard -> main_menu, чтобы совпадало с импортом в handlers.py
def main_menu():
    builder = InlineKeyboardBuilder()
    
    # 1. Кнопка запуска Mini App (Самая главная)
    builder.row(InlineKeyboardButton(
        text="📱 Открыть МойРитм App", 
        web_app=WebAppInfo(url=WEB_APP_URL)
    ))

    # 2. Стандартные кнопки (резервный вариант)
    builder.row(
        InlineKeyboardButton(text="📅 План на сегодня", callback_data="plan_today"),
        InlineKeyboardButton(text="➕ Быстрая задача", callback_data="add_task")
    )

    # 3. Дополнительные функции
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="stats"),
        InlineKeyboardButton(text="🤖 Спросить ИИ", callback_data="ask_ai")
    )
    
    return builder.as_markup()

# --- КНОПКА ВЫХОДА ИЗ AI (Была пропущена, но используется в handlers) ---
def ai_exit_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="⏹ Выйти из режима ИИ", callback_data="ai_stop")
    return builder.as_markup()

# --- КНОПКИ ДЕЙСТВИЙ С ЗАДАЧЕЙ (В чате) ---
def task_actions(task_id, status):
    builder = InlineKeyboardBuilder()
    if status == "pending":
        builder.button(text="✅ Выполнено", callback_data=f"done_{task_id}")
    else:
        builder.button(text="🔄 Вернуть", callback_data=f"return_{task_id}")
    
    builder.button(text="🗑 Удалить", callback_data=f"delete_{task_id}")
    return builder.as_markup()

# --- КНОПКА ОТМЕНЫ ---
def cancel_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])
    return keyboard