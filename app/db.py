import sqlite3

DB_PATH = "tasks.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            due_datetime TEXT,
            remind INTEGER DEFAULT 0,
            completed INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()



def add_task(user_id, title, due_datetime, remind):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (user_id, title, due_datetime, remind, completed) VALUES (?, ?, ?, ?, 0)",
        (user_id, title, due_datetime, 1 if remind else 0)
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def list_tasks(user_id, only_active=True):
    conn = get_connection()
    cur = conn.cursor()
    if only_active:
        cur.execute("SELECT * FROM tasks WHERE user_id=? AND completed=0", (user_id,))
    else:
        cur.execute("SELECT * FROM tasks WHERE user_id=?", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(zip([c[0] for c in cur.description], row)) for row in rows]


def get_task(task_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return dict(zip([c[0] for c in cur.description], row))
    return None


def mark_completed(task_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET completed=1 WHERE id=?", (task_id,))
    conn.commit()
    conn.close()


def delete_task(task_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()


def update_task_title(task_id, new_title):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET title=? WHERE id=?", (new_title, task_id))
    conn.commit()
    conn.close()


def update_task_datetime(task_id, new_datetime):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET due_datetime=? WHERE id=?", (new_datetime, task_id))
    conn.commit()
    conn.close()


def update_task_remind(task_id, remind):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET remind=? WHERE id=?", (1 if remind else 0, task_id))
    conn.commit()
    conn.close()


def get_pending_reminders():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, user_id, title, due_datetime FROM tasks WHERE remind = 1 AND completed = 0")
    rows = cur.fetchall()
    conn.close()
    return [dict(zip(["id", "user_id", "title", "due_datetime"], row)) for row in rows]
