@echo off
echo Building Muxolotl...

REM Создание виртуального окружения, если его нет
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Активация окружения и установка зависимостей
call venv\Scripts\activate.bat
pip install uv
uv pip install pyinstaller -r requirements.txt

REM Запуск PyInstaller
echo Running PyInstaller...
python build.py

echo.
echo Build complete! Find your executable in the 'dist' folder.
pause