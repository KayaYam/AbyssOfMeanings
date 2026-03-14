import sqlite3
from pathlib import Path
from datetime import datetime

DIARY_DB_PATH = Path("diary.db")

def init_diary_db():
    conn = sqlite3.connect(DIARY_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id TEXT PRIMARY KEY,
            title TEXT,
            text_content TEXT,
            file_path TEXT,
            created_at DATETIME,
            category TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_diary_entry(entry_id, title, content, file_path, category="record"):
    conn = sqlite3.connect(DIARY_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO entries (id, title, text_content, file_path, created_at, category)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (entry_id, title, content, str(file_path), datetime.now(), category))
    conn.commit()
    conn.close()