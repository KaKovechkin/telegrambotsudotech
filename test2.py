import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardMarkup,
    KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Хранилище состояний
storage = MemoryStorage()

# Создание роутера
router = Router()

# Временное хранилище данных
user_tasks: Dict[int, list] = {}
user_settings: Dict[int, Dict[str, Any]] = {}


# Состояния FSM
class TaskCreation(StatesGroup):
    waiting_for_text = State()
    waiting_for_time = State()
    waiting_for_priority = State()
    waiting_for_category = State()


class AIAssistant(StatesGroup):
    waiting_for_template = State()


# ===== КЛАВИАТУРЫ =====

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню"""
    keyboard = [
        [KeyboardButton(text="📅 Сегодня"), KeyboardButton(text="📆 Неделя")],
        [KeyboardButton(text="➕ Задача"), KeyboardButton(text="🧠 AI Помощник")],
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="⚙️ Настройки")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_task_creation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для создания задачи"""
    # Время
    time_buttons = [
        [
            InlineKeyboardButton(text="🕘 09:00", callback_data="time_09:00"),
            InlineKeyboardButton(text="🕙 10:00", callback_data="time_10:00"),
            InlineKeyboardButton(text="🕚 11:00", callback_data="time_11:00")
        ],
        [
            InlineKeyboardButton(text="🕛 12:00", callback_data="time_12:00"),
            InlineKeyboardButton(text="🕐 13:00", callback_data="time_13:00"),
            InlineKeyboardButton(text="🕑 14:00", callback_data="time_14:00")
        ],
        [
            InlineKeyboardButton(text="🕒 15:00", callback_data="time_15:00"),
            InlineKeyboardButton(text="🕓 16:00", callback_data="time_16:00"),
            InlineKeyboardButton(text="🕔 17:00", callback_data="time_17:00")
        ]
    ]

    # Приоритеты
    priority_buttons = [
        [
            InlineKeyboardButton(text="🎯 Высокий", callback_data="priority_high"),
            InlineKeyboardButton(text="🔸 Средний", callback_data="priority_medium"),
            InlineKeyboardButton(text="🔹 Низкий", callback_data="priority_low")
        ]
    ]

    # Категории
    category_buttons = [
        [
            InlineKeyboardButton(text="💼 Работа", callback_data="category_work"),
            InlineKeyboardButton(text="🏃 Спорт", callback_data="category_sport"),
            InlineKeyboardButton(text="🎓 Учеба", callback_data="category_study")
        ],
        [
            InlineKeyboardButton(text="❤️ Личное", callback_data="category_personal"),
            InlineKeyboardButton(text="🛒 Покупки", callback_data="category_shopping"),
            InlineKeyboardButton(text="🎉 Отдых", callback_data="category_rest")
        ]
    ]

    # Управление
    control_buttons = [
        [
            InlineKeyboardButton(text="✅ Сохранить", callback_data="save_task"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_task")
        ]
    ]

    all_buttons = time_buttons + priority_buttons + category_buttons + control_buttons
    return InlineKeyboardMarkup(inline_keyboard=all_buttons)


def get_task_management_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для управления задачей"""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Выполнено", callback_data=f"complete_{task_id}"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_{task_id}")
        ],
        [
            InlineKeyboardButton(text="📅 Перенести", callback_data=f"move_{task_id}"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_{task_id}")
        ],
        [
            InlineKeyboardButton(text="🔁 Повторить", callback_data=f"repeat_{task_id}"),
            InlineKeyboardButton(text="➡️ Поделиться", callback_data=f"share_{task_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_quick_actions_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Быстрые действия под задачей"""
    keyboard = [
        [
            InlineKeyboardButton(text="➕ Подзадача", callback_data=f"subtask_{task_id}"),
            InlineKeyboardButton(text="⏰ Напомнить", callback_data=f"remind_{task_id}"),
            InlineKeyboardButton(text="🔄 Разделить", callback_data=f"split_{task_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_ai_assistant_keyboard() -> InlineKeyboardMarkup:
    """Главное меню AI помощника"""
    keyboard = [
        [
            InlineKeyboardButton(text="🎯 Сгенерировать день", callback_data="ai_generate_day"),
            InlineKeyboardButton(text="💡 Оптимизировать", callback_data="ai_optimize")
        ],
        [
            InlineKeyboardButton(text="📊 Проанализировать", callback_data="ai_analyze"),
            InlineKeyboardButton(text="🚀 Мотивация", callback_data="ai_motivation")
        ],
        [
            InlineKeyboardButton(text="🛠️ Шаблоны", callback_data="ai_templates"),
            InlineKeyboardButton(text="❓ Помощь", callback_data="ai_help")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_ai_templates_keyboard() -> InlineKeyboardMarkup:
    """Шаблоны расписания AI"""
    keyboard = [
        [
            InlineKeyboardButton(text="👔 Рабочий день", callback_data="template_work"),
            InlineKeyboardButton(text="🏠 Удаленка", callback_data="template_remote")
        ],
        [
            InlineKeyboardButton(text="📚 Учебный день", callback_data="template_study"),
            InlineKeyboardButton(text="🧘 Выходной", callback_data="template_dayoff")
        ],
        [
            InlineKeyboardButton(text="💪 Продуктивный", callback_data="template_productive"),
            InlineKeyboardButton(text="🎨 Творческий", callback_data="template_creative")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="ai_back")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_calendar_navigation() -> InlineKeyboardMarkup:
    """Навигация по дням"""
    keyboard = [
        [
            InlineKeyboardButton(text="◀️ Вчера", callback_data="nav_yesterday"),
            InlineKeyboardButton(text="📅 Сегодня", callback_data="nav_today"),
            InlineKeyboardButton(text="▶️ Завтра", callback_data="nav_tomorrow")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_week_view_keyboard() -> InlineKeyboardMarkup:
    """Недельный просмотр"""
    keyboard = [
        [
            InlineKeyboardButton(text="Пн 12", callback_data="day_mon"),
            InlineKeyboardButton(text="Вт 13", callback_data="day_tue"),
            InlineKeyboardButton(text="Ср 14", callback_data="day_wed"),
            InlineKeyboardButton(text="Чт 15", callback_data="day_thu"),
            InlineKeyboardButton(text="Пт 16", callback_data="day_fri")
        ],
        [
            InlineKeyboardButton(text="Сб 17", callback_data="day_sat"),
            InlineKeyboardButton(text="Вс 18", callback_data="day_sun"),
            InlineKeyboardButton(text="🗓️ Неделя", callback_data="week_view")
        ],
        [
            InlineKeyboardButton(text="📅 Текущая", callback_data="week_current"),
            InlineKeyboardButton(text="📅 Следующая", callback_data="week_next")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_statistics_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура статистики"""
    keyboard = [
        [
            InlineKeyboardButton(text="📅 Сегодня", callback_data="stats_today"),
            InlineKeyboardButton(text="📆 Неделя", callback_data="stats_week"),
            InlineKeyboardButton(text="📊 Месяц", callback_data="stats_month")
        ],
        [
            InlineKeyboardButton(text="🔄 Сравнить", callback_data="stats_compare"),
            InlineKeyboardButton(text="📈 Тренды", callback_data="stats_trends")
        ],
        [
            InlineKeyboardButton(text="✅ Выполнено", callback_data="stats_completed"),
            InlineKeyboardButton(text="⏰ Время", callback_data="stats_time")
        ],
        [
            InlineKeyboardButton(text="🎯 Приоритеты", callback_data="stats_priority"),
            InlineKeyboardButton(text="📂 Категории", callback_data="stats_categories")
        ],
        [
            InlineKeyboardButton(text="📉 Продуктивность", callback_data="stats_productivity"),
            InlineKeyboardButton(text="🏆 Достижения", callback_data="stats_achievements")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура настроек"""
    keyboard = [
        [
            InlineKeyboardButton(text="⏰ Уведомления", callback_data="settings_notifications"),
            InlineKeyboardButton(text="🎨 Тема", callback_data="settings_theme")
        ],
        [
            InlineKeyboardButton(text="🔄 Синхронизация", callback_data="settings_sync"),
            InlineKeyboardButton(text="📤 Экспорт", callback_data="settings_export")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ===== ОБРАБОТЧИКИ КОМАНД =====

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user = message.from_user
    welcome_text = f"""
Привет, {user.first_name}! 👋

Я твой персональный помощник по планированию "МойРити". Я помогу тебе:

📅 Управлять задачами и расписанием
🧠 Оптимизировать день с помощью AI
📊 Анализировать продуктивность
🎯 Достигать целей эффективнее

Выбери действие в главном меню ниже:
    """

    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard()
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = """
🤖 **Доступные команды:**

**Основные:**
/start - Главное меню
/add - Быстро добавить задачу
/today - Задачи на сегодня
/week - Задачи на неделю

**AI Помощник:**
/ai - Меню AI помощника
/plan_day - Планирование дня
/optimize - Оптимизация задач

**Статистика:**
/stats - Статистика продуктивности

**Настройки:**
/settings - Настройки бота

Или используй кнопки ниже для навигации!
    """
    await message.answer(help_text, reply_markup=get_main_menu_keyboard())


@router.message(Command("add"))
async def cmd_add_task(message: Message, state: FSMContext):
    """Быстрое добавление задачи"""
    args = message.text.split()[1:]
    task_text = " ".join(args)

    if task_text:
        await message.answer(
            f"✅ Быстрая задача добавлена:\n*{task_text}*",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        # Если текст не указан, начинаем процесс создания задачи
        await message.answer(
            "📝 Введите описание задачи:",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(TaskCreation.waiting_for_text)


@router.message(Command("plan_day"))
async def cmd_plan_day(message: Message):
    """Планирование дня через AI"""
    ai_plan_text = """
🧠 **AI ПЛАНИРОВАНИЕ ДНЯ**

На основе ваших привычек и целей, AI предлагает:

🕘 **УТРО (09:00-12:00):**
• 09:00-10:30 - Сложные задачи (максимальная продуктивность)
• 10:30-11:00 - Кофе-брейк + планирование
• 11:00-12:00 - Работа над проектами

🕛 **ДЕНЬ (12:00-18:00):**
• 12:00-13:00 - Обед + отдых
• 13:00-15:00 - Встречи и коммуникация
• 15:00-16:30 - Творческие задачи
• 16:30-17:00 - Спорт/разминка
• 17:00-18:00 - Завершение задач

🕖 **ВЕЧЕР (18:00-21:00):**
• 18:00-19:00 - Учеба/саморазвитие
• 19:00-20:00 - Ужин с семьей
• 20:00-21:00 - Отдых, планирование завтрашнего дня
    """

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Оптимизировать", callback_data="optimize_day"),
            InlineKeyboardButton(text="💡 Другой стиль", callback_data="change_style"),
            InlineKeyboardButton(text="✅ Применить", callback_data="apply_day_plan")
        ]
    ])

    await message.answer(ai_plan_text, reply_markup=keyboard)


# ===== ОБРАБОТЧИКИ ГЛАВНОГО МЕНЮ =====

@router.message(F.text == "📅 Сегодня")
async def show_today_tasks(message: Message):
    """Показ задач на сегодня"""
    today = datetime.now().strftime("%d.%m.%Y")

    tasks_text = f"""
📅 **СЕГОДНЯ • {today}**

✅ Завершено: 3/8 задач
⏰ Осталось времени: 6 часов

🎯 **ВЫСОКИЙ ПРИОРИТЕТ:**
• Подготовить отчет (до 14:00)
• Совещание с командой (15:00-16:00)

🔸 **СРЕДНИЙ ПРИОРИТЕТ:**
• Занятие спортом (18:00)
• Заказать продукты

🔹 **НИЗКИЙ ПРИОРИТЕТ:**
• Почитать книгу
• Убраться на столе

🧠 **AI РЕКОМЕНДУЕТ:** 
«У вас плотный день - рекомендую сделать 15-минутный перерыв в 17:00»
    """

    await message.answer(tasks_text, reply_markup=get_calendar_navigation())


@router.message(F.text == "📆 Неделя")
async def show_week_tasks(message: Message):
    """Показ задач на неделю"""
    week_text = """
📆 **НЕДЕЛЯ • 12-18 ДЕКАБРЯ**

┌─────────┬─────────────┐
│   День  │   Задачи    │
├─────────┼─────────────┤
│  Пн 12  │     5 ✅    │
│  Вт 13  │     8 ✅    │
│  Ср 14  │     6 ⏰    │
│  Чт 15  │     7 📅    │
│  Пт 16  │     9 📅    │
│  Сб 17  │     4 📅    │
│  Вс 18  │     3 📅    │
└─────────┴─────────────┘

**📈 Прогресс недели:** 19/42 задач
**🎯 Эффективность:** 76%
    """

    await message.answer(week_text, reply_markup=get_week_view_keyboard())


@router.message(F.text == "➕ Задача")
async def create_task_start(message: Message, state: FSMContext):
    """Начало создания задачи"""
    instruction_text = """
📝 **Создание новой задачи**

1. Введите описание задачи
2. Выберите время выполнения
3. Установите приоритет
4. Выберите категорию

Сначала введите текст задачи:
    """

    await message.answer(instruction_text, reply_markup=ReplyKeyboardRemove())
    await state.set_state(TaskCreation.waiting_for_text)


@router.message(F.text == "🧠 AI Помощник")
async def show_ai_assistant(message: Message):
    """Показ AI помощника"""
    ai_text = """
🧠 **AI ПОМОЩНИК**

Я помогу вам:
• 🤖 Автоматически планировать день
• 💡 Оптимизировать расписание
• 📊 Анализировать продуктивность
• 🎯 Предлагать улучшения

Выберите действие:
    """

    await message.answer(ai_text, reply_markup=get_ai_assistant_keyboard())


@router.message(F.text == "📊 Статистика")
async def show_statistics(message: Message):
    """Показ статистики"""
    stats_text = """
📊 **СТАТИСТИКА ПРОДУКТИВНОСТИ**

📅 **За сегодня:**
• Выполнено: 8/12 задач (67%)
• Время работы: 6ч 45мин
• Продуктивность: 72%

📈 **За неделю:**
• Среднее выполнение: 75%
• Лучший день: Вторник (89%)
• Всего задач: 84

🎯 **Распределение:**
• Высокий приоритет: 35%
• Средний приоритет: 45%
• Низкий приоритет: 20%

🏆 **Достижения:**
• Непрерывная серия: 5 дней
• Рекорд продуктивности: 92%
    """

    await message.answer(stats_text, reply_markup=get_statistics_keyboard())


@router.message(F.text == "⚙️ Настройки")
async def show_settings_menu(message: Message):
    """Показ настроек"""
    settings_text = """
⚙️ **НАСТРОЙКИ**

🔔 **Уведомления:** Включены
🎨 **Тема:** Светлая
🔄 **Синхронизация:** Отключена
📤 **Авто-экспорт:** Нет

Выберите параметр для изменения:
    """

    await message.answer(settings_text, reply_markup=get_settings_keyboard())


# ===== ОБРАБОТЧИКИ СОСТОЯНИЙ (FSM) =====

@router.message(TaskCreation.waiting_for_text)
async def process_task_text(message: Message, state: FSMContext):
    """Обработка текста задачи"""
    task_text = message.text
    await state.update_data(task_text=task_text)

    await message.answer(
        f"✅ Задача сохранена: *{task_text}*\n\nТеперь настройте параметры:",
        reply_markup=get_task_creation_keyboard()
    )
    await state.set_state(TaskCreation.waiting_for_time)


# ===== ОБРАБОТЧИКИ CALLBACK QUERY =====

@router.callback_query(F.data.startswith("time_"))
async def handle_time_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора времени"""
    time = callback.data.split("_")[1]
    await state.update_data(task_time=time)

    await callback.message.edit_text(
        f"⏰ Время установлено: {time}\nВыберите приоритет:",
        reply_markup=get_task_creation_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("priority_"))
async def handle_priority_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора приоритета"""
    priority = callback.data.split("_")[1]
    priority_emoji = {"high": "🎯", "medium": "🔸", "low": "🔹"}
    await state.update_data(task_priority=priority)

    await callback.message.edit_text(
        f"{priority_emoji[priority]} Приоритет установлен\nВыберите категорию:",
        reply_markup=get_task_creation_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("category_"))
async def handle_category_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора категории"""
    category = callback.data.split("_")[1]
    category_names = {
        "work": "💼 Работа", "sport": "🏃 Спорт",
        "study": "🎓 Учеба", "personal": "❤️ Личное",
        "shopping": "🛒 Покупки", "rest": "🎉 Отдых"
    }
    await state.update_data(task_category=category)

    data = await state.get_data()
    task_text = data.get('task_text', 'Новая задача')

    await callback.message.edit_text(
        f"✅ Задача создана!\n\n"
        f"📝 *{task_text}*\n"
        f"⏰ Время: {data.get('task_time', 'Не указано')}\n"
        f"🎯 Приоритет: {priority_emoji.get(data.get('task_priority', 'medium'), '🔸')}\n"
        f"📂 Категория: {category_names[category]}\n\n"
        f"Нажмите 'Сохранить' для завершения",
        reply_markup=get_task_creation_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "save_task")
async def handle_save_task(callback: CallbackQuery, state: FSMContext):
    """Сохранение задачи"""
    data = await state.get_data()
    task_text = data.get('task_text', 'Новая задача')

    # Здесь должна быть логика сохранения в БД
    user_id = callback.from_user.id
    if user_id not in user_tasks:
        user_tasks[user_id] = []

    user_tasks[user_id].append({
        'text': task_text,
        'time': data.get('task_time'),
        'priority': data.get('task_priority', 'medium'),
        'category': data.get('task_category', 'general'),
        'created_at': datetime.now()
    })

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Новая задача", callback_data="new_task"),
            InlineKeyboardButton(text="📅 Посмотреть задачи", callback_data="view_tasks")
        ]
    ])

    await callback.message.edit_text(
        "✅ Задача успешно сохранена!\n\n"
        "Хотите создать еще одну задачу?",
        reply_markup=keyboard
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "cancel_task")
async def handle_cancel_task(callback: CallbackQuery, state: FSMContext):
    """Отмена создания задачи"""
    await callback.message.edit_text(
        "❌ Создание задачи отменено",
        reply_markup=get_main_menu_keyboard()
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "ai_templates")
async def handle_ai_templates(callback: CallbackQuery):
    """Показ шаблонов AI"""
    await callback.message.edit_text(
        "🛠️ **Шаблоны расписания**\n\nВыберите подходящий шаблон:",
        reply_markup=get_ai_templates_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "ai_back")
async def handle_ai_back(callback: CallbackQuery):
    """Возврат к меню AI"""
    ai_text = """
🧠 **AI ПОМОЩНИК**

Я помогу вам:
• 🤖 Автоматически планировать день
• 💡 Оптимизировать расписание
• 📊 Анализировать продуктивность
• 🎯 Предлагать улучшения

Выберите действие:
    """

    await callback.message.edit_text(ai_text, reply_markup=get_ai_assistant_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("template_"))
async def handle_template_selection(callback: CallbackQuery):
    """Обработка выбора шаблона"""
    template = callback.data.split("_")[1]
    template_names = {
        "work": "👔 Рабочий день",
        "remote": "🏠 Удаленная работа",
        "study": "📚 Учебный день",
        "dayoff": "🧘 Выходной",
        "productive": "💪 Продуктивный день",
        "creative": "🎨 Творческий день"
    }

    template_text = f"""
✅ Шаблон применен: {template_names[template]}

🧠 AI сгенерировал оптимальное расписание на день

📅 **Пример расписания:**
• 09:00-10:30 - Важные задачи
• 10:30-11:00 - Перерыв
• 11:00-13:00 - Работа/Учеба
• 13:00-14:00 - Обед
• 14:00-16:00 - Проекты
• 16:00-17:00 - Спорт/Отдых
• 17:00-18:30 - Завершение дел

Сохранить это расписание?
    """

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Применить", callback_data="apply_schedule"),
            InlineKeyboardButton(text="✏️ Изменить", callback_data="edit_schedule")
        ]
    ])

    await callback.message.edit_text(template_text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "nav_today")
async def handle_nav_today(callback: CallbackQuery):
    """Навигация: сегодня"""
    await show_today_tasks(callback.message)
    await callback.answer()


@router.callback_query(F.data == "week_view")
async def handle_week_view(callback: CallbackQuery):
    """Просмотр недели"""
    await show_week_tasks(callback.message)
    await callback.answer()


@router.callback_query(F.data.startswith("stats_"))
async def handle_statistics(callback: CallbackQuery):
    """Обработка статистики"""
    stat_type = callback.data.split("_")[1]
    stat_names = {
        "today": "сегодня",
        "week": "неделя",
        "month": "месяц",
        "compare": "сравнение",
        "trends": "тренды",
        "completed": "выполненные задачи",
        "time": "время",
        "priority": "приоритеты",
        "categories": "категории",
        "productivity": "продуктивность",
        "achievements": "достижения"
    }

    await callback.message.edit_text(
        f"📊 Статистика: {stat_names.get(stat_type, stat_type)}\n\n"
        f"Здесь будет детальная статистика...\n"
        f"(В разработке)",
        reply_markup=get_statistics_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("settings_"))
async def handle_settings(callback: CallbackQuery):
    """Обработка настроек"""
    setting_type = callback.data.split("_")[1]
    setting_names = {
        "notifications": "уведомления",
        "theme": "тема",
        "sync": "синхронизация",
        "export": "экспорт"
    }

    await callback.message.edit_text(
        f"⚙️ Настройка: {setting_names.get(setting_type, setting_type)}\n\n"
        f"Здесь будут настройки...\n"
        f"(В разработке)",
        reply_markup=get_settings_keyboard()
    )
    await callback.answer()


@router.callback_query()
async def handle_other_callbacks(callback: CallbackQuery):
    """Обработка остальных callback'ов"""
    await callback.message.edit_text(
        f"🔧 Функция в разработке\n\nКнопка: {callback.data}",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


# ===== ОСНОВНАЯ ФУНКЦИЯ =====

async def main():
    """Запуск бота"""
    # Вставьте ваш токен бота
    TOKEN = '8467505643:AAGDKpKvZeeQbKsyDIKiMbwJgtiuS2HDUBE'

    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=storage)
    dp.include_router(router)

    # Запуск бота
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())