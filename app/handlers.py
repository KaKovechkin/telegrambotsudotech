from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
from app.ai_agent import ai_answer
from app.db import add_task, list_tasks, delete_task
from app.keyboards import main_menu, ai_exit_kb

router = Router()

# Хранение состояния пользователя
user_context = {}


# ------------------------------------------------------------
# Главное меню
# ------------------------------------------------------------
@router.message(F.text == "/start")
async def start(message: Message):
    await message.answer("👋 Привет! Я — МойРитм, твой персональный планировщик.", reply_markup=main_menu())


@router.message(F.text == "/menu")
async def menu(message: Message):
    await message.answer("Главное меню:", reply_markup=main_menu())

@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu())
    await callback.answer()

# ------------------------------------------------------------
# 📝 МЕНЮ ЗАДАЧ
# ------------------------------------------------------------
def tasks_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить задачу", callback_data="task_add")
    kb.button(text="📋 Список задач", callback_data="task_list")
    kb.button(text="⬅ Назад", callback_data="back_main")
    kb.adjust(1)
    return kb.as_markup()


@router.callback_query(F.data == "tasks")
async def open_tasks(callback: CallbackQuery):
    await callback.message.edit_text("📝 Меню задач:", reply_markup=tasks_keyboard())
    await callback.answer()


# ------------------------------------------------------------
# ➕ ДОБАВЛЕНИЕ ЗАДАЧИ
# ------------------------------------------------------------
@router.callback_query(F.data == "task_add")
async def add_task_title(callback: CallbackQuery):
    user_context[callback.from_user.id] = {"mode": "add_title"}
    await callback.message.edit_text("🆕 Введи название задачи:")
    await callback.answer()


async def ask_date(message: Message):
    user_context[message.from_user.id]["mode"] = "add_date"
    await message.answer("📅 Введи дату (дд/мм/гггг) или напиши «сегодня».")


async def ask_time(message: Message):
    user_context[message.from_user.id]["mode"] = "add_time"
    await message.answer("⏰ Теперь введи время (чч:мм)")


# ------------------------------------------------------------
# 📋 СПИСОК ЗАДАЧ
# ------------------------------------------------------------
@router.callback_query(F.data == "task_list")
async def show_tasks(callback: CallbackQuery):
    tasks = list_tasks(callback.from_user.id)

    if not tasks:
        await callback.message.edit_text("📭 У тебя нет задач.", reply_markup=tasks_keyboard())
        return await callback.answer()

    kb = InlineKeyboardBuilder()
    text = "📋 <b>Твои задачи:</b>\n\n"

    for t in tasks:
        dt = t["due_datetime"]
        text += f"• <b>{t['title']}</b> — <i>{dt}</i>\n"
        kb.button(text=f"❌ {t['id']}", callback_data=f"del:{t['id']}")

    kb.button(text="⬅ Назад", callback_data="tasks")
    kb.adjust(1)

    await callback.message.edit_text(text, reply_markup=kb.as_markup())
    await callback.answer()


# Удаление задачи
@router.callback_query(F.data.startswith("del:"))
async def del_task_handler(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    delete_task(task_id)
    await show_tasks(callback)


# ------------------------------------------------------------
# 📅 ПЛАН ДНЯ
# ------------------------------------------------------------
@router.callback_query(F.data == "day")
async def today_plan(callback: CallbackQuery):
    today = datetime.now().strftime("%Y-%m-%d")
    tasks = list_tasks(callback.from_user.id)

    # ---- Исправленная фильтрация ----
    today_tasks = [
        t for t in tasks
        if t["due_datetime"][:10] == today  # сравниваем только дату YYYY-MM-DD
    ]


    if not today_tasks:
        await callback.message.edit_text("Сегодня задач нет 🙌", reply_markup=main_menu())
        return await callback.answer()

    text = "📅 <b>План на сегодня:</b>\n\n"
    for t in today_tasks:
        dt = t["due_datetime"]
        time = dt.split(" ")[1]
        text += f"• {t['title']} — <i>{time}</i>\n"

    await callback.message.edit_text(text, reply_markup=main_menu())
    await callback.answer()


# ------------------------------------------------------------
# ⏰ НАПОМИНАНИЯ
# ------------------------------------------------------------
@router.callback_query(F.data == "reminders")
async def reminders_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "⏰ Чтобы создать напоминание — просто добавляй задачи с датой и временем.\n"
        "Я сам напомню вовремя!",
        reply_markup=main_menu()
    )
    await callback.answer()


# ------------------------------------------------------------
# 🤖 ИИ ассистент
# ------------------------------------------------------------
@router.callback_query(F.data == "ai")
async def ai_start(callback: CallbackQuery):
    user_context[callback.from_user.id] = {"mode": "ai"}
    await callback.message.edit_text("🧠 Я слушаю. Напиши вопрос.", reply_markup=ai_exit_kb())
    await callback.answer()


@router.callback_query(F.data == "ai_stop")
async def ai_stop(callback: CallbackQuery):
    user_context.pop(callback.from_user.id, None)
    await callback.message.edit_text("👌 Выход выполнен.", reply_markup=main_menu())
    await callback.answer()


# ------------------------------------------------------------
# 🌐 ОСНОВНОЙ ОБРАБОТЧИК ТЕКСТА
# ------------------------------------------------------------
@router.message()
async def text_handler(message: Message):

    user_id = message.from_user.id
    ctx = user_context.get(user_id, {}).get("mode")

    # 1 — Название задачи
    if ctx == "add_title":
        user_context[user_id]["title"] = message.text
        return await ask_date(message)

    # 2 — Дата задачи
    if ctx == "add_date":
        txt = message.text.lower()

        if txt == "сегодня":
            date = datetime.now().strftime("%d/%m/%Y")
        else:
            date = txt

        try:
            datetime.strptime(date, "%d/%m/%Y")
        except:
            return await message.answer("⚠ Формат неверный. Пример: 05/12/2024")

        user_context[user_id]["date"] = date
        return await ask_time(message)

    # 3 — Время задачи
    if ctx == "add_time":
        try:
            datetime.strptime(message.text, "%H:%M")
        except:
            return await message.answer("⚠ Формат времени неверный. Пример: 18:30")

        title = user_context[user_id]["title"]
        date = user_context[user_id]["date"]
        time = message.text

        dt = datetime.strptime(f"{date} {time}", "%d/%m/%Y %H:%M")

        add_task(user_id, title, dt.strftime("%Y-%m-%d %H:%M"))

        user_context.pop(user_id)

        return await message.answer("✔ Задача сохранена!", reply_markup=main_menu())

    # ИИ ассистент
    if ctx == "ai":
        await message.answer("⏳ Думаю…")
        reply = await ai_answer(message.text)
        return await message.answer(reply, reply_markup=ai_exit_kb())

    # По умолчанию
    return await message.answer("Выбери действие в меню:", reply_markup=main_menu())


# ------------------------------------------------------------
# SCHEDULER — напоминания
# ------------------------------------------------------------
async def setup_scheduler(scheduler, bot):
    from app.db import get_pending_reminders

    async def check_reminders():
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        tasks = get_pending_reminders(now)

        for t in tasks:
            try:
                await bot.send_message(t["user_id"], f"🔔 Напоминание:\n<b>{t['title']}</b>")
            except:
                pass

    scheduler.add_job(check_reminders, "interval", seconds=30)
