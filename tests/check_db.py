import sqlite3
from pathlib import Path

db_path = Path("metadata.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Сколько всего книг?
cursor.execute("SELECT COUNT(*) FROM papers")
total = cursor.fetchone()[0]

# 2. У скольких есть путь к тексту?
cursor.execute("SELECT COUNT(*) FROM papers WHERE txt_path IS NOT NULL")
with_txt = cursor.fetchone()[0]

# 3. Сколько из них реально существуют на диске?
cursor.execute("SELECT txt_path FROM papers WHERE txt_path IS NOT NULL")
paths = cursor.fetchall()
existing_files = sum(1 for p in paths if Path(p[0]).exists())

print(f"--- Отчет по базе данных ---")
print(f"Всего записей в БД: {total}")
print(f"Записей с прописанным txt_path: {with_txt}")
print(f"Реальных файлов в папке /txt/: {existing_files}")

conn.close()