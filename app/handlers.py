# app/handlers.py
import asyncio
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.enums import ChatAction

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

import app.keyboards as kb
from app.db import (
    add_task, list_tasks, get_task, mark_completed, delete_task,
    update_task_title, update_task_datetime, update_task_remind,
    get_pending_reminders
)

router = Router()


# ---------------------------------------------------------
#  FSM: ДОБАВЛЕНИЕ ЗАДАЧИ
# ---------------------------------------------------------
class AddTaskStates(StatesGroup):
    waiting_title = State()
    waiting_date = State()
    waiting_time = State()
    waiting_remind = State()


# ---------------------------------------------------------
#  FSM: РЕДАКТИРОВАНИЕ ЗАДАЧИ
# ---------------------------------------------------------
class EditTaskStates(StatesGroup):
    waiting_id = State()
    choose_field = State()
    edit_title = State()
    edit_date = State()
    edit_time = State()
    edit_remind = State()


# ---------------------------------------------------------
#  Чистая отправка сообщения
# ---------------------------------------------------------
async def send_clean(message: Message, text: str, keyboard=kb.main_menu):
    try:
        await message.delete()
    except:
        pass
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    await asyncio.sleep(0.4)
    await message.answer(text, reply_markup=keyboard)


# ---------------------------------------------------------
#  Планирование напоминания
# ---------------------------------------------------------
def schedule_reminder(scheduler: AsyncIOScheduler, bot, task_id: int, user_id: int, title: str, when_iso: str):
    when = datetime.strptime(when_iso, "%Y-%m-%d %H:%M:%S")
    if when <= datetime.utcnow():
        return

    job_id = f"reminder_{task_id}"
    try:
        scheduler.remove_job(job_id)
    except:
        pass

    trigger = DateTrigger(run_date=when)

    def job_send():
        loop = asyncio.get_event_loop()
        coro = bot.send_message(user_id, f"🔔 Напоминание: <b>{title}</b>\nСрок: {when_iso}")
        asyncio.run_coroutine_threadsafe(coro, loop)

    scheduler.add_job(job_send, trigger=trigger, id=job_id, replace_existing=True)


async def reschedule_pending_reminders(scheduler: AsyncIOScheduler, bot):
    pend = get_pending_reminders()
    for t in pend:
        try:
            schedule_reminder(scheduler, bot, t["id"], t["user_id"], t["title"], t["due_datetime"])
        except Exception as e:
            print("Ошибка при реседулинге:", e)


# ---------------------------------------------------------
#  /start
# ---------------------------------------------------------
@router.message(Command("start"))
async def cmd_start(message: Message):
    username = message.from_user.first_name or message.from_user.username
    await message.answer(
        f"👋 Привет, <b>{username}</b>!\n\n"
        "Я — интеллектуальный помощник <b>МойРитм</b>.\n"
        "Используй меню ниже 👇",
        reply_markup=kb.main_menu
    )


# ---------------------------------------------------------
#  МЕНЮ — Мои задачи
# ---------------------------------------------------------
@router.message(F.text == "🧠 Мои задачи")
async def menu_tasks(message: Message):
    await send_clean(message, "📋 Меню задач:", kb.tasks_menu)


# ---------------------------------------------------------
#  ➕ Добавить задачу
# ---------------------------------------------------------
@router.message(F.text == "➕ Добавить задачу")
async def start_add_task(message: Message, state: FSMContext):
    await send_clean(message, "✏️ Введи название задачи:", ReplyKeyboardRemove())
    await state.set_state(AddTaskStates.waiting_title)


@router.message(StateFilter(AddTaskStates.waiting_title))
async def process_title(message: Message, state: FSMContext):
    title = message.text.strip()
    await state.update_data(title=title)
    await message.answer("📅 Введи дату: (пример 12.11.2025)")
    await state.set_state(AddTaskStates.waiting_date)


@router.message(StateFilter(AddTaskStates.waiting_date))
async def process_date(message: Message, state: FSMContext):
    try:
        dt = datetime.strptime(message.text.strip(), "%d.%m.%Y")
        await state.update_data(date=dt.date().isoformat())
        await message.answer("⏰ Теперь введи время (пример 14:30):")
        await state.set_state(AddTaskStates.waiting_time)
    except:
        await message.answer("❌ Неверный формат. Пример: 12.11.2025")


@router.message(StateFilter(AddTaskStates.waiting_time))
async def process_time(message: Message, state: FSMContext):
    try:
        t = datetime.strptime(message.text.strip(), "%H:%M").time()
        data = await state.get_data()
        full = datetime.combine(datetime.fromisoformat(data["date"]), t)
        await state.update_data(due=full.strftime("%Y-%m-%d %H:%M:%S"))
        await message.answer("🔔 Включить напоминание? (Да/Нет)")
        await state.set_state(AddTaskStates.waiting_remind)
    except:
        await message.answer("❌ Неверный формат. Пример: 14:30")


@router.message(StateFilter(AddTaskStates.waiting_remind))
async def process_remind(message: Message, state: FSMContext):
    remind = not message.text.lower().startswith(("н", "no"))
    user_id = message.from_user.id
    data = await state.get_data()

    title = data["title"]
    due = data["due"]

    task_id = add_task(user_id, title, due, remind)

    try:
        import run
        if remind:
            schedule_reminder(run.scheduler, message.bot, task_id, user_id, title, due)
    except:
        pass

    await message.answer(
        f"✅ Задача создана!\n<b>{title}</b>\nСрок: {due}",
        reply_markup=kb.tasks_menu
    )
    await state.clear()


# ---------------------------------------------------------
#  Незавершённые
# ---------------------------------------------------------
@router.message(F.text == "🚧 Незавершённые задачи")
async def active_tasks(message: Message):
    await message.delete()
    tasks = list_tasks(message.from_user.id, only_active=True)
    if not tasks:
        await message.answer("Нет активных задач.", reply_markup=kb.tasks_menu)
        return

    text = "🔎 <b>Незавершённые:</b>\n\n"
    for t in tasks:
        text += f"• <b>{t['id']}</b> — {t['title']} ({t['due_datetime']})\n"

    await message.answer(text, reply_markup=kb.tasks_menu)


# ---------------------------------------------------------
#  Завершённые
# ---------------------------------------------------------
@router.message(F.text == "✅ Завершённые задачи")
async def completed_tasks(message: Message):
    await message.delete()
    tasks = list_tasks(message.from_user.id, only_active=False)
    done = [t for t in tasks if t["completed"]]

    if not done:
        await message.answer("Нет выполненных задач.", reply_markup=kb.tasks_menu)
        return

    text = "📦 <b>Выполненные:</b>\n\n"
    for t in done:
        text += f"• <b>{t['id']}</b> — {t['title']}\n"

    await message.answer(text, reply_markup=kb.tasks_menu)


# ---------------------------------------------------------
#  ✏️ Редактировать задачу
# ---------------------------------------------------------
@router.message(F.text == "✏️ Редактировать задачу")
async def edit_prompt(message: Message, state: FSMContext):
    await send_clean(message, "Введи ID задачи:", ReplyKeyboardRemove())
    await state.set_state(EditTaskStates.waiting_id)


@router.message(StateFilter(EditTaskStates.waiting_id))
async def edit_choose(message: Message, state: FSMContext):
    try:
        task_id = int(message.text)
        task = get_task(task_id)
        if not task or task["user_id"] != message.from_user.id:
            raise ValueError
    except:
        await message.answer("❌ Неверный ID. Попробуй снова.")
        return

    await state.update_data(task_id=task_id)

    await message.answer(
        "Что изменить?\n"
        "1 — Название\n"
        "2 — Дата/время\n"
        "3 — Напоминание",
    )
    await state.set_state(EditTaskStates.choose_field)


@router.message(StateFilter(EditTaskStates.choose_field))
async def edit_field(message: Message, state: FSMContext):
    if message.text == "1":
        await message.answer("Введи новое название:")
        await state.set_state(EditTaskStates.edit_title)
    elif message.text == "2":
        await message.answer("Введи новую дату (12.11.2025):")
        await state.set_state(EditTaskStates.edit_date)
    elif message.text == "3":
        await message.answer("Включить напоминание? (Да/Нет)")
        await state.set_state(EditTaskStates.edit_remind)
    else:
        await message.answer("Напиши 1, 2 или 3.")


@router.message(StateFilter(EditTaskStates.edit_title))
async def edit_title(message: Message, state: FSMContext):
    data = await state.get_data()
    update_task_title(data["task_id"], message.text.strip())

    await message.answer("Название обновлено.", reply_markup=kb.tasks_menu)
    await state.clear()


@router.message(StateFilter(EditTaskStates.edit_date))
async def edit_date(message: Message, state: FSMContext):
    try:
        dt = datetime.strptime(message.text.strip(), "%d.%m.%Y")
        await state.update_data(new_date=dt.date().isoformat())
        await message.answer("Теперь время (14:30):")
        await state.set_state(EditTaskStates.edit_time)
    except:
        await message.answer("Формат неверный. Пример: 12.11.2025")


@router.message(StateFilter(EditTaskStates.edit_time))
async def edit_time(message: Message, state: FSMContext):
    try:
        t = datetime.strptime(message.text.strip(), "%H:%M").time()
        data = await state.get_data()

        dt = datetime.combine(datetime.fromisoformat(data["new_date"]), t)
        due = dt.strftime("%Y-%m-%d %H:%M:%S")

        update_task_datetime(data["task_id"], due)

        task = get_task(data["task_id"])
        if task["remind"]:
            import run
            schedule_reminder(run.scheduler, message.bot, task["id"], task["user_id"], task["title"], due)

        await message.answer("Дата/время обновлены.", reply_markup=kb.tasks_menu)
        await state.clear()

    except:
        await message.answer("Формат неверный. Пример: 14:30")


@router.message(StateFilter(EditTaskStates.edit_remind))
async def edit_remind(message: Message, state: FSMContext):
    enable = not message.text.lower().startswith(("н", "no"))
    data = await state.get_data()
    update_task_remind(data["task_id"], enable)

    task = get_task(data["task_id"])

    if enable:
        import run
        schedule_reminder(run.scheduler, message.bot, task["id"], task["user_id"], task["title"], task["due_datetime"])
    else:
        try:
            import run
            run.scheduler.remove_job(f"reminder_{task['id']}")
        except:
            pass

    await message.answer("Напоминание обновлено.", reply_markup=kb.tasks_menu)
    await state.clear()


# ---------------------------------------------------------
#  🗑 Удаление
# ---------------------------------------------------------
@router.message(F.text == "🗑 Удалить задачу")
async def delete_task_prompt(message: Message, state: FSMContext):
    await send_clean(message, "Введи ID задачи:", ReplyKeyboardRemove())
    await state.set_state("delete_waiting_id")


@router.message(StateFilter("delete_waiting_id"))
async def delete_task_flow(message: Message, state: FSMContext):
    try:
        task_id = int(message.text)
        task = get_task(task_id)
        if not task or task["user_id"] != message.from_user.id:
            raise ValueError
    except:
        await message.answer("Неверный ID, попробуй снова.")
        return

    delete_task(task_id)

    try:
        import run
        run.scheduler.remove_job(f"reminder_{task_id}")
    except:
        pass

    await message.answer("Задача удалена.", reply_markup=kb.tasks_menu)
    await state.clear()


# ---------------------------------------------------------
#  Универсальный fallback
# ---------------------------------------------------------
@router.message()
async def fallback(message: Message):
    await send_clean(message, "💡 Используй меню для управления задачами.", kb.main_menu)
