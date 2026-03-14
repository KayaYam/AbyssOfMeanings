import requests
import time
import sys
from pathlib import Path
from . import config as cfg
from .db_utils import add_paper

# Фикс кодировки для вывода названий статей
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

S2_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

# Имитируем реальный браузер
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def is_valid_pdf(file_path):
    try:
        with open(file_path, "rb") as f:
            header = f.read(4)
            return header == b"%PDF"
    except:
        return False

def search_and_download(query, label, limit=50):
    # Добавляем фильтр на наличие PDF прямо в запрос
    params = {
        "query": f"{query} has:pdf",
        "limit": limit,
        "fields": "title,authors,year,externalIds,abstract,openAccessPdf"
    }
    
    print(f"[*] Semantic Scholar: Поиск '{query}'...")
    try:
        # Используем HEADERS здесь тоже
        response = requests.get(S2_API_URL, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"[!] Ошибка API Semantic Scholar: {e}")
        return

    data = response.json()
    papers = data.get("data", [])
    
    downloaded = 0
    for p in papers:
        pdf_info = p.get("openAccessPdf")
        if not pdf_info or not pdf_info.get("url"):
            continue
            
        paper_id = p.get("paperId")
        title = p.get("title")
        pdf_url = pdf_info["url"]
        
        pdf_path = cfg.PDF_DIR / f"s2_{paper_id}.pdf"
        
        if pdf_path.exists():
            continue

        try:
            print(f"  --> Скачиваю: {title[:60]}...")
            # Добавляем HEADERS в запрос на скачивание файла
            r = requests.get(pdf_url, headers=HEADERS, timeout=25, stream=True)
            
            if r.status_code == 200:
                with open(pdf_path, "wb") as f:
                    f.write(r.content)
                
                # ПРОВЕРКА ВАЛИДНОСТИ
                if not is_valid_pdf(pdf_path):
                    print(f"  [!] Файл '{title[:30]}...' — это HTML-заглушка (удаляю)")
                    pdf_path.unlink() 
                    continue 

                # Если файл ок — собираем авторов и пишем в базу
                author_list = p.get('authors', [])
                authors_str = ", ".join([a['name'] for a in author_list]) if author_list else "Unknown"
                
                add_paper(
                    id_=f"s2_{paper_id}",
                    title=title,
                    authors=authors_str,
                    published=f"{p.get('year', '2024')}-01-01",
                    pdf_path=pdf_path,
                    source_name="SemanticScholar",
                    topic=label
                )
                downloaded += 1
                # Пауза 3.5 сек, как ты и хотел
                time.sleep(3.5) 
                
        except Exception as e:
            print(f"  [!] Пропуск {title[:30]}: {e}")
            if pdf_path.exists():
                pdf_path.unlink()

    print(f"[OK] Сессия завершена. Новых статей: {downloaded}")