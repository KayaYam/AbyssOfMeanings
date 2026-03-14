import time
import re
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus
from pathlib import Path
from typing import Optional, List, Dict
from tqdm import tqdm
from .db_utils import add_paper

from . import config as cfg

ARXIV_API = "http://export.arxiv.org/api/query"
USER_AGENT = f"brain2/{cfg.VERSION}/arxiv-downloader (contact: {cfg.CONTACT_EMAIL})"
REQUEST_DELAY = 1.0 

def sanitize_arxiv_id(url_or_id: str) -> str:
    """Извлекает только цифровой ID, игнорируя протоколы и слэши."""
    # Ищем паттерн типа 2301.12345 или старые форматы типа q-bio/0405027
    match = re.search(r'(\d{4}\.\d+)|([a-z\-]+/\d{7})', url_or_id)
    if match:
        return match.group(0).replace("/", "_") # Заменяем / на _, чтобы Windows не ругался
    return "".join(c for c in url_or_id if c.isalnum())

def build_arxiv_query(
    keywords: Optional[str] = None,
    categories: Optional[str] = None,
    exclude: Optional[str] = None,
    max_results: int = 100,
    start: int = 0
) -> str:
    query_parts = []
    
    # Ищем ключевые слова строго в названии или аннотации
    if keywords:
        kw = keywords.strip().replace(" ", "+")
        query_parts.append(f'%28ti:%22{kw}%22+OR+abs:%22{kw}%22%29')

    # Категории (оставляем только биологические)
    if categories:
        cat_clean = categories.replace(" OR ", "+OR+")
        query_parts.append(f'cat:%28{cat_clean}%29')

    # Расширяем список исключений для борьбы с ML/AI
    ml_exclude = "neural+network+OR+deep+learning+OR+robot+OR+computation"
    if exclude:
        exclude = f"{exclude.strip().replace(' ', '+')}+OR+{ml_exclude}"
    else:
        exclude = ml_exclude
        
    query_parts.append(f'ANDNOT+%28ti:%22{exclude}%22+OR+abs:%22{exclude}%22%29')

    full_query = "+AND+".join(query_parts)
    return f"search_query={full_query}&start={start}&max_results={max_results}&sortBy=relevance&sortOrder=descending"

def fetch_arxiv_batch(query_params: str) -> str:
    url = f"{ARXIV_API}?{query_params}"
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f" API Error: {e}")
        return ""

def parse_arxiv_xml(xml_str: str) -> List[Dict]:
    if not xml_str or "<entry" not in xml_str:
        return []
    root = ET.fromstring(xml_str)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    records = []
    for entry in root.findall("atom:entry", ns):
        id_elem = entry.find("atom:id", ns)
        title_elem = entry.find("atom:title", ns)
        summary_elem = entry.find("atom:summary", ns)
        published_elem = entry.find("atom:published", ns)
        
        pdf_url = ""
        for link in entry.findall("atom:link", ns):
            if link.attrib.get("title") == "pdf":
                pdf_url = link.attrib.get("href")

        authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)]
        
        records.append({
            "arxiv_id": sanitize_arxiv_id(id_elem.text),
            "title": title_elem.text.strip().replace("\n", " "),
            "summary": summary_elem.text.strip(),
            "published": published_elem.text,
            "authors": authors,
            "pdf_url": pdf_url,
        })
    return records

def download_pdf(url: str, save_path: Path, arxiv_id: str) -> bool:
    try:
        resp = requests.get(url, stream=True, timeout=60)
        resp.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        time.sleep(REQUEST_DELAY)
        return True
    except Exception as e:
        print(f" Download error {arxiv_id}: {e}")
        return False

def run(keywords: str, categories: str, exclude: str, max_total: int, start=0) -> List[Dict]:
    """Центральная функция: ищет, скачивает и записывает в БД."""
    query_params = build_arxiv_query(
        keywords, 
        categories, 
        exclude, 
        max_results=max_total, 
        start=start # Прокидываем сюда
    )
    xml_data = fetch_arxiv_batch(query_params)
    records = parse_arxiv_xml(xml_data)
    
    downloaded_count = 0
    pdf_dir = cfg.PDF_DIR
    
    for rec in records:
        safe_id = rec["arxiv_id"]
        pdf_path = pdf_dir / f"{safe_id}.pdf"
        
        if pdf_path.exists():
            continue
            
        print(f"  --> Downloading {safe_id}...")
        success = download_pdf(rec["pdf_url"], pdf_path, safe_id)
        
        if success:
            # СРАЗУ регистрируем в базе
            add_paper(
                id_=safe_id,
                title=rec["title"],
                authors=rec["authors"],
                published=rec["published"],
                pdf_path=pdf_path,
                source_name="arXiv",
                topic=keywords # или любая метка
            )
            downloaded_count += 1
            
    print(f"  [DONE] New papers downloaded: {downloaded_count}")
    return records