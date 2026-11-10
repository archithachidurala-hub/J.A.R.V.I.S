@echo off
cd /d "%~dp0"
if not exist .venv (
    echo Setting up J.A.R.V.I.S. for the first time...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip -q
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)
if not exist .env copy .env.example .env >nul
python app.py
pause
