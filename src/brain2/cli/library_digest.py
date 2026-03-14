import sqlite3
import sys
from datetime import datetime, timedelta
from brain2.query_engine import get_answer

DB_PATH = "metadata.db"

def get_library_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM papers")
    total = cursor.fetchone()[0]
    cursor.execute("PRAGMA table_info(papers)")
    cols = [c[1] for c in cursor.fetchall()]
    processed = 0
    if 'processed_at' in cols:
        cursor.execute("SELECT COUNT(*) FROM papers WHERE processed_at IS NOT NULL")
        processed = cursor.fetchone()[0]
    conn.close()
    return total, processed

def get_latest_papers(limit=5):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(papers)")
    columns = [info[1] for info in cursor.fetchall()]
    path_col = next((c for c in ['path', 'source', 'file_path'] if c in columns), None)
    
    query_cols = ["title", "topic", "txt_path", "authors", "published"]
    if path_col: query_cols.append(path_col)
    
    cursor.execute(f"SELECT {', '.join(query_cols)} FROM papers ORDER BY rowid DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        d = dict(row)
        if path_col and path_col != 'path': d['path'] = d.pop(path_col)
        elif not path_col: d['path'] = "N/A"
        d['filename'] = d.get('txt_path', 'Destination unknown')
        d['authors'] = d.get('authors', 'Authors unknown')
        d['published'] = d.get('published', 'Published unknown')
        result.append(d)
    return result

def render_digest(mode="latest", value=10):
    total, processed = get_library_stats()
    papers = get_latest_papers(limit=value)
    
    if not papers:
        return "Записи не найдены."

    # Собираем МАКСИМАЛЬНО ПОЛНЫЕ данные для Ollama
    context_data = ""
    for i, p in enumerate(papers, 1):
        context_data += f"--- ОБЪЕКТ [{i}] ---\n"
        context_data += f"ID/ПУТЬ: {p.get('filename', 'N/A')}\n"
        context_data += f"ЗАГОЛОВОК: {p.get('title', 'N/A')}\n"
        context_data += f"АВТОРЫ: {p.get('authors', 'N/A')}\n"
        context_data += f"ДАТА: {p.get('published', 'N/A')}\n"
        context_data += f"ТЕМАТИКА: {p.get('topic', 'N/A')}\n\n"

    # Теперь обновляем инструкцию, чтобы он НЕ игнорировал эти поля
    prompt = f"""
    Ты — научный ассистент. Перед тобой список новых поступлений из базы данных.
    
    ТВОЯ ЗАДАЧА:
    Для каждого объекта из списка ниже составь отчет, СТРОГО используя предоставленные данные. Свой ответи переведи на русский язык.
    
    ФОРМАТ ОТЧЕТА ДЛЯ КАЖДОЙ ЗАПИСИ:
    1. Название и Авторы (если указаны).
    2. ПУТЬ ФАЙЛА (строка из поля ID/ПУТЬ).
    3. Дата публикации.
    4. Расскажи о содержимом статьи как будто пишешь о ней в Научно-порулярный журнал не менее 4000 знаков. Не делай разбор метаданных файла, имени файла, даты публикации - только содержание статьи. Если содержание статьи большое, то можно ограничится введением или первой частью.
    
    ДАННЫЕ ДЛЯ АНАЛИЗА:
    {context_data}
    """
    
    print(f"\n--- АНАЛИЗ {len(papers)} ИСТОЧНИКОВ ---")
    return get_answer(prompt, mode="ask")

def main():
    limit = 1
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            pass
    print(render_digest(mode="latest", value=limit))

if __name__ == "__main__":
    main()
 