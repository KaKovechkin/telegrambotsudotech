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
