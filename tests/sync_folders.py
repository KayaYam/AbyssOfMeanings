import sqlite3
import hashlib
from pathlib import Path

DB_PATH = Path("metadata.db")
PDF_DIR = Path("data/pdf")

def get_hash(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def sync():
    if not DB_PATH.exists():
        print(f"[!] База {DB_PATH} не найдена.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    pdf_files = list(PDF_DIR.glob("*.pdf"))
    print(f"[*] На диске найдено PDF: {len(pdf_files)}")
    
    # Очищаем таблицу перед чистой вставкой
    cursor.execute("DELETE FROM papers") 
    
    added_count = 0
    for pdf_path in pdf_files:
        actual_hash = get_hash(pdf_path)
        file_id = f"local_{actual_hash[:12]}"
        title = pdf_path.stem.replace("_", " ")
        
        try:
            # ДОБАВИЛИ КОЛОНКУ file_hash
            cursor.execute("""
                INSERT INTO papers (id, title, pdf_path, processed_at, topic, source, file_hash)
                VALUES (?, ?, ?, NULL, 'local', 'LocalSync', ?)
            """, (file_id, title, str(pdf_path), actual_hash))
            added_count += 1
        except sqlite3.Error as e:
            print(f"[!] Ошибка вставки {pdf_path.name}: {e}")
            
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM papers")
    total_db = cursor.fetchone()[0]
    conn.close()
    
    print(f"\n--- ИТОГ СИНХРОНИЗАЦИИ ---")
    print(f"Файлов на диске: {len(pdf_files)}")
    print(f"Записей в базе: {total_db}")
    
    if len(pdf_files) == total_db:
        print("✅ ПОБЕДА! Теперь база полная.")
    else:
        print("❌ ОШИБКА: Снова не всё зашло.")

if __name__ == "__main__":
    sync()