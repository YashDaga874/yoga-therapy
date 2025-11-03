@echo off
REM Quick launcher - runs from web directory
REM This assumes you're already in the yoga-therapy root directory

cd /d "%~dp0.."
call venv\Scripts\activate.bat
python web\app.py

