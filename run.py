import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN
from app import handlers
from app.handlers import router


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )

    dp = Dispatcher()
    dp.include_router(router)

    scheduler = AsyncIOScheduler()
    await handlers.setup_scheduler(scheduler, bot)
    scheduler.start()

    print("Бот запущен!")
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    asyncio.run(main())