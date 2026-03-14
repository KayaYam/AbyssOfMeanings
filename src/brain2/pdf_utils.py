# src/brain2/pdf_utils.py
from pathlib import Path
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)

# -------------------------------------------------
def pdf_to_text(pdf_path: Path) -> str:
    """
    Извлекает весь текст из PDF при помощи pdfminer‑six.
    Возвращает строку (может быть пустой, если PDF – скан).
    """
    from pdfminer.high_level import extract_text
    return extract_text(str(pdf_path))


def batch_extract(
    pdf_dir: Path,
    out_dir: Path,
    use_plumber: bool = False,
    ocr_if_needed: bool = False,
    max_pages: int | None = None,
):
    """
    Пробегает по всем *.pdf в pdf_dir и сохраняет *.txt в out_dir.

    Параметры:
    - use_plumber – если True, использует pdfplumber (лучше работает с таблицами)
    - ocr_if_needed – при отсутствии текста делает OCR (нужен tesseract)
    - max_pages – ограничивает количество страниц (для отладки)
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"⚠️  В каталоге {pdf_dir} нет PDF‑файлов")
        return

    for pdf_path in tqdm(pdf_files, desc="PDF → TXT"):
        txt_path = out_dir / f"{pdf_path.stem}.txt"
        if txt_path.is_file():
            continue   # уже обработано

        try:
            if use_plumber:
                import pdfplumber
                with pdfplumber.open(str(pdf_path)) as pdf:
                    parts = []
                    for i, page in enumerate(pdf.pages):
                        if max_pages is not None and i >= max_pages:
                            break
                        text = page.extract_text()
                        parts.append(text or "")
                    txt = "\n".join(parts)
            else:
                txt = pdf_to_text(pdf_path)

            # ------------------- OCR fallback (optional) -------------------
            if ocr_if_needed and not txt.strip():
                # Если текст пустой – считаем, что PDF – скан
                import pytesseract
                from PIL import Image
                import io
                import fitz   # PyMuPDF только для рендера в PNG

                doc = fitz.open(str(pdf_path))
                ocr_parts = []
                for i in range(doc.page_count):
                    if max_pages is not None and i >= max_pages:
                        break
                    pix = doc.load_page(i).get_pixmap(dpi=300)
                    img = Image.open(io.BytesIO(pix.tobytes()))
                    ocr_parts.append(pytesseract.image_to_string(img, lang="eng+rus"))
                txt = "\n".join(ocr_parts)
                doc.close()

            txt_path.write_text(txt, encoding="utf-8")
        except Exception as e:
            logger.error(f"❌ Не удалось обработать {pdf_path.name}: {e}")
