import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.enums import ChatAction

# Импортируем роутер (убедитесь, что файл handlers.py существует)
from app.handlers import router

dp = Dispatcher()


# Добавляем базовые обработчики в основном файле на всякий случай
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.bot.send_chat_action(chat_id = message.from_user.id ,
                                       action=ChatAction.TYPING)
    await asyncio.sleep(2)
    await message.answer("Привет! Бот запущен и работает.")


@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("Доступные команды: /start, /help")


async def main():
    load_dotenv()
    token = os.getenv('TG_TOKEN')

    if not token:
        print("Ошибка: TG_TOKEN не найден в переменных окружения")
        return

    bot = Bot(token=token)

    # Включаем роутер из handlers.py
    dp.include_router(router)

    try:
        # Закрываем предыдущие сессии чтобы избежать конфликтов
        await bot.delete_webhook(drop_pending_updates=True)
        print("Бот запущен успешно!")
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