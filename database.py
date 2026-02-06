import sqlite3
from pathlib import Path

DB_PATH = Path("lifehub.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT DEFAULT 'General',
        active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS habit_logs (
        habit_id INTEGER NOT NULL,
        day TEXT NOT NULL,
        done INTEGER DEFAULT 0,
        note TEXT DEFAULT '',
        PRIMARY KEY (habit_id, day),
        FOREIGN KEY (habit_id) REFERENCES habits(id)
    )
    """)

    conn.commit()
    conn.close()

