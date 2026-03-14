# src/brain2/__init__.py
"""
Главный пакет brain2.

Экспортируем часто‑используемые объекты, чтобы в ноутбуках писать:
    from brain2 import config, arxiv_downloader, pdf_utils, db_utils
"""

from . import config
from . import arxiv_downloader
from . import pdf_utils
from . import db_schema
from . import db_utils
from . import embedding_store
from . import ollama_summarizer
