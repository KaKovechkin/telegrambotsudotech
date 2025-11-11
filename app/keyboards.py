from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# --- Главное меню ---
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 План дня"), KeyboardButton(text="⏰ Напоминания")],
        [KeyboardButton(text="🧠 Мои задачи"), KeyboardButton(text="🤖 ИИ агент")],
        [KeyboardButton(text="⚙️ Настройки")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выбери раздел 👇"
)


# --- Подменю: План дня ---
plan_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить задачу")],
        [KeyboardButton(text="📋 Список задач")],
        [KeyboardButton(text="✅ Завершить задачу")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)


# --- Подменю: Напоминания ---
reminder_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔔 Новое напоминание")],
        [KeyboardButton(text="📆 Активные напоминания")],
        [KeyboardButton(text="❌ Удалить напоминание")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)


# --- Подменю: Мои задачи ---
tasks_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚧 Незавершённые задачи")],
        [KeyboardButton(text="✅ Завершённые задачи")],
        [KeyboardButton(text="⭐ Цели недели")],
        [KeyboardButton(text="📊 Статистика продуктивности")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)


# --- Подменю: Настройки ---
settings_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧑 Изменить имя")],
        [KeyboardButton(text="🔔 Настройки уведомлений")],
        [KeyboardButton(text="🗑 Очистить данные")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)


# --- Подменю: ИИ Агент ---
ai_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✨ Сгенерировать день")],
        [KeyboardButton(text="⚡ Оптимизировать")],
        [KeyboardButton(text="❓ Помощь")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)
