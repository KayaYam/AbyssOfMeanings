@echo off
chcp 65001 >nul

echo [%date% %time%] --- Global Sync Start ---

:: Убрали дефис перед именем файла
call poetry run python tests\morning_routine.py

echo [%date% %time%] --- Sync Complete ---
pause