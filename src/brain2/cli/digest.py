# src/brain2/cli/digest.py
import argparse
import datetime
from pathlib import Path
from sqlalchemy import text               # <‑‑ импортируем helper
from .. import config as cfg
from ..db_schema import Session, Paper
from ..ollama_summarizer import summarize_text


def _get_new_papers(days_back: int = 1):
    """
    Возвращает список статей, опубликованных за последние `days_back` дней.
    Запрос оформлен через `text()` и параметры передаются словарём
    (требование SQLAlchemy 2.x).
    """
    cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=days_back)).date()

    with Session() as s:
        stmt = s.execute(
            text(
                """
                SELECT id, title, txt_path, published
                FROM papers
                WHERE date(published) >= :cutoff
                ORDER BY published DESC
                """
            ),
            {"cutoff": cutoff.isoformat()},
        )
        rows = stmt.fetchall()
    return rows


def main():
    parser = argparse.ArgumentParser(
        description="Сгенерировать дайджест за последние N дней"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="Сколько дней назад искать новые статьи (по умолчанию 1)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=cfg.BASE_DIR / "daily_digest.md",
        help="Файл, в который будет записан дайджест",
    )
    args = parser.parse_args()

    # Получаем новые статьи
    new_papers = _get_new_papers(days_back=args.days)

    if not new_papers:
        print("За выбранный период новых статей не найдено.")
        args.output.write_text("Новых статей не найдено.", encoding="utf-8")
        return

    # Формируем дайджест – резюме каждой статьи через Ollama
    parts = []
    for pid, title, txt_path, pub in new_papers:
        txt = Path(txt_path).read_text(errors="ignore") if txt_path else ""
        snippet = txt[:2000]                     # ограничиваем размер для LLM
        summary = summarize_text(snippet)
        parts.append(f"**{title}**\n*Опубликовано:* {pub}\n{summary}\n---")

    digest = "\n".join(parts)
    args.output.write_text(digest, encoding="utf-8")
    print(f"Дайджест сохранён в {args.output}")


if __name__ == "__main__":
    main()
