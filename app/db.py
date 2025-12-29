import sqlite3
from datetime import datetime
from config import DB_PATH

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        due_datetime TEXT,
        remind INTEGER DEFAULT 1,
        completed INTEGER DEFAULT 0
    )
    """)

    con.commit()
    con.close()

init_db()

# Добавление задачи
def add_task(user_id, title, due_datetime, remind=1):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("""
        INSERT INTO tasks (user_id, title, due_datetime, remind)
        VALUES (?, ?, ?, ?)
    """, (user_id, title, due_datetime, int(remind)))

    con.commit()
    con.close()

# Список задач
def list_tasks(user_id):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    cur.execute("""
        SELECT * FROM tasks
        WHERE user_id=?
        ORDER BY due_datetime
    """, (user_id,))

    rows = cur.fetchall()
    con.close()
    return rows

# Удаление
def delete_task(task_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    con.commit()
    con.close()

# Получить напоминания
def get_pending_reminders(now):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    cur.execute("""
        SELECT * FROM tasks
        WHERE remind=1 AND completed=0 AND due_datetime=?
    """, (now,))

    rows = cur.fetchall()
    con.close()
    return rows

# === НОВЫЕ ФУНКЦИИ ДЛЯ КАЛЕНДАРЯ ===

def get_tasks_for_day(user_id, date_str):
    """
    Возвращает задачи за конкретный день.
    """
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    # Ищем задачи, где дата начинается с 'YYYY-MM-DD'
    search_pattern = f"{date_str}%"
    
    cur.execute("""
        SELECT * FROM tasks
        WHERE user_id=? AND due_datetime LIKE ?
        ORDER BY due_datetime
    """, (user_id, search_pattern))
    
    rows = cur.fetchall()
    con.close()
    return rows

def get_days_with_tasks(user_id, year, month):
    """
    Возвращает список чисел (дней), на которые есть задачи в месяце.
    """
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    search_pattern = f"{year}-{month:02d}-%"
    
    cur.execute("""
        SELECT due_datetime FROM tasks
        WHERE user_id=? AND due_datetime LIKE ?
    """, (user_id, search_pattern))
    
    rows = cur.fetchall()
    con.close()
    
    active_days = set()
    for row in rows:
        try:
            # row[0] = '2025-05-25 14:00'. Бьем строку, чтобы достать '25'
            day_str = row[0].split(" ")[0].split("-")[2]
            active_days.add(int(day_str))
        except:
            continue
            
    return list(active_days)

# ... (начало файла без изменений)

# ОБНОВЛЕННАЯ функция списка задач (показывает только активные)
def list_tasks(user_id):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # Берем только те, где completed = 0
    cur.execute("""
        SELECT * FROM tasks
        WHERE user_id=? AND completed=0
        ORDER BY due_datetime
    """, (user_id,))

    rows = cur.fetchall()
    con.close()
    return rows

# === НОВЫЕ ФУНКЦИИ ДЛЯ КИЛЛЕР-ФИЧИ ===

def mark_task_completed(task_id):
    """Помечает задачу как выполненную"""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("UPDATE tasks SET completed=1 WHERE id=?", (task_id,))
    con.commit()
    con.close()

def get_stats_data(user_id):
    """Собирает цифры для графиков"""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    # 1. Считаем выполненные и активные
    cur.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND completed=1", (user_id,))
    completed_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND completed=0", (user_id,))
    pending_count = cur.fetchone()[0]
    
    # 2. Считаем нагрузку по дням (для активных задач)
    # Группируем по дате (первые 10 символов строки времени: YYYY-MM-DD)
    cur.execute("""
        SELECT substr(due_datetime, 1, 10) as day, COUNT(*) 
        FROM tasks 
        WHERE user_id=? AND completed=0
        GROUP BY day
        ORDER BY day ASC
        LIMIT 5
    """, (user_id,))
    
    rows = cur.fetchall()
    con.close()
    
    # Подготовка данных для графика
    days = []
    counts = []
    for r in rows:
        # Превращаем '2025-12-31' в '31.12' для красоты
        try:
            date_part = r[0].split("-")
            formatted_date = f"{date_part[2]}.{date_part[1]}"
            days.append(formatted_date)
            counts.append(r[1])
        except:
            continue
            
    return completed_count, pending_count, days, counts