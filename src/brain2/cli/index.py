# src/brain2/cli/index.py
import sys
import codecs
from .. import config as cfg

# Это заставит консоль Windows понимать UTF-8
sys.stdout.reconfigure(encoding='utf-8')
def main():
    """
    Построить FAISS‑индекс по всем txt‑файлам, которые уже прописаны в БД.
    """
    from ..embedding_store import build_faiss_index
    count = build_faiss_index()

# ДОБАВЬ ЭТИ СТРОКИ:
    print("\n" + "="*40)
    print(f"[INDEX] Успешно проиндексировано фрагментов: {count}")
    print(f"[INDEX] Индекс обновлен в: {cfg.EMB_DIR}")
    print("="*40 + "\n")
    
   
   
if __name__ == "__main__":
    main()