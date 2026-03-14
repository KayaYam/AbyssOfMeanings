import os
import shutil
import hashlib
from pathlib import Path
from .. import config as cfg
from ..db_utils import add_paper
from ..db_schema import Session, Paper
from sqlalchemy import select
from datetime import datetime

def get_file_hash(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def scan_import_folder():
    import_dir = Path("data/import")
    import_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[*] Сканирую: {import_dir}")
    
    # Теперь ищем И PDF, И TXT
    files = list(import_dir.rglob("*.pdf")) + list(import_dir.rglob("*.txt"))
    
    if not files:
        print("--- Новых файлов не найдено.")
        return

    with Session() as session:
        for f_path in files:
            f_hash = get_file_hash(f_path)
            existing = session.execute(
                select(Paper).where(Paper.file_hash == f_hash)
            ).scalar_one_or_none()
            
            if existing:
                continue

            print(f"[+] Импорт: {f_path.name}...")
            
            # Если это PDF — в папку pdf, если TXT — сразу в txt
            safe_id = f"local_{f_hash[:12]}"
    
            if f_path.suffix.lower() == ".txt":
        # ДЛЯ ДНЕВНИКА: прописываем только txt_path
                current_date = datetime.now().strftime("%Y-%m-%d")
                add_paper(
                    id_=safe_id,
                    title=f_path.stem.replace("_", " "),
                    authors="Diary",
                    published=current_date,
                    pdf_path=None,        # Здесь нет PDF
                    txt_path=str(f_path), # Прямой путь к файлу в папке diary
                    source_name="DiaryBot",
                    topic="diary"
                )
            elif f_path.suffix.lower() == ".pdf":
                # ДЛЯ КНИГ: копируем и прописываем pdf_path
                dest_path = cfg.PDF_DIR / f_path.name
                if not dest_path.exists():
                    try:
                        shutil.copy(f_path, dest_path)
                        print(f"[+] Скопировано: {f_path.name}")
                    except PermissionError:
                        print(f"[!] Файл заблокирован, пропускаю: {f_path.name}")
                        continue
            else:
                print(f"[-] Файл уже на месте: {f_path.name}")
                add_paper(
                    id_=safe_id,
                    title=f_path.stem.replace("_", " "),
                    authors="Local Author",
                    published="2026-01-01",
                    pdf_path=str(dest_path),
                    txt_path=None,        # Заполнится позже через extract.py
                    source_name="LocalImport",
                    topic="local"
                )
            
            safe_id = f"local_{f_hash[:12]}"
            add_paper(
                id_=safe_id,
                title=f_path.stem.replace("_", " "),
                authors="Diary",
                published="2026-03-14",
                pdf_path=dest_path if f_path.suffix == ".pdf" else None,
                txt_path=dest_path if f_path.suffix == ".txt" else None,
                source_name="DiaryBot",
                topic="diary"
            )

def main():
    scan_import_folder()

if __name__ == "__main__":
    main()