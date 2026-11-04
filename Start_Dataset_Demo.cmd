@echo off
cd /d "%~dp0"
.venv\Scripts\python.exe -m retail_pulse serve --port 8001
pause
