@echo off
echo Running MuXolotl...

REM Создание виртуального окружения, если его нет
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Активация окружения и установка зависимостей
call venv\Scripts\activate.bat
pip install uv
uv pip install -r requirements.txt

REM Запуск MuXolotl
echo Running MuXolotl...
python main.py

pause