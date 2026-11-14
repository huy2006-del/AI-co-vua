@echo off
cd /d "%~dp0"
python --version >nul 2>&1
if errorlevel 1 (
  echo Python 3.10 or newer is required and must be on PATH.
  pause
  exit /b 1
)
python -c "import chess" >nul 2>&1
if errorlevel 1 python -m pip install -r ..\requirements.txt
python web_app.py
if errorlevel 1 pause
