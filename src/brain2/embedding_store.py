import json
import faiss
import numpy as np
from pathlib import Path
from . import config as cfg
from .db_schema import Session, Paper
from sqlalchemy import select

# Твоя функция разбивки текста на куски (оставляем как была)
def get_chunks(text, chunk_size=1000, overlap=100):
    if not text:
        return []
    # (Здесь твоя текущая логика разбиения текста)
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - overlap)]

def build_faiss_index(store_type="library"):
    """
    store_type: "library" (книги) или "diary" (твой опыт)
    """
    # 1. Настраиваем пути в зависимости от типа
    if store_type == "diary":
        index_path = cfg.EMB_DIR / "diary.index"
        meta_path = cfg.EMB_DIR / "diary_meta.json"
        topic_filter = "diary"
        print(f"[*] Индексация ДНЕВНИКА...")
    else:
        index_path = cfg.EMB_DIR / "library.index"
        meta_path = cfg.EMB_DIR / "library_meta.json"
        topic_filter = "local" # Или то, что ты ставишь книгам в базе
        print(f"[*] Индексация БИБЛИОТЕКИ...")

    # 2. Загружаем существующие метаданные
    existing_metadata = []
    indexed_ids = set()
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                existing_metadata = json.load(f)
                indexed_ids = {m["paper_id"] for m in existing_metadata}
        except Exception as e:
            print(f"[!] Ошибка чтения меты: {e}")

    # 3. Ищем в базе новые записи для этого типа
    from .query_engine import EMBEDDER # Берем модель, загруженную в памяти
    
    with Session() as session:
        # Фильтруем по топику и наличию текстового пути
        query = select(Paper.id, Paper.txt_path).where(
            Paper.txt_path.isnot(None),
            Paper.topic == topic_filter
        )
        all_papers = session.execute(query).all()
    
    new_papers = [(pid, path) for pid, path in all_papers if pid not in indexed_ids]
    
    if not new_papers:
        print(f"[INDEX] {store_type}: Новых данных нет.")
        return len(existing_metadata)

    print(f"[INDEX] Добавляю {len(new_papers)} новых записей в {store_type}...")
    
    new_vectors = []
    new_metadata = []
    
    for paper_id, txt_path in new_papers:
        # ЖЕСТКАЯ ПРОВЕРКА №1: Проверка на None (NoneType killer)
        if txt_path is None:
            continue
            
        p = Path(txt_path)
        
        # ЖЕСТКАЯ ПРОВЕРКА №2: Физическое наличие файла
        if not p.exists():
            print(f"[WARN] Файл не найден: {p}")
            continue
        
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
            if not text.strip():
                continue
                
            chunks = get_chunks(text)
            if not chunks:
                continue
            
            # Кодируем (модель уже в памяти)
            vecs = EMBEDDER.encode(chunks, normalize_embeddings=True)
            new_vectors.append(vecs.astype("float32"))
            for c in chunks:
                new_metadata.append({"paper_id": paper_id, "text": c})
        except Exception as e:
            print(f"[!] Ошибка файла {p}: {e}")
            continue

    if not new_vectors:
        return len(existing_metadata)

    # 4. Обновление FAISS
    combined_new_vecs = np.vstack(new_vectors)
    dim = 384 # Для all-MiniLM-L6-v2
    
    if index_path.exists() and len(existing_metadata) > 0:
        index = faiss.read_index(str(index_path))
        index.add(combined_new_vecs)
    else:
        index = faiss.IndexFlatL2(dim)
        index.add(combined_new_vecs)

    # 5. Сохранение
    faiss.write_index(index, str(index_path))
    full_meta = existing_metadata + new_metadata
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(full_meta, f, ensure_ascii=False, indent=2)

    print(f"[SUCCESS] Индекс {store_type} обновлен.")
    return len(full_meta)