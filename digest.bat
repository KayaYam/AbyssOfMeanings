@echo off
chcp 65001 >nul
echo 📖 Генерирую интеллектуальный дайджест библиотеки...
set PYTHONPATH=src
call poetry run python src/brain2/cli/library_digest.py
pause