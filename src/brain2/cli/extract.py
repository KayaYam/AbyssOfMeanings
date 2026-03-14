# src/brain2/cli/extract.py
import argparse
from pathlib import Path                     # <-- обязательный импорт
from .. import config as cfg
from ..pdf_utils import batch_extract
from ..db_utils import list_unprocessed, mark_as_processed
import sys
import codecs

# Это заставит консоль Windows понимать UTF-8
sys.stdout.reconfigure(encoding='utf-8')

def main() -> None:
    """
    Конвертировать все PDF → TXT (pdfminer / pdfplumber) и
    отметить в базе, что файл уже обработан.
    """
    parser = argparse.ArgumentParser(
        description="Конвертировать PDF → TXT (pdfminer / pdfplumber)."
    )
    parser.add_argument(
        "--plumber",
        action="store_true",
        help="Использовать pdfplumber (лучше работает с таблицами).",
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Если PDF – скан, выполнить OCR (нужен Tesseract).",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Ограничить количество обрабатываемых страниц (для отладки).",
    )
    args = parser.parse_args()

    # 1️⃣ Конвертируем ВСЕ pdf‑файлы в указанные директории
    batch_extract(
        pdf_dir=cfg.PDF_DIR,
        out_dir=cfg.TXT_DIR,
        use_plumber=args.plumber,
        ocr_if_needed=args.ocr,
        max_pages=args.max_pages,
    )

    # 2️⃣ После конвертации отмечаем в БД, что документы обработаны
    for paper in list_unprocessed():
        # Формируем путь к готовому txt‑файлу
        txt_path = cfg.TXT_DIR / f"{Path(paper.pdf_path).stem}.txt"

        # Если txt‑файл действительно существует – помечаем как processed
        if txt_path.is_file():
            mark_as_processed(paper.id, txt_path)

    print("Конвертация завершена и записи помечены как processed.")
