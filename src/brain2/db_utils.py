# src/brain2/db_utils.py
import hashlib
import json
import datetime
from pathlib import Path
from sqlalchemy import select
from . import config as cfg
from .db_schema import Session, Source, Paper


def _hash_file(file_path: Path) -> str:
    # 1. Защита: превращаем в Path, если пришла строка
    if isinstance(file_path, str):
        file_path = Path(file_path)
        
    # 2. Инициализируем объект хеша
    import hashlib
    h = hashlib.sha256()
    
    # 3. Открываем файл ОДИН раз и читаем по кусочкам
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
            
    # 4. Возвращаем результат
    return h.hexdigest()


def register_source(name: str) -> Source:
    """Создаёт запись о новом источнике, если её ещё нет."""
    with Session() as s:
        src = s.get(Source, name)
        if not src:
            src = Source(name=name, last_fetched=None, completed=False)
            s.add(src)
            s.commit()
        return src


def add_paper(
    *,
    id_: str,
    title: str,
    authors: list[str] | None,
    published: str | None,
    pdf_path: Path,
    source_name: str,
    topic: str,  # ← добавляем тему
    txt_path: Path | None = None,
    processed: bool = False,
) -> Paper:
    """
    Добавляем (или обновляем) запись о PDF‑файле.
    Дедупликация происходит по SHA‑256 хешу.
    """
    file_hash = _hash_file(pdf_path)

    with Session() as s:
        # Проверяем, есть ли уже файл с тем же хешем
        existing = s.execute(select(Paper).where(Paper.file_hash == file_hash)).scalar_one_or_none()
        if existing:
            # Если путь изменился – обновляем
            if existing.pdf_path != str(pdf_path):
                existing.pdf_path = str(pdf_path)
                s.commit()
            return existing

        # Новая запись
        paper = Paper(
            id=id_,
            title=title,
            authors=json.dumps(authors or []),
            published=datetime.datetime.fromisoformat(published) if published else None,
            pdf_path=str(pdf_path),
            txt_path=str(txt_path) if txt_path else None,
            source=source_name,
            file_hash=file_hash,
            topic=topic,  # ← добавляем тему
            processed_at=datetime.datetime.utcnow() if processed else None,
        )
        s.add(paper)
        s.commit()
        return paper


def mark_as_processed(paper_id: str, txt_path: Path):
    """Помечаем запись как обработанную (сохраняем путь к txt)."""
    with Session() as s:
        paper = s.get(Paper, paper_id)
        if not paper:
            raise ValueError(f"Paper with id={paper_id} not found")
        paper.processed_at = datetime.datetime.utcnow()
        paper.txt_path = str(txt_path)
        s.commit()


def is_already_processed(paper_id: str) -> bool:
    """Быстрая проверка: уже есть txt‑файл?"""
    with Session() as s:
        paper = s.get(Paper, paper_id)
        return bool(paper and paper.processed_at)


def list_unprocessed(limit: int = 100) -> list[Paper]:
    """Возвращает список записей, которые ещё не обработаны."""
    with Session() as s:
        stmt = select(Paper).where(Paper.processed_at.is_(None)).limit(limit)
        return list(s.scalars(stmt).all())
