from aiogram import Router, F
from aiogram.types import Message,ReplyKeyboardRemove, CallbackQuery#Убирает Клавиатуру с кнопками
from aiogram.filters import Command
from pyexpat.errors import messages

import app.keyboards as kb

router = Router()

# Пример обработчиков в отдельном файле
@router.message(Command("test"))
async def cmd_test(message: Message):
    await message.answer("Тестовая команда из handlers.py",reply_markup=kb.inline_main)

@router.message(F.text == "привет")
async def hello(message: Message):
    await message.answer("И тебе привет!", reply_markup=kb.inline_main)

@router.message(F.text)
async def echo(message: Message):
    await message.answer(f"Вы сказали: {message.text}")

@router.callback_query(F.data=='catalog')
async def catalog(callback: CallbackQuery):
    await callback.answer('Это высплывающее окно')
    await callback.message.edit_text('Выберите категорию',reply_markup=kb.catalog)
