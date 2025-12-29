import json
import logging
import asyncio
import re
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest # <--- ВАЖНЫЙ ИМПОРТ ДЛЯ ИСПРАВЛЕНИЯ ОШИБКИ

# Импорты наших модулей
from app.ai_agent import ai_answer
from app.keyboards import main_menu, ai_exit_kb

# Импорты для работы с базой данных
from app.db import (
    add_task, 
    list_tasks, 
    delete_task, 
    get_pending_reminders, 
    get_days_with_tasks,
    get_tasks_for_day,
    mark_task_completed,
    get_stats_data
)

# Импорты для доп. функционала
from app.bot_calendar import build_month
from app.stats import draw_stats_chart

# Инициализация роутера и логирования
router = Router()
logging.basicConfig(level=logging.INFO)

# Хранилище состояния пользователя
user_context = {}

# ==========================================================
# 🛠 СЛУЖЕБНЫЕ ФУНКЦИИ (УТИЛИТЫ)
# ==========================================================

async def safe_delete(bot, chat_id, message_id):
    """
    Безопасное удаление сообщения.
    """
    if not message_id:
        return
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        pass

def update_last_msg(user_id, msg_id):
    """
    Запоминаем ID последнего сообщения бота.
    """
    if user_id not in user_context:
        user_context[user_id] = {}
    user_context[user_id]["last_msg_id"] = msg_id

def get_last_msg(user_id):
    """Получаем ID последнего сообщения"""
    return user_context.get(user_id, {}).get("last_msg_id")

async def nav_edit_or_send(callback: CallbackQuery, text: str, reply_markup):
    """
    ⚡ УМНАЯ НАВИГАЦИЯ (ИСПРАВЛЕНИЕ ОШИБКИ С КАРТИНКОЙ)
    Пытается отредактировать текст. Если это невозможно (например, предыдущее
    сообщение было фото-статистикой), удаляет старое и шлет новое.
    """
    user_id = callback.from_user.id
    try:
        # Пытаемся просто изменить текст (быстро и красиво)
        await callback.message.edit_text(text, reply_markup=reply_markup)
        update_last_msg(user_id, callback.message.message_id)
    except TelegramBadRequest:
        # Опа! Ошибка. Скорее всего мы пытаемся превратить ФОТО в ТЕКСТ.
        # Telegram так не умеет. Значит:
        
        # 1. Удаляем старое сообщение (фото)
        await safe_delete(callback.bot, callback.message.chat.id, callback.message.message_id)
        
        # 2. Отправляем новое чистое сообщение
        sent_msg = await callback.message.answer(text, reply_markup=reply_markup)
        update_last_msg(user_id, sent_msg.message_id)

def parse_json_from_text(text: str):
    try:
        cleaned_text = text.replace("```json", "").replace("```", "").strip()
        start_index = cleaned_text.find("{")
        end_index = cleaned_text.rfind("}")
        
        if start_index != -1 and end_index != -1:
            json_substring = cleaned_text[start_index : end_index + 1]
            return json.loads(json_substring)
    except Exception as e:
        logging.error(f"Ошибка парсинга JSON: {e}")
        return None
    return None

def parse_date_time(date_str, time_str):
    d = str(date_str).replace(".", "/").replace("-", "/").strip()
    t = str(time_str).replace(".", ":").replace("-", ":").strip()
    
    formats = [
        "%d/%m/%Y %H:%M",
        "%Y/%m/%d %H:%M",
        "%d-%m-%Y %H:%M",
        "%d/%m/%y %H:%M",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(f"{d} {t}", fmt)
        except ValueError:
            continue
    return None

# ==========================================================
# 🏠 ГЛАВНОЕ МЕНЮ И НАВИГАЦИЯ
# ==========================================================

@router.message(F.text == "/start")
async def start(message: Message):
    await safe_delete(message.bot, message.chat.id, message.message_id)
    await message.answer(
        "🤖 <b>МойРитм запущен</b>\n"
        "〰〰〰〰〰〰〰〰〰〰\n"
        "<i>(Это системное сообщение, чтобы чат не прыгал)</i>"
    )
    sent_msg = await message.answer(
        "👋 <b>Привет! Я — твой помощник.</b>\nВыбери действие:", 
        reply_markup=main_menu()
    )
    update_last_msg(message.from_user.id, sent_msg.message_id)

@router.message(F.text == "/menu")
async def menu(message: Message):
    sent_msg = await message.answer("Главное меню:", reply_markup=main_menu())
    await safe_delete(message.bot, message.chat.id, message.message_id)
    old_bot_msg_id = get_last_msg(message.from_user.id)
    if old_bot_msg_id:
        await safe_delete(message.bot, message.chat.id, old_bot_msg_id)
    update_last_msg(message.from_user.id, sent_msg.message_id)

@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    # Используем нашу умную функцию, чтобы кнопка "Назад" работала везде
    await nav_edit_or_send(callback, "Главное меню:", main_menu())
    await callback.answer()

# ==========================================================
# 📝 УПРАВЛЕНИЕ ЗАДАЧАМИ (КНОПКИ)
# ==========================================================

def tasks_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить задачу", callback_data="task_add")
    kb.button(text="📋 Список задач", callback_data="task_list")
    kb.button(text="⬅ Назад", callback_data="back_main")
    kb.adjust(1)
    return kb.as_markup()

@router.callback_query(F.data == "tasks")
async def open_tasks(callback: CallbackQuery):
    # Исправлено: используем nav_edit_or_send
    await nav_edit_or_send(
        callback, 
        "📝 <b>Меню задач:</b>\nВыбери действие:", 
        tasks_keyboard()
    )

# --- БЛОК: РУЧНОЕ ДОБАВЛЕНИЕ ЗАДАЧИ ---

@router.callback_query(F.data == "task_add")
async def add_task_title(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_context:
        user_context[user_id] = {}
    user_context[user_id]["mode"] = "add_title"
    
    # Здесь тоже безопасно переходим
    await nav_edit_or_send(callback, "🆕 <b>Шаг 1 из 3:</b>\nНапиши название задачи:", None)

async def ask_date_step(message: Message, last_bot_msg_id):
    user_id = message.from_user.id
    user_context[user_id]["mode"] = "add_date"
    sent_msg = await message.answer("📅 <b>Шаг 2 из 3:</b>\nВведи дату (ДД/ММ/ГГГГ) или напиши «сегодня»:")
    await safe_delete(message.bot, message.chat.id, message.message_id)
    await safe_delete(message.bot, message.chat.id, last_bot_msg_id)
    update_last_msg(user_id, sent_msg.message_id)

async def ask_time_step(message: Message, last_bot_msg_id):
    user_id = message.from_user.id
    user_context[user_id]["mode"] = "add_time"
    sent_msg = await message.answer("⏰ <b>Шаг 3 из 3:</b>\nВведи время (ЧЧ:ММ):")
    await safe_delete(message.bot, message.chat.id, message.message_id)
    await safe_delete(message.bot, message.chat.id, last_bot_msg_id)
    update_last_msg(user_id, sent_msg.message_id)

# --- БЛОК: СПИСОК ЗАДАЧ ---

@router.callback_query(F.data == "task_list")
async def show_tasks(callback: CallbackQuery):
    user_id = callback.from_user.id
    tasks = list_tasks(user_id)
    
    if not tasks:
        await nav_edit_or_send(callback, "📭 <b>Список задач пуст.</b>\nСамое время добавить что-то!", tasks_keyboard())
        return

    kb = InlineKeyboardBuilder()
    text_output = "📋 <b>Ваши активные задачи:</b>\n\n"
    
    for t in tasks:
        text_output += f"🔹 <b>{t['title']}</b>\n🕒 {t['due_datetime']}\n\n"
        kb.button(text="✅", callback_data=f"done:{t['id']}")
        kb.button(text="❌", callback_data=f"del:{t['id']}")
        
    kb.button(text="⬅ Назад", callback_data="tasks")
    # Сетка: по 2 кнопки на задачу, последняя одна
    sizes = [2] * len(tasks) + [1]
    kb.adjust(*sizes)
    
    await nav_edit_or_send(callback, text_output, kb.as_markup())

@router.callback_query(F.data.startswith("del:"))
async def del_task_handler(callback: CallbackQuery):
    try:
        task_id = int(callback.data.split(":")[1])
        delete_task(task_id)
        await show_tasks(callback)
    except Exception as e:
        await callback.answer("Ошибка удаления!", show_alert=True)

@router.callback_query(F.data.startswith("done:"))
async def done_task_handler(callback: CallbackQuery):
    try:
        task_id = int(callback.data.split(":")[1])
        mark_task_completed(task_id)
        await callback.answer("Супер! Задача выполнена 🎉")
        await show_tasks(callback)
    except Exception as e:
        await callback.answer("Ошибка!", show_alert=True)

# ==========================================================
# 📊 СТАТИСТИКА
# ==========================================================

@router.callback_query(F.data == "stats")
async def stats_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    # Удаляем старое сообщение (текст или фото)
    await safe_delete(callback.bot, callback.message.chat.id, callback.message.message_id)
    
    comp, pend, days, counts = get_stats_data(user_id)
    photo_buf = draw_stats_chart(comp, pend, days, counts)
    image_file = BufferedInputFile(photo_buf.read(), filename="stats.png")
    
    sent_msg = await callback.message.answer_photo(
        photo=image_file,
        caption=(
            f"📊 <b>Твоя продуктивность:</b>\n\n"
            f"✅ Выполнено задач: <b>{comp}</b>\n"
            f"🔥 В работе: <b>{pend}</b>\n\n"
            f"<i>Выбери раздел ниже, чтобы продолжить:</i>"
        ),
        reply_markup=main_menu()
    )
    update_last_msg(user_id, sent_msg.message_id)

# ==========================================================
# 📅 КАЛЕНДАРЬ
# ==========================================================

@router.callback_query(F.data == "calendar_open")
async def open_calendar_handler(callback: CallbackQuery):
    now = datetime.now()
    year, month = now.year, now.month
    active_days = get_days_with_tasks(callback.from_user.id, year, month)
    
    # Исправлено: используем безопасный переход
    await nav_edit_or_send(
        callback,
        f"📅 <b>Календарь задач</b>\nВыберите дату:",
        build_month(year, month, active_days)
    )

@router.callback_query(F.data.startswith("cal:"))
async def calendar_action_handler(callback: CallbackQuery):
    parts = callback.data.split(":")
    action = parts[1]
    
    if action == "ignore":
        await callback.answer()
        return

    if action in ["prev", "next"]:
        year = int(parts[2])
        month = int(parts[3])
        
        if action == "prev":
            month -= 1
            if month < 1:
                month = 12
                year -= 1
        elif action == "next":
            month += 1
            if month > 12:
                month = 1
                year += 1
        
        active_days = get_days_with_tasks(callback.from_user.id, year, month)
        # Внутри календаря можно использовать edit, т.к. мы уже в текстовом режиме
        await callback.message.edit_reply_markup(
            reply_markup=build_month(year, month, active_days)
        )
        await callback.answer()

    elif action == "day":
        year = int(parts[2])
        month = int(parts[3])
        day = int(parts[4])
        date_str = f"{year}-{month:02d}-{day:02d}"
        tasks = get_tasks_for_day(callback.from_user.id, date_str)
        
        kb = InlineKeyboardBuilder()
        kb.button(text="⬅ Назад к календарю", callback_data=f"cal:back:{year}:{month}")
        
        if not tasks:
            text_out = f"📅 <b>{day}.{month}.{year}</b>\n\nНет задач на этот день. Отдыхай! 🌴"
        else:
            text_out = f"📅 <b>Задачи на {day}.{month}.{year}:</b>\n\n"
            for t in tasks:
                time_val = t['due_datetime'].split(" ")[1]
                text_out += f"⏰ {time_val} — {t['title']}\n"
        
        await callback.message.edit_text(text_out, reply_markup=kb.as_markup())
        await callback.answer()

    elif action == "back":
        year = int(parts[2])
        month = int(parts[3])
        active_days = get_days_with_tasks(callback.from_user.id, year, month)
        
        await callback.message.edit_text(
            f"📅 <b>Календарь задач</b>\nВыберите дату:",
            reply_markup=build_month(year, month, active_days)
        )

# --- БЛОК: ПЛАН НА СЕГОДНЯ ---

@router.callback_query(F.data == "day")
async def today_plan(callback: CallbackQuery):
    today_str = datetime.now().strftime("%Y-%m-%d")
    tasks = list_tasks(callback.from_user.id)
    today_tasks = [t for t in tasks if t["due_datetime"].startswith(today_str)]
    
    if not today_tasks:
        # Исправлено: nav_edit_or_send
        await nav_edit_or_send(callback, "🌴 <b>На сегодня задач нет!</b>\nМожно отдохнуть.", main_menu())
        return

    text_output = f"📅 <b>План на сегодня ({datetime.now().strftime('%d.%m')}):</b>\n\n"
    for t in today_tasks:
        time_part = t["due_datetime"].split(" ")[1]
        text_output += f"• {time_part} — <b>{t['title']}</b>\n"
        
    await nav_edit_or_send(callback, text_output, main_menu())

@router.callback_query(F.data == "reminders")
async def reminders_menu(callback: CallbackQuery):
    # Исправлено: nav_edit_or_send
    await nav_edit_or_send(
        callback,
        "⏰ <b>Информация о напоминаниях:</b>\n\n"
        "Бот автоматически проверяет ваши задачи каждые 30 секунд. "
        "Если время задачи совпадает с текущим временем, вы получите уведомление.", 
        main_menu()
    )

# ==========================================================
# 🧠 ИНТЕЛЛЕКТУАЛЬНЫЙ АГЕНТ
# ==========================================================

@router.callback_query(F.data == "ai")
async def ai_start(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_context[user_id] = {"mode": "ai"}
    
    # Исправлено: nav_edit_or_send
    await nav_edit_or_send(
        callback,
        "🧠 <b>ИИ-Ассистент активирован.</b>\n\n"
        "Я вижу все ваши задачи и могу управлять ими.\n"
        "<b>Примеры команд:</b>\n"
        "🔸 «Напомни купить хлеб завтра в 10:00»\n"
        "🔸 «Удали задачу про встречу»\n"
        "🔸 «Какие у меня планы на вечер?»\n"
        "🔸 «Спланируй мой день»\n\n"
        "<i>Напишите ваш запрос ниже:</i>", 
        ai_exit_kb()
    )

@router.callback_query(F.data == "ai_stop")
async def ai_stop(callback: CallbackQuery):
    user_context.pop(callback.from_user.id, None)
    await nav_edit_or_send(callback, "👌 ИИ режим выключен. Возврат в меню.", main_menu())

# ==========================================================
# 📨 ОБРАБОТЧИК ТЕКСТА
# ==========================================================

@router.message()
async def text_handler(message: Message):
    user_id = message.from_user.id
    ctx_data = user_context.get(user_id, {})
    mode = ctx_data.get("mode")
    last_bot_msg_id = ctx_data.get("last_msg_id")

    # --- СЦЕНАРИЙ 1: РУЧНОЙ ВВОД ЗАДАЧИ ---
    if mode == "add_title":
        user_context[user_id]["title"] = message.text
        return await ask_date_step(message, last_bot_msg_id)

    if mode == "add_date":
        raw_date = message.text.lower().strip()
        if raw_date == "сегодня":
            final_date_str = datetime.now().strftime("%d/%m/%Y")
        else:
            final_date_str = raw_date
        
        if len(final_date_str) < 5:
            sent_msg = await message.answer("⚠ Дата слишком короткая. Попробуй формат ДД/ММ/ГГГГ")
            await safe_delete(message.bot, message.chat.id, message.message_id)
            if last_bot_msg_id: await safe_delete(message.bot, message.chat.id, last_bot_msg_id)
            update_last_msg(user_id, sent_msg.message_id)
            return

        user_context[user_id]["date"] = final_date_str
        return await ask_time_step(message, last_bot_msg_id)

    if mode == "add_time":
        raw_time = message.text.strip()
        dt_obj = parse_date_time(user_context[user_id]["date"], raw_time)
        
        if dt_obj is None:
            sent_msg = await message.answer("⚠ Неверный формат времени. Используй ЧЧ:ММ.")
            await safe_delete(message.bot, message.chat.id, message.message_id)
            if last_bot_msg_id: await safe_delete(message.bot, message.chat.id, last_bot_msg_id)
            update_last_msg(user_id, sent_msg.message_id)
            return
        
        db_datetime_str = dt_obj.strftime("%Y-%m-%d %H:%M")
        task_title = user_context[user_id]["title"]
        add_task(user_id, task_title, db_datetime_str)
        user_context[user_id]["mode"] = None
        
        sent_msg = await message.answer(f"✅ <b>Отлично!</b>\nЗадача «{task_title}» сохранена.", reply_markup=main_menu())
        await safe_delete(message.bot, message.chat.id, message.message_id)
        if last_bot_msg_id: await safe_delete(message.bot, message.chat.id, last_bot_msg_id)
        update_last_msg(user_id, sent_msg.message_id)
        return

    # --- СЦЕНАРИЙ 2: ИИ АССИСТЕНТ ---
    if mode == "ai":
        wait_msg = await message.answer("⏳ <i>Анализирую запрос...</i>")
        await safe_delete(message.bot, message.chat.id, message.message_id)
        if last_bot_msg_id: await safe_delete(message.bot, message.chat.id, last_bot_msg_id)

        raw_tasks = list_tasks(user_id)
        if raw_tasks:
            tasks_context_str = "\n".join([f"- {t['title']} ({t['due_datetime']})" for t in raw_tasks])
        else:
            tasks_context_str = "Список задач пуст."

        ai_response_text = await ai_answer(message.text, tasks_context=tasks_context_str)
        json_data = parse_json_from_text(ai_response_text)
        await safe_delete(message.bot, message.chat.id, wait_msg.message_id)

        if json_data and "action" in json_data:
            action = json_data.get("action")
            
            if action == "create_task":
                t_title = json_data.get("title", "Задача")
                dt_obj = parse_date_time(json_data.get("date"), json_data.get("time"))
                if dt_obj:
                    db_str = dt_obj.strftime("%Y-%m-%d %H:%M")
                    add_task(user_id, t_title, db_str)
                    final_msg = await message.answer(f"✅ <b>Задача создана!</b>\n\n🎯 {t_title}\n📅 {db_str}", reply_markup=ai_exit_kb())
                else:
                    final_msg = await message.answer(f"⚠ Ошибка в дате от ИИ.", reply_markup=ai_exit_kb())
                update_last_msg(user_id, final_msg.message_id)
                return

            elif action == "delete_task":
                keywords = json_data.get("keywords", "").lower()
                to_delete = [t for t in raw_tasks if keywords in t['title'].lower()]
                if not to_delete:
                    final_msg = await message.answer(f"🤷‍♂️ Не нашел задач с «{keywords}».", reply_markup=ai_exit_kb())
                else:
                    for t in to_delete: delete_task(t['id'])
                    final_msg = await message.answer(f"🗑 <b>Удалено задач: {len(to_delete)}</b>", reply_markup=ai_exit_kb())
                update_last_msg(user_id, final_msg.message_id)
                return

        final_msg = await message.answer(ai_response_text, reply_markup=ai_exit_kb())
        update_last_msg(user_id, final_msg.message_id)
        return

    # --- СЦЕНАРИЙ 3: МУСОР ---
    sent_msg = await message.answer("🤔 Я не понял. Выбери действие в меню:", reply_markup=main_menu())
    await safe_delete(message.bot, message.chat.id, message.message_id)
    if last_bot_msg_id: await safe_delete(message.bot, message.chat.id, last_bot_msg_id)
    update_last_msg(user_id, sent_msg.message_id)

# ==========================================================
# ⏰ ПЛАНИРОВЩИК ЗАДАЧ
# ==========================================================

async def setup_scheduler(scheduler, bot):
    async def check_reminders():
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        tasks = get_pending_reminders(now_str)
        for t in tasks:
            try:
                await bot.send_message(chat_id=t["user_id"], text=f"🔔 <b>НАПОМИНАНИЕ!</b>\n\nНе забудь: {t['title']}")
            except Exception:
                pass
    scheduler.add_job(check_reminders, "interval", seconds=30)