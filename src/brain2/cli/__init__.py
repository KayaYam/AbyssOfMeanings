# src/brain2/cli/__init__.py
import sys

def main():
    """
    Запуск команды:   brain2 <subcommand> [options]

    Доступные под‑команды:
        download   – скачивание из arXiv
        extract    – конверсия PDF → TXT
        index      – построение FAISS‑индекса
        digest     – генерация ежедневного дайджеста
    """
    if len(sys.argv) < 2:
        print("usage: brain2 <command> [options]")
        return

    cmd = sys.argv[1]
    # Обрезаем argv, чтобы под‑командам было проще парсить свои аргументы
    sys.argv = sys.argv[1:]

    if cmd == "download":
        from .download import main as run
    elif cmd == "extract":
        from .extract import main as run
    elif cmd == "index":
        from .index import main as run
    elif cmd == "digest":
        from .digest import main as run
    elif cmd == "init-db":
        from .init_db import main as run
    else:
        print(f"unknown command: {cmd}")
        return

    run()
