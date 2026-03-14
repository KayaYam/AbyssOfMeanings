# src/brain2/cli/init_db.py
def main():
    """Создать/обновить схему БД."""
    from ..db_schema import init_db
    init_db()
