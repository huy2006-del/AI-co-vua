@echo off
setlocal
set "ROOT=%~dp0"
set "PYTHON=%ROOT%.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
  py -3 -m venv "%ROOT%.venv"
  if errorlevel 1 python -m venv "%ROOT%.venv"
)
if not exist "%PYTHON%" (
  echo Could not create the project Python environment. Install Python 3.10 or newer and try again.
  pause
  exit /b 1
)

"%PYTHON%" -c "import chess, pygame, pandas, matplotlib" >nul 2>&1
if errorlevel 1 (
  echo Installing project dependencies...
  "%PYTHON%" -m pip install -r "%ROOT%requirements.txt"
  if errorlevel 1 (
    echo Dependency installation failed. Check your internet connection and try again.
    pause
    exit /b 1
  )
)

cd /d "%ROOT%AI-co-vua-Wood"
set "PYTHONPATH=%CD%\backend;%CD%;%PYTHONPATH%"
"%PYTHON%" -m frontend.gui.app %*
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" pause
exit /b %EXIT_CODE%
