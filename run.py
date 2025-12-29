import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Импорты проекта
from config import BOT_TOKEN
from app.handlers import router, setup_scheduler
from app.db import init_db

# Логирование
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

async def main():
    # 1. Инициализация Базы Данных
    init_db()
    
    # 2. Создаем объекты бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # 3. Регистрируем роутеры (обработчики)
    dp.include_router(router)
    
    # 4. Настраиваем планировщик (Scheduler)
    scheduler = AsyncIOScheduler()
    await setup_scheduler(scheduler, bot)
    scheduler.start()

    # 5. Запускаем бота
    try:
        logging.info("🚀 Бот запущен в Нативном режиме (без серверов)!")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка при запуске: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")