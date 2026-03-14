import sqlite3
from pathlib import Path

DB_PATH = Path("metadata.db")
TXT_DIR = Path("data/txt")

def final_sync():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Получаем все файлы из папки TXT
    txt_files = list(TXT_DIR.glob("*.txt"))
    print(f"[*] Всего в папке /txt/: {len(txt_files)} файлов")
    
    updated = 0
    for t_path in txt_files:
        # Берем имя файла без расширения
        clean_name = t_path.stem
        
        # Ищем в базе запись, где имя файла содержится в pdf_path или title
        # Используем LIKE для гибкого поиска
        cursor.execute("""
            UPDATE papers 
            SET txt_path = ?, processed_at = datetime('now')
            WHERE txt_path IS NULL 
            AND (pdf_path LIKE ? OR title LIKE ?)
        """, (str(t_path), f"%{clean_name}%", f"%{clean_name}%"))
        
        if cursor.rowcount > 0:
            updated += 1
            
    conn.commit()
    conn.close()
    print(f"✅ Успешно привязано к базе: {updated} текстов")

if __name__ == "__main__":
    final_sync()