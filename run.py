import os
from aiogram.types import Message

import aiogram
from aiogram import Bot, Dispatcher , F
import asyncio

from aiogram.filters import Command
from app.handlers import router

from dotenv import load_dotenv
from aiogram.filters import CommandStart


dp = Dispatcher()




async def main():
    load_dotenv()
    bot = Bot(os.getenv('TG_TOKEN'))
    dp.include_router(router)
    await dp.start_polling(bot)
    
    
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

    
    