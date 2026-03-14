import sys
import os
from pathlib import Path
import logging
import sync_txt

# 1. Находим корень проекта (C:\2ndbrain)
# Мы находимся в /tests/morning_routine.py, значит корень — на один уровень выше
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Добавляем /src в пути поиска
# Теперь Python поймет, что такое 'from brain2...'
sys.path.append(str(BASE_DIR / "src"))

# 3. Теперь импортируем БЕЗ точек, как внешние библиотеки
try:
    from brain2.cli import folder_import, extract, index, library_digest
    #from brain2 import diary_db
    print("✅ Модули успешно импортированы")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print(f"Проверь, что путь существует: {BASE_DIR / 'src' / 'brain2'}")
    # sys.exit(1)
    
from brain2.cli import library_digest

from brain2.cli import folder_import
from brain2.cli import extract
from brain2.cli import index


try:
    from brain2.cli import folder_import, extract, index, library_digest
    # ВАЖНО: Импортируем сами модули, чтобы обращаться к ним semantic_downloader.search...
    from brain2 import semantic_downloader
    from brain2 import arxiv_downloader
    print("✅ Все модули загружены")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)


def run_daily_update():
    print("--- 🧠 ЗАПУСК ЕЖЕДНЕВНОГО ОБНОВЛЕНИЯ МОЗГА ---")
    
    # === ШАГ 0: АВТОНОМНЫЙ ПОИСК В СЕТИ ===
    print("\n[0/5] 🌐 Выхожу в интернет за новинками...")
    
    # 1. Используем Semantic Scholar (он сам знает, что искать, если мы вызовем его штатно)
    # Мы можем просто перечислить главные темы для поиска
    arxiv_downloader.run() 
    
    # Запускаем Semantic Scholar с его паузами в 3.5 сек и проверкой валидности PDF
    semantic_downloader.search_and_download()
    
    
    
    
    # Шаг 1: Импорт новых PDF из папки /import
    print("\n[1/4] Сканирую новые поступления...")
    folder_import.scan_import_folder()
    
    # Шаг 2: Синхронизация (на случай, если файлы подкинули вручную в /pdf)
    # Мы встроим сюда логику нашего sync_txt, чтобы база видела всё
    print("[2/4] Проверяю целостность путей в базе...")
    sync_txt.final_sync() 
    
    # Шаг 3: Экстракция текста из новых PDF
    print("\n[3/4] Извлекаю смыслы (PDF -> TXT)...")
    extract.main()
    
    # Шаг 4: Индексация (Библиотека + Дневник)
    print("\n[4/4] Обновляю нейронные связи (Индексация)...")
    #index.main(store_type="library")
    #index.main(store_type="diary")
    index.main()
    
    print("\n✅ ГОТОВО! Мозг актуален.")
    
    print(library_digest.render_digest(mode="days", value=1))
    
if __name__ == "__main__":
    run_daily_update()