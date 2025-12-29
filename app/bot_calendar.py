import calendar
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def build_month(year: int, month: int, active_days: list = None) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру-календарь на месяц.
    active_days — список чисел дней, где есть задачи (их выделим).
    """
    if active_days is None:
        active_days = []

    kb = InlineKeyboardBuilder()
    
    # --- 1. Шапка (Месяц Год) и навигация ---
    # Кнопки: <  Месяц Год  >
    kb.row(
        InlineKeyboardButton(text="<<", callback_data=f"cal:prev:{year}:{month}"),
        InlineKeyboardButton(text=f"{calendar.month_name[month]} {year}", callback_data="cal:ignore"),
        InlineKeyboardButton(text=">>", callback_data=f"cal:next:{year}:{month}")
    )

    # --- 2. Дни недели ---
    days_of_week = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    row_days = [InlineKeyboardButton(text=d, callback_data="cal:ignore") for d in days_of_week]
    kb.row(*row_days)

    # --- 3. Сетка дней ---
    cal = calendar.Calendar(firstweekday=0) # 0 = Понедельник
    month_days = cal.monthdayscalendar(year, month)

    for week in month_days:
        row_btns = []
        for day in week:
            if day == 0:
                # Пустая кнопка (день другого месяца)
                row_btns.append(InlineKeyboardButton(text=" ", callback_data="cal:ignore"))
            else:
                # Проверяем, есть ли задачи на этот день
                if day in active_days:
                    btn_text = f"• {day} •"  # Выделяем
                else:
                    btn_text = str(day)
                
                row_btns.append(InlineKeyboardButton(text=btn_text, callback_data=f"cal:day:{year}:{month}:{day}"))
        
        kb.row(*row_btns)

    # --- 4. Кнопка "Назад" ---
    kb.row(InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_main"))

    return kb.as_markup()