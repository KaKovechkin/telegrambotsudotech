# app/keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 План дня"), KeyboardButton(text="⏰ Напоминания")],
        [KeyboardButton(text="🧠 Мои задачи"), KeyboardButton(text="🤖 ИИ агент")],
        [KeyboardButton(text="⚙️ Настройки")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выбери раздел 👇"
)

plan_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить задачу")],
        [KeyboardButton(text="📋 Список задач")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

reminder_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔔 Новое напоминание")],
        [KeyboardButton(text="📆 Активные напоминания")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

tasks_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить задачу")],
        [KeyboardButton(text="🚧 Незавершённые задачи"), KeyboardButton(text="✅ Завершённые задачи")],
        [KeyboardButton(text="✏️ Редактировать задачу"), KeyboardButton(text="🗑 Удалить задачу")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

settings_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧑 Изменить имя")],
        [KeyboardButton(text="🔔 Настройки уведомлений")],
        [KeyboardButton(text="🗑 Очистить данные")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

ai_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✨ Сгенерировать день")],
        [KeyboardButton(text="⚡ Оптимизировать")],
        [KeyboardButton(text="❓ Помощь")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)
