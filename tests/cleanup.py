from brain2.db_schema import Session, Paper
from sqlalchemy import delete

def remove_paper_by_title_part(title_part):
    with Session() as session:
        # Ищем по части заголовка (например, "КАНТ")
        stmt = delete(Paper).where(Paper.title.like(f"%{title_part}%"))
        result = session.execute(stmt)
        session.commit()
        print(f"[OK] Удалено записей из БД: {result.rowcount}")

if __name__ == "__main__":
    remove_paper_by_title_part("И.Кант")