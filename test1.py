import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.enums import ChatAction

# Импортируем роутер (убедитесь, что файл handlers.py существует)
from app.handlers import router

dp = Dispatcher()


async def main():
    load_dotenv()
    token = os.getenv('TG_TOKEN')

    if not token:
        print("Ошибка: TG_TOKEN не найден в переменных окружения")
        return

    bot = Bot(token=token)

    # Подключаем роутеры
    dp.include_router(router)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Бот запущен успешно!")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')
