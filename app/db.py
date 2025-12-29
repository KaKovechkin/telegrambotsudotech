import sqlite3
from datetime import datetime

DB_NAME = "tasks.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            due_datetime TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)
    conn.commit()
    conn.close()

def add_task(user_id, title, due_datetime):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (user_id, title, due_datetime) VALUES (?, ?, ?)", 
                   (user_id, title, due_datetime))
    conn.commit()
    conn.close()

def list_tasks(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Позволяет обращаться к полям по имени
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE user_id = ? AND status != 'done' ORDER BY due_datetime", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    # Конвертируем в список словарей для удобства JSON
    tasks = []
    for row in rows:
        tasks.append({
            "id": row["id"],
            "title": row["title"],
            "due_datetime": row["due_datetime"],
            "status": row["status"]
        })
    return tasks

# --- НОВАЯ ФУНКЦИЯ ДЛЯ MINI APP ---
def get_all_tasks_json(user_id):
    """Возвращает ВСЕ задачи (и выполненные) для статистики и календаря"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE user_id = ? ORDER BY due_datetime", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    tasks = []
    for row in rows:
        tasks.append({
            "id": row["id"],
            "title": row["title"],
            "due_datetime": row["due_datetime"],
            "status": row["status"]
        })
    return tasks

def delete_task(task_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def mark_task_completed(task_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status = 'done' WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def get_pending_reminders(current_time_str):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE due_datetime = ? AND status != 'done'", (current_time_str,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_days_with_tasks(user_id, year, month):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    search_pattern = f"{year}-{month:02d}-%"
    cursor.execute("SELECT due_datetime FROM tasks WHERE user_id = ? AND due_datetime LIKE ?", (user_id, search_pattern))
    rows = cursor.fetchall()
    conn.close()
    
    days = set()
    for row in rows:
        try:
            date_part = row[0].split(" ")[0] # Берём '2023-10-25'
            day = int(date_part.split("-")[2])
            days.add(day)
        except:
            continue
    return list(days)

def get_tasks_for_day(user_id, date_str):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # date_str приходит как YYYY-MM-DD
    search_pattern = f"{date_str}%"
    cursor.execute("SELECT * FROM tasks WHERE user_id = ? AND due_datetime LIKE ? ORDER BY due_datetime", (user_id, search_pattern))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_stats_data(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'done'", (user_id,))
    completed = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status != 'done'", (user_id,))
    pending = cursor.fetchone()[0]
    
    # Уникальные дни с задачами (активность)
    cursor.execute("SELECT COUNT(DISTINCT substr(due_datetime, 1, 10)) FROM tasks WHERE user_id = ?", (user_id,))
    active_days = cursor.fetchone()[0]
    
    # Категории (парсим из [Категория] Название)
    cursor.execute("SELECT title FROM tasks WHERE user_id = ?", (user_id,))
    all_titles = cursor.fetchall()
    
    category_counts = {}
    for t in all_titles:
        title = t[0]
        if title.startswith("[") and "]" in title:
            cat = title.split("]")[0].strip("[")
            category_counts[cat] = category_counts.get(cat, 0) + 1
            
    conn.close()
    return completed, pending, active_days, category_counts