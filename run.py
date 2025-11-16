import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from app.handlers import router, reschedule_pending_reminders
from app.db import init_db
from apscheduler.schedulers.asyncio import AsyncIOScheduler

async def main():
    from config import BOT_TOKEN as token

    # ИНИЦИАЛИЗАЦИЯ БАЗЫ — ОБЯЗАТЕЛЬНО!
    init_db()

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode="HTML")
    )

    dp = Dispatcher()

    global scheduler
    scheduler = AsyncIOScheduler()
    scheduler.start()

    await reschedule_pending_reminders(scheduler, bot)
    dp.include_router(router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
