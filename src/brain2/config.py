# src/brain2/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Метаданные проекта (то, чего не хватало)
VERSION = "0.1.0"
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "your-email@example.com")

BASE_DIR = Path(r"C:/2ndbrain")
DATA_DIR = BASE_DIR / "data"
PDF_DIR  = DATA_DIR / "pdf"
TXT_DIR  = DATA_DIR / "txt"
EMB_DIR  = DATA_DIR / "embeddings"
DIARY_ROOT = Path("diary/records")


for p in (PDF_DIR, TXT_DIR, EMB_DIR):
    p.mkdir(parents=True, exist_ok=True)

# Путь к базе (используем единое имя)
SQLITE_PATH = BASE_DIR / "metadata.db"
DB_PATH = SQLITE_PATH  # Алиас для совместимости с твоим кодом в download.py

ARXIV_MAX_RESULTS = 200
# ... остальное без изменений