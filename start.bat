@echo off
chcp 65001 >nul 2>&1
title ComfyUI-Yezhi-API

cd /d "%~dp0"

echo [*] Checking dependencies...
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Missing dependencies, installing...
    pip install -r requirements.txt -q
    if %errorlevel% neq 0 (
        echo [X] Install failed. Run: pip install -r requirements.txt
        pause
        exit /b 1
    )
)
echo [OK] Dependencies OK

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5090.*LISTENING" 2^>nul') do (
    echo [*] Port 5090 busy, killing PID %%a...
    taskkill /f /pid %%a >nul 2>&1
    timeout /t 2 /nobreak >nul
)
echo [OK] Port 5090 free

if not exist ".env" (
    echo [*] Creating .env...
    copy ".env.example" ".env" >nul
    echo [OK] Created .env
)

if not exist "uploads" mkdir "uploads"
if not exist "logs"    mkdir "logs"
echo [OK] Directories ready

echo.
echo ==============================================
echo   Frontend : http://127.0.0.1:5090
echo   Health   : http://127.0.0.1:5090/api/health
echo ==============================================
echo.

echo [RUN] Starting server...
python app.py
pause
