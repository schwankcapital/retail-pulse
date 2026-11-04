@echo off
setlocal
cd /d "%~dp0.."
if not exist .env copy .env.example .env >nul
if not exist runtime\retail_pulse.sqlite3 (
    python -m retail_pulse demo
    if errorlevel 1 exit /b 1
)
python -m retail_pulse serve
