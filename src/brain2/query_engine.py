import json
import faiss
import numpy as np
import os
from sentence_transformers import SentenceTransformer
from . import config as cfg
from .db_schema import Session, Paper
from sqlalchemy import select
from brain2.ollama_summarizer import ollama_chat

# Загружаем модель один раз при импорте модуля
print("[INFO] Загрузка нейросети EMBEDDER...")
EMBEDDER = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def get_context(query, top_k=15, mode="ask"):
    index_path = cfg.EMB_DIR / "papers.index"
    meta_path = cfg.EMB_DIR / "chunks_metadata.json"

    if not index_path.exists() or not meta_path.exists():
        return "Контекст не найден.", []

    index = faiss.read_index(str(index_path))
    with open(meta_path, "r", encoding="utf-8") as f:
        chunks_metadata = json.load(f)

    # Поиск векторов
    query_vec = EMBEDDER.encode([query], normalize_embeddings=True).astype("float32")
    distances, indices = index.search(query_vec, top_k)
    
    context_parts = []
    seen_papers = set()
    sources_info = []
    
    with Session() as session:
        for idx in indices[0]:
            if idx == -1 or idx >= len(chunks_metadata): continue
            chunk = chunks_metadata[idx]
            context_parts.append(chunk["text"])
            
            if chunk["paper_id"] not in seen_papers:
                paper = session.execute(select(Paper).where(Paper.id == chunk["paper_id"])).scalar_one_or_none()
                if paper:
                    sources_info.append({"id": paper.id, "title": paper.title})
                    seen_papers.add(paper.id)

    # Настройка роли ИИ
    if mode == "reflect":
        system_role = (
            "Ты — глубокий аналитический ассистент и психолог. Твоя цель: помочь пользователю осмыслить его жизнь.\n"
            "НЕ ищи события жизни пользователя в книгах. ПРИМЕНЯЙ ТЕОРИИ из книг к этим событиям.\n"
            "Если пользователь говорит про зависимости или драйв — используй Сапольски (дофамин). \n"
            "Если про риски и неопределенность — Талеба (антихрупкость).\n"
            "Игнорируй технический мусор (телефоны, рекламу) в контексте."
        )
    else:
        system_role = "Ты — ученый-синтезатор. Отвечай на вопросы, используя предоставленный контекст."

    full_context = f"SYSTEM INSTRUCTION: {system_role}\n\nRELEVANT LIBRARY CHUNKS:\n" + "\n---\n".join(context_parts)
    return full_context, sources_info
    
def get_answer(query, mode="ask"):
    # 1. Получаем контекст через твою функцию поиска
    full_context, sources = get_context(query, mode=mode)
    
    # 2. Используем твою рабочую функцию
    # Передаем системный промпт (с контекстом) и вопрос пользователя
    answer = ollama_chat(
        system_prompt=full_context, 
        user_prompt=query, 
        model="qwen3.5:9b"
    )
    
    return answer