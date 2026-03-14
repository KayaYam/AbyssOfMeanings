# src/brain2/cli/download.py
import argparse
import sys
from pathlib import Path
from .. import arxiv_downloader as arxiv
from .. import config as cfg
from ..db_utils import register_source, add_paper

def main():
    parser = argparse.ArgumentParser(
        description="Скачивание PDF‑файлов из arXiv с расширенным поиском"
    )
    
    # Обязательные аргументы
    parser.add_argument("-t", "--topic", required=True, 
                        help="Тема для метки в БД (пример: 'психология')")
    parser.add_argument("-k", "--keywords", required=True,
                        help="Ключевые слова поиска (пример: 'psychology')")
    parser.add_argument("-n", "--max", type=int, default=100,
                        help="Максимальное количество статей")

    # Дополнительные аргументы фильтрации (опциональные)
    parser.add_argument("-c", "--categories", required=False, 
                        help="Категории arXiv через OR (пример: 'q-bio.NC OR cs.HC')")
    parser.add_argument("-x", "--exclude", required=False,
                        help="Исключаемые слова/темы для фильтрации (пример: 'cosmology OR astrophysics')")

    args = parser.parse_args()

    # Инициализация путей и проверок
    pdf_dir = Path(cfg.PDF_DIR)
    db_path = Path(cfg.DB_PATH)
    
    # Регистрация источника (темы) перед запуском, чтобы избежать дублей в БД
    register_source(args.topic)

    # print(f"Поиск статей по запросу:")
    print(f"Ключевые слова: {args.keywords}")
    if args.categories:
        print(f"Категории: {args.categories}")
    if args.exclude:
        print(f"Исключения: {args.exclude}")
    print("-" * 50)

    try:
        # Запуск поиска в arXiv с новыми параметрами
        # Предполагается, что arxiv_downloader.run() умеет принимать kwargs: keywords, categories, exclude
        results = arxiv.run(
            keywords=args.keywords,
            categories=args.categories,
            exclude=args.exclude,
            max_total=args.max
        )
        
        if not results:
            print("Найдено статей: 0. Возможно, запрос слишком специфичен.")
            return

        downloaded = 0
        failed = 0
        
        for rec in results:
            safe_id = rec["arxiv_id"]
            pdf_path = pdf_dir / f"{safe_id}.pdf"

            if pdf_path.exists():
                print(f" Уже существует: {safe_id}")
            else:
                # В аргументах: url (pdf_url), путь сохранения, и сам ID
                success = arxiv.download_pdf(rec["pdf_url"], pdf_path, safe_id)
                if not success:
                    failed += 1
                    continue
                downloaded += 1

            # Регистрируем в БД (используем именованные аргументы!)
            add_paper(
                id_=safe_id,
                title=rec["title"],
                authors=rec["authors"],
                published=rec["published"],
                pdf_path=pdf_path,
                source_name=args.topic,
                topic=args.topic
            )
        
        print("-" * 50)
        print(f"ИТОГО: Найдено: {len(results)} | Скачано: {downloaded} | Пропущено/Ошибка: {failed}")

    except Exception as e:
        # Глобальная ошибка выполнения (например, сбой API или базы данных)
        print(f"КРИТИЧЕСКАЯ ОШИБКА: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
