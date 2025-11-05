from gc import callbacks

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton



main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Корзина'),
     KeyboardButton(text='Каталог')],
    [KeyboardButton(text='Контакты')]
],
    resize_keyboard = True,#Делает нормальные кнопки
    input_field_placeholder='Выберите пункт ниже') #Заменяет текст в поле набора текста

inline_main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Каталог', callback_data='catalog')],
    [InlineKeyboardButton(text='Telegram', callback_data='cart')]
])


catalog = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Корзина', callback_data='basket')],
    [InlineKeyboardButton(text='Каталог', callback_data='catalog')],
    [InlineKeyboardButton(text='Контакты', callback_data='contacts')]
])