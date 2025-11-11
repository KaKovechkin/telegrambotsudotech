import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.enums import ChatAction
import app.keyboards as kb

router = Router()


# --- /start ---
@router.message(Command("start"))
async def cmd_start(message: Message):
    user = message.from_user.first_name or message.from_user.username
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    await asyncio.sleep(1.5)
    await message.answer(
        f"👋 Привет, *{user}!* Я — твой интеллектуальный помощник *МойРитм*.\n\n"
        "Помогу тебе спланировать день, составить задачи и ничего не забыть 🧠✨",
        reply_markup=kb.main_menu,
        parse_mode="Markdown"
    )


# --- Главное меню ---
@router.message(F.text == "📅 План дня")
async def plan_day(message: Message):
    await message.delete()
    await message.answer(
        "🗓 Раздел *План дня*.\n\n"
        "Здесь ты сможешь добавлять и просматривать задачи, отмечать выполненные ✅",
        reply_markup=kb.plan_menu,
        parse_mode="Markdown"
    )


@router.message(F.text == "⏰ Напоминания")
async def reminders(message: Message):
    await message.delete()
    await message.answer(
        "🔔 Раздел *Напоминания*.\n\n"
        "Создавай, управляй и удаляй напоминания, чтобы ничего не забывать 💡",
        reply_markup=kb.reminder_menu,
        parse_mode="Markdown"
    )


@router.message(F.text == "🧠 Мои задачи")
async def my_tasks(message: Message):
    await message.delete()
    await message.answer(
        "📋 Раздел *Мои задачи*.\n\n"
        "Здесь ты можешь просматривать и редактировать все активные задачи.",
        reply_markup=kb.tasks_menu,
        parse_mode="Markdown"
    )


@router.message(F.text == "⚙️ Настройки")
async def settings(message: Message):
    await message.delete()
    await message.answer(
        "⚙️ Раздел *Настройки*.\n\n"
        "Здесь ты можешь изменить имя, уведомления и другие параметры.",
        reply_markup=kb.settings_menu,
        parse_mode="Markdown"
    )


@router.message(F.text == "🤖 ИИ агент")
async def ai_agent(message: Message):
    await message.delete()
    await message.answer(
        "🤖 Раздел *ИИ-агент*.\n\n"
        "Я могу помочь тебе спланировать день, оптимизировать задачи и подсказать команды 💬",
        reply_markup=kb.ai_menu,
        parse_mode="Markdown"
    )


# --- ИИ Агент подменю ---
@router.message(F.text == "✨ Сгенерировать день")
async def generate_day(message: Message):
    await message.delete()
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    await asyncio.sleep(2)
    await message.answer(
        "🧩 Вот пример твоего идеального дня:\n\n"
        "🌅 07:30 — Подъём и зарядка\n"
        "🍳 08:00 — Завтрак\n"
        "📚 09:00 — Учёба / Работа над проектом\n"
        "☕ 13:00 — Обед и отдых\n"
        "💻 14:00 — Планирование / Разработка / Задачи\n"
        "🚶 18:00 — Прогулка\n"
        "🌙 22:30 — Подготовка ко сну\n\n"
        "💡 Всё сбалансировано: работа, отдых и личное время.",
        reply_markup=kb.ai_menu
    )


@router.message(F.text == "⚡ Оптимизировать")
async def optimize_day(message: Message):
    await message.delete()
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    await asyncio.sleep(2)
    await message.answer(
        "⚙️ Оптимизация расписания завершена!\n\n"
        "✅ Перераспределил задачи для большей эффективности.\n"
        "📈 Добавил перерывы для восстановления фокуса.\n"
        "✨ Теперь твой день станет ещё продуктивнее!",
        reply_markup=kb.ai_menu
    )


@router.message(F.text == "❓ Помощь")
async def help_menu(message: Message):
    await message.delete()
    await message.answer(
        "🆘 *Помощь по командам:*\n\n"
        "• /start — перезапуск бота\n"
        "• 📅 План дня — работа с ежедневными задачами\n"
        "• ⏰ Напоминания — управление напоминаниями\n"
        "• 🧠 Мои задачи — просмотр и редактирование\n"
        "• 🤖 ИИ агент — помощь в планировании\n"
        "• ⚙️ Настройки — персонализация профиля\n\n"
        "💬 Просто нажми нужную кнопку, чтобы перейти.",
        reply_markup=kb.ai_menu,
        parse_mode="Markdown"
    )


# --- Возврат в главное меню ---
@router.message(F.text == "⬅️ Назад")
async def back_to_main(message: Message):
    await message.delete()
    await message.answer("🔙 Возврат в главное меню", reply_markup=kb.main_menu)


# --- Эхо (если написал что-то другое) ---
@router.message(F.text)
async def echo(message: Message):
    await message.delete()
    await message.answer("💡 Используй кнопки меню ниже, чтобы управлять ботом 👇", reply_markup=kb.main_menu)
