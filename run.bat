@echo off
cd /d "%~dp0"

set PYTHONPATH=%~dp0backend;%PYTHONPATH%

python cli.py %*
pause
