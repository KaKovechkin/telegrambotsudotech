import json
import logging
import asyncio
import re
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

# Импорты наших модулей
from app.ai_agent import ai_answer
from app.db import add_task, list_tasks, delete_task, get_pending_reminders
from app.keyboards import main_menu, ai_exit_kb

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
    Если сообщение уже удалено или слишком старое, бот не упадет с ошибкой.
    """
    if not message_id:
        return
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        # Логируем ошибку, но не останавливаем бота
        pass

def update_last_msg(user_id, msg_id):
    """
    Запоминаем ID последнего сообщения бота, чтобы потом его стереть
    и не захламлять чат.
    """
    if user_id not in user_context:
        user_context[user_id] = {}
    user_context[user_id]["last_msg_id"] = msg_id

def get_last_msg(user_id):
    """Получаем ID последнего сообщения"""
    return user_context.get(user_id, {}).get("last_msg_id")

def parse_json_from_text(text: str):
    """
    Ищет JSON-объект внутри текста, даже если ИИ написал вступление.
    Например: "Конечно! Вот команда: {"action":...}" -> вернет словарь.
    """
    try:
        # 1. Убираем возможную разметку Markdown
        cleaned_text = text.replace("```json", "").replace("```", "").strip()
        
        # 2. Ищем границы JSON-объекта (первую { и последнюю })
        start_index = cleaned_text.find("{")
        end_index = cleaned_text.rfind("}")
        
        if start_index != -1 and end_index != -1:
            # Вырезаем строку
            json_substring = cleaned_text[start_index : end_index + 1]
            # Пытаемся превратить строку в словарь
            return json.loads(json_substring)
            
    except Exception as e:
        logging.error(f"Ошибка парсинга JSON: {e}")
        return None
    
    return None

def parse_date_time(date_str, time_str):
    """
    Пытается распознать дату и время в разных форматах.
    Устойчив к точкам, тире и слешам.
    """
    # Унификация разделителей
    d = str(date_str).replace(".", "/").replace("-", "/").strip()
    t = str(time_str).replace(".", ":").replace("-", ":").strip()
    
    # Список поддерживаемых форматов
    formats = [
        "%d/%m/%Y %H:%M",  # 27/12/2025 18:00
        "%Y/%m/%d %H:%M",  # 2025/12/27 18:00
        "%d-%m-%Y %H:%M",  # 27-12-2025 18:00
        "%d/%m/%y %H:%M",  # 27/12/25 18:00
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
    # 1. Удаляем команду /start от юзера (для чистоты)
    await safe_delete(message.bot, message.chat.id, message.message_id)

    # 2. ОТПРАВЛЯЕМ "ЯКОРЬ" (НЕСГОРАЕМОЕ СООБЩЕНИЕ)
    # Это сообщение мы никогда не будем удалять. 
    # Благодаря ему чат никогда не будет пустым, и кнопка "Start" не вылезет.
    await message.answer(
        "🤖 <b>МойРитм запущен</b>\n"
        "〰〰〰〰〰〰〰〰〰〰\n"
        "<i>(Это системное сообщение, чтобы чат не прыгал)</i>"
    )
    
    # 3. Отправляем сменное меню
    sent_msg = await message.answer(
        "👋 <b>Привет! Я — твой помощник.</b>\nВыбери действие:", 
        reply_markup=main_menu()
    )
    
    # 4. Запоминаем ID меню (вот его мы будем удалять и менять)
    update_last_msg(message.from_user.id, sent_msg.message_id)


@router.message(F.text == "/menu")
async def menu(message: Message):
    # 1. Сначала отправляем новое меню
    sent_msg = await message.answer("Главное меню:", reply_markup=main_menu())
    
    # 2. Удаляем команду пользователя
    await safe_delete(message.bot, message.chat.id, message.message_id)
    
    # 3. Удаляем СТАРОЕ меню (если оно было)
    old_bot_msg_id = get_last_msg(message.from_user.id)
    if old_bot_msg_id:
        await safe_delete(message.bot, message.chat.id, old_bot_msg_id)
        
    # 4. Запоминаем ID нового меню
    update_last_msg(message.from_user.id, sent_msg.message_id)


@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    # При нажатии кнопки "Назад" мы просто редактируем текст.
    # Это не вызывает мигания клавиатуры.
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu())
    await callback.answer()
    update_last_msg(callback.from_user.id, callback.message.message_id)

# ==========================================================
# 📝 УПРАВЛЕНИЕ ЗАДАЧАМИ (КНОПКИ)
# ==========================================================

def tasks_keyboard():
    """Генерация клавиатуры для раздела задач"""
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить задачу", callback_data="task_add")
    kb.button(text="📋 Список задач", callback_data="task_list")
    kb.button(text="⬅ Назад", callback_data="back_main")
    kb.adjust(1)
    return kb.as_markup()

@router.callback_query(F.data == "tasks")
async def open_tasks(callback: CallbackQuery):
    await callback.message.edit_text("📝 <b>Меню задач:</b>\nВыбери действие:", reply_markup=tasks_keyboard())
    update_last_msg(callback.from_user.id, callback.message.message_id)

# --- БЛОК: РУЧНОЕ ДОБАВЛЕНИЕ ЗАДАЧИ ---

@router.callback_query(F.data == "task_add")
async def add_task_title(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    # Инициализируем память для пользователя
    if user_id not in user_context:
        user_context[user_id] = {}
    
    # Устанавливаем режим "Ожидание названия"
    user_context[user_id]["mode"] = "add_title"
    
    # Редактируем сообщение (так красивее)
    await callback.message.edit_text("🆕 <b>Шаг 1 из 3:</b>\nНапиши название задачи:")
    update_last_msg(user_id, callback.message.message_id)

async def ask_date_step(message: Message, last_bot_msg_id):
    """Переход к шагу ввода даты"""
    user_id = message.from_user.id
    user_context[user_id]["mode"] = "add_date"
    
    # 1. Отправляем вопрос
    sent_msg = await message.answer("📅 <b>Шаг 2 из 3:</b>\nВведи дату (ДД/ММ/ГГГГ) или напиши «сегодня»:")
    
    # 2. Удаляем ответ пользователя (название задачи)
    await safe_delete(message.bot, message.chat.id, message.message_id)
    
    # 3. Удаляем предыдущий вопрос бота ("Введи название")
    await safe_delete(message.bot, message.chat.id, last_bot_msg_id)
    
    update_last_msg(user_id, sent_msg.message_id)

async def ask_time_step(message: Message, last_bot_msg_id):
    """Переход к шагу ввода времени"""
    user_id = message.from_user.id
    user_context[user_id]["mode"] = "add_time"
    
    # 1. Отправляем вопрос
    sent_msg = await message.answer("⏰ <b>Шаг 3 из 3:</b>\nВведи время (ЧЧ:ММ):")
    
    # 2. Удаляем ответ пользователя (дата)
    await safe_delete(message.bot, message.chat.id, message.message_id)
    
    # 3. Удаляем предыдущий вопрос бота
    await safe_delete(message.bot, message.chat.id, last_bot_msg_id)
    
    update_last_msg(user_id, sent_msg.message_id)

# --- БЛОК: СПИСОК ЗАДАЧ И УДАЛЕНИЕ ---

@router.callback_query(F.data == "task_list")
async def show_tasks(callback: CallbackQuery):
    user_id = callback.from_user.id
    tasks = list_tasks(user_id)
    
    if not tasks:
        await callback.message.edit_text("📭 <b>Список задач пуст.</b>\nСамое время добавить что-то!", reply_markup=tasks_keyboard())
        return

    kb = InlineKeyboardBuilder()
    text_output = "📋 <b>Ваши активные задачи:</b>\n\n"
    
    for t in tasks:
        # Формируем красивый вывод
        text_output += f"🔹 <b>{t['title']}</b>\n🕒 {t['due_datetime']}\n\n"
        # Кнопка удаления привязана к ID задачи
        kb.button(text=f"❌ Удалить «{t['title'][:10]}...»", callback_data=f"del:{t['id']}")
        
    kb.button(text="⬅ Назад", callback_data="tasks")
    kb.adjust(1)
    
    await callback.message.edit_text(text_output, reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith("del:"))
async def del_task_handler(callback: CallbackQuery):
    try:
        # Извлекаем ID из callback_data
        task_id = int(callback.data.split(":")[1])
        delete_task(task_id)
        
        # Обновляем список задач (рекурсивно вызываем функцию просмотра)
        await show_tasks(callback)
    except Exception as e:
        logging.error(f"Ошибка при удалении задачи: {e}")
        await callback.answer("Ошибка удаления!", show_alert=True)

# --- БЛОК: ПЛАН НА СЕГОДНЯ ---

@router.callback_query(F.data == "day")
async def today_plan(callback: CallbackQuery):
    today_str = datetime.now().strftime("%Y-%m-%d")
    tasks = list_tasks(callback.from_user.id)
    
    # Фильтруем задачи на Python-уровне
    today_tasks = [t for t in tasks if t["due_datetime"].startswith(today_str)]
    
    if not today_tasks:
        await callback.message.edit_text("🌴 <b>На сегодня задач нет!</b>\nМожно отдохнуть.", reply_markup=main_menu())
        return

    text_output = f"📅 <b>План на сегодня ({datetime.now().strftime('%d.%m')}):</b>\n\n"
    for t in today_tasks:
        time_part = t["due_datetime"].split(" ")[1]
        text_output += f"• {time_part} — <b>{t['title']}</b>\n"
        
    await callback.message.edit_text(text_output, reply_markup=main_menu())

@router.callback_query(F.data == "reminders")
async def reminders_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "⏰ <b>Информация о напоминаниях:</b>\n\n"
        "Бот автоматически проверяет ваши задачи каждые 30 секунд. "
        "Если время задачи совпадает с текущим временем, вы получите уведомление.\n\n"
        "<i>Ничего настраивать дополнительно не нужно!</i>", 
        reply_markup=main_menu()
    )

# ==========================================================
# 🧠 ИНТЕЛЛЕКТУАЛЬНЫЙ АГЕНТ (ИИ РЕЖИМ)
# ==========================================================

@router.callback_query(F.data == "ai")
async def ai_start(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_context[user_id] = {"mode": "ai"}
    
    await callback.message.edit_text(
        "🧠 <b>ИИ-Ассистент активирован.</b>\n\n"
        "Я вижу все ваши задачи и могу управлять ими.\n"
        "<b>Примеры команд:</b>\n"
        "🔸 «Напомни купить хлеб завтра в 10:00»\n"
        "🔸 «Удали задачу про встречу»\n"
        "🔸 «Какие у меня планы на вечер?»\n"
        "🔸 «Спланируй мой день»\n\n"
        "<i>Напишите ваш запрос ниже:</i>", 
        reply_markup=ai_exit_kb()
    )
    update_last_msg(user_id, callback.message.message_id)

@router.callback_query(F.data == "ai_stop")
async def ai_stop(callback: CallbackQuery):
    # Очищаем контекст и выходим в меню
    user_context.pop(callback.from_user.id, None)
    await callback.message.edit_text("👌 ИИ режим выключен. Возврат в меню.", reply_markup=main_menu())
    update_last_msg(callback.from_user.id, callback.message.message_id)

# ==========================================================
# 📨 ОБРАБОТЧИК ТЕКСТА (ЗДЕСЬ ВСЯ МАГИЯ)
# ==========================================================

@router.message()
async def text_handler(message: Message):
    user_id = message.from_user.id
    
    # Получаем данные из контекста (режим, ID прошлого сообщения)
    ctx_data = user_context.get(user_id, {})
    mode = ctx_data.get("mode")
    last_bot_msg_id = ctx_data.get("last_msg_id")

    # --- СЦЕНАРИЙ 1: РУЧНОЙ ВВОД ЗАДАЧИ ---
    
    # 1.1 Ввод названия
    if mode == "add_title":
        user_context[user_id]["title"] = message.text
        # Переходим к следующему шагу
        return await ask_date_step(message, last_bot_msg_id)

    # 1.2 Ввод даты
    if mode == "add_date":
        raw_date = message.text.lower().strip()
        
        # Обработка слова "сегодня"
        if raw_date == "сегодня":
            final_date_str = datetime.now().strftime("%d/%m/%Y")
        else:
            final_date_str = raw_date
        
        # Проверка длины (минимальная защита от мусора)
        if len(final_date_str) < 5:
            sent_msg = await message.answer("⚠ Дата слишком короткая. Попробуй формат ДД/ММ/ГГГГ")
            await safe_delete(message.bot, message.chat.id, message.message_id)
            if last_bot_msg_id: await safe_delete(message.bot, message.chat.id, last_bot_msg_id)
            update_last_msg(user_id, sent_msg.message_id)
            return

        user_context[user_id]["date"] = final_date_str
        # Переходим к вводу времени
        return await ask_time_step(message, last_bot_msg_id)

    # 1.3 Ввод времени и сохранение
    if mode == "add_time":
        raw_time = message.text.strip()
        
        # Пытаемся собрать полную дату и время
        dt_obj = parse_date_time(user_context[user_id]["date"], raw_time)
        
        if dt_obj is None:
            sent_msg = await message.answer("⚠ Неверный формат времени. Используй ЧЧ:ММ (например 18:30).")
            await safe_delete(message.bot, message.chat.id, message.message_id)
            if last_bot_msg_id: await safe_delete(message.bot, message.chat.id, last_bot_msg_id)
            update_last_msg(user_id, sent_msg.message_id)
            return
        
        # Форматируем для базы данных
        db_datetime_str = dt_obj.strftime("%Y-%m-%d %H:%M")
        task_title = user_context[user_id]["title"]
        
        # Сохраняем в БД
        add_task(user_id, task_title, db_datetime_str)
        
        # Сбрасываем режим
        user_context[user_id]["mode"] = None
        
        # Отправляем подтверждение
        sent_msg = await message.answer(f"✅ <b>Отлично!</b>\nЗадача «{task_title}» сохранена.", reply_markup=main_menu())
        
        # Чистим чат
        await safe_delete(message.bot, message.chat.id, message.message_id)
        if last_bot_msg_id: await safe_delete(message.bot, message.chat.id, last_bot_msg_id)
        
        update_last_msg(user_id, sent_msg.message_id)
        return

    # --- СЦЕНАРИЙ 2: ИИ АССИСТЕНТ (БЕЗ "ПУСТОГО ЧАТА") ---
    
    if mode == "ai":
        # 1. Отправляем сообщение-якорь "Думаю..."
        wait_msg = await message.answer("⏳ <i>Анализирую запрос...</i>")
        
        # 2. Удаляем сообщение пользователя (теперь это безопасно, чат не пустой)
        await safe_delete(message.bot, message.chat.id, message.message_id)
        
        # 3. Удаляем предыдущий ответ бота (если был)
        if last_bot_msg_id:
            await safe_delete(message.bot, message.chat.id, last_bot_msg_id)

        # 4. Получаем список задач для контекста ИИ
        raw_tasks = list_tasks(user_id)
        if raw_tasks:
            tasks_context_str = "\n".join([f"- {t['title']} ({t['due_datetime']})" for t in raw_tasks])
        else:
            tasks_context_str = "Список задач пуст."

        # 5. Делаем запрос к нейросети
        ai_response_text = await ai_answer(message.text, tasks_context=tasks_context_str)
        
        # 6. Пытаемся найти JSON-команду внутри ответа
        json_data = parse_json_from_text(ai_response_text)

        # Удаляем сообщение "Анализирую..." перед финальным ответом
        await safe_delete(message.bot, message.chat.id, wait_msg.message_id)

        # Обработка JSON
        if json_data and "action" in json_data:
            action = json_data.get("action")
            
            # ВАРИАНТ А: СОЗДАНИЕ ЗАДАЧИ
            if action == "create_task":
                t_title = json_data.get("title", "Задача")
                t_date = json_data.get("date")
                t_time = json_data.get("time")
                
                # Парсим дату от ИИ
                dt_obj = parse_date_time(t_date, t_time)
                
                if dt_obj:
                    db_str = dt_obj.strftime("%Y-%m-%d %H:%M")
                    add_task(user_id, t_title, db_str)
                    
                    final_msg = await message.answer(
                        f"✅ <b>Задача создана!</b>\n\n🎯 {t_title}\n📅 {t_date} в {t_time}", 
                        reply_markup=ai_exit_kb()
                    )
                else:
                    final_msg = await message.answer(
                        f"⚠ ИИ прислал некорректную дату: {t_date} {t_time}. Попробуй переформулировать.",
                        reply_markup=ai_exit_kb()
                    )
                
                update_last_msg(user_id, final_msg.message_id)
                return

            # ВАРИАНТ Б: УДАЛЕНИЕ ЗАДАЧИ
            elif action == "delete_task":
                keywords = json_data.get("keywords", "").lower()
                
                to_delete = []
                for t in raw_tasks:
                    if keywords in t['title'].lower():
                        to_delete.append(t)
                
                if not to_delete:
                    final_msg = await message.answer(
                        f"🤷‍♂️ Я не нашел задач, содержащих: «{keywords}».", 
                        reply_markup=ai_exit_kb()
                    )
                else:
                    for t in to_delete:
                        delete_task(t['id'])
                    final_msg = await message.answer(
                        f"🗑 <b>Удалено задач: {len(to_delete)}</b>\n(По запросу «{keywords}»)", 
                        reply_markup=ai_exit_kb()
                    )
                
                update_last_msg(user_id, final_msg.message_id)
                return

        # ВАРИАНТ В: ПРОСТОЙ ТЕКСТОВЫЙ ОТВЕТ (Если JSON не найден)
        final_msg = await message.answer(ai_response_text, reply_markup=ai_exit_kb())
        update_last_msg(user_id, final_msg.message_id)
        return

    # --- СЦЕНАРИЙ 3: НЕПОНЯТНОЕ СООБЩЕНИЕ (МУСОР) ---
    
    # Если пользователь пишет что-то, не выбрав режим меню
    sent_msg = await message.answer("🤔 Я не понял. Пожалуйста, выбери действие в меню:", reply_markup=main_menu())
    
    await safe_delete(message.bot, message.chat.id, message.message_id)
    if last_bot_msg_id:
        await safe_delete(message.bot, message.chat.id, last_bot_msg_id)
        
    update_last_msg(user_id, sent_msg.message_id)


# ==========================================================
# ⏰ ПЛАНИРОВЩИК ЗАДАЧ (SCHEDULER)
# ==========================================================

async def setup_scheduler(scheduler, bot):
    """
    Фоновая задача, которая проверяет БД каждые 30 секунд
    и отправляет напоминания.
    """
    async def check_reminders():
        # Текущее время до минут
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Получаем список задач, время которых пришло
        tasks = get_pending_reminders(now_str)
        
        for t in tasks:
            try:
                # Отправляем уведомление пользователю
                await bot.send_message(
                    chat_id=t["user_id"], 
                    text=f"🔔 <b>НАПОМИНАНИЕ!</b>\n\nНе забудь: {t['title']}"
                )
                logging.info(f"Напоминание отправлено пользователю {t['user_id']}")
            except Exception as e:
                logging.error(f"Не удалось отправить напоминание: {e}")

    # Добавляем задачу в планировщик
    scheduler.add_job(check_reminders, "interval", seconds=30)