# src/brain2/db_schema.py
import datetime
from pathlib import Path
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, sessionmaker

# Путь к базе берём из config (чтобы он всегда был одинаков)
from . import config as cfg
print(f"[DB_DEBUG] Using database at: {cfg.SQLITE_PATH}")

engine = sa.create_engine(f"sqlite:///{cfg.SQLITE_PATH}", future=True, echo=False)
Session = sessionmaker(bind=engine, future=True)

Base = declarative_base()


class Source(Base):
    __tablename__ = "sources"
    name = sa.Column(sa.String, primary_key=True)          # e.g. "arXiv", "manual"
    last_fetched = sa.Column(sa.DateTime, nullable=True)
    completed = sa.Column(sa.Boolean, default=False)


class Paper(Base):
    __tablename__ = "papers"
    id = sa.Column(sa.String, primary_key=True)           # arXiv‑id / DOI / uuid
    title = sa.Column(sa.Text, nullable=False)
    authors = sa.Column(sa.Text)                         # JSON‑строка
    published = sa.Column(sa.DateTime, nullable=True)
    pdf_path = sa.Column(sa.Text, nullable=False, unique=True)
    txt_path = sa.Column(sa.Text, nullable=True, unique=True)
    source = sa.Column(sa.String, sa.ForeignKey("sources.name"), nullable=False)
    file_hash = sa.Column(sa.String(64), nullable=False)   # SHA‑256 хеш
    processed_at = sa.Column(sa.DateTime, nullable=True)
    topic = sa.Column(sa.String, nullable=True)

    __table_args__ = (
        sa.Index("ix_hash", "file_hash"),
        sa.Index("ix_processed", "processed_at"),
    )


# --------------------------------------------------------------
def init_db() -> None:
    """
    Создаёт все таблицы, если их ещё нет.
    Вызывается один раз перед первым использованием проекта.
    """
    Base.metadata.create_all(engine)
    print(f"✅ База SQLite проинициализирована: {cfg.SQLITE_PATH}")
