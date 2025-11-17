
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from datetime import date, datetime, timedelta
import calendar

def build_month(year:int, month:int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=7)
    # Header prev, title, next
    kb.row(
        InlineKeyboardButton("<", callback_data=f"cal:prev:{year}:{month}"),
        InlineKeyboardButton(f"{calendar.month_name[month]} {year}", callback_data="cal:noop"),
        InlineKeyboardButton(">", callback_data=f"cal:next:{year}:{month}")
    )
    # Weekdays
    days = ["Mo","Tu","We","Th","Fr","Sa","Su"]
    kb.row(*[InlineKeyboardButton(d, callback_data="cal:noop") for d in days])

    cal = calendar.Calendar(firstweekday=0)
    for week in cal.monthdayscalendar(year, month):
        row = []
        for d in week:
            if d==0:
                row.append(InlineKeyboardButton(" ", callback_data="cal:noop"))
            else:
                row.append(InlineKeyboardButton(str(d), callback_data=f"cal:day:{year}:{month}:{d}"))
        kb.row(*row)
    kb.row(InlineKeyboardButton("Отмена", callback_data="cal:cancel"))
    return kb

def build_time_picker() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=4)
    # показать часы каждые 1 час (00:00 .. 23:00)
    for h in range(0,24,4):  # показываем по 4 в ряд, но выводим все — будем генерировать per 1
        pass
    # build all hours lines (every hour)
    buttons=[]
    for h in range(0,24):
        txt = f"{h:02d}:00"
        buttons.append(InlineKeyboardButton(txt, callback_data=f"time:hour:{h}"))
    # chunk into rows of 4
    for i in range(0, len(buttons), 4):
        kb.row(*buttons[i:i+4])
    kb.row(InlineKeyboardButton("Отмена", callback_data="time:cancel"))
    return kb
