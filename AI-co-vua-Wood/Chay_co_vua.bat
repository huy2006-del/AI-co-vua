@echo off
cd /d "%~dp0"
python --version >nul 2>&1
if errorlevel 1 (
    echo Cai Python 3.10 tro len va them Python vao PATH.
    pause
    exit /b 1
)
python -c "import chess, pygame, matplotlib" >nul 2>&1
if errorlevel 1 (
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        pause
        exit /b 1
    )
)
python -m frontend.gui.app
if errorlevel 1 pause
