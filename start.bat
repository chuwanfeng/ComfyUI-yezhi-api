@echo off
chcp 65001 >nul
title ComfyUI-Yezhi-API - AI Image Generation
setlocal enabledelayedexpansion

:: ── Root directory (where this .bat lives) ──
set "PROJECT_DIR=%~dp0"

:: ── Python interpreter priority: 1) .\venv\Scripts\python.exe  2) python ──
set "PYTHON_EXE="
if exist "%PROJECT_DIR%venv\Scripts\python.exe" (
    set "PYTHON_EXE=%PROJECT_DIR%venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)
echo    Python: "!PYTHON_EXE!"

:: ── Check dependencies ──
echo  [*]   Checking dependencies...
!PYTHON_EXE! -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo  [!]   Missing dependencies. Installing from requirements.txt...
    !PYTHON_EXE! -m pip install -r "%PROJECT_DIR%requirements.txt" -q
    if errorlevel 1 (
        echo  [X]   Dependency install failed.
        echo  [>]   Please run manually: pip install -r requirements.txt
        pause
        exit /b 1
    )
)
echo  [OK]  Dependencies OK

:: ── Kill existing on port 5090 (soft kill — only what's listening on 5090) ──
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5090.*LISTENING" 2^>nul') do (
    echo  [*]   Port 5090 occupied by PID %%a ... killing
    taskkill /f /pid %%a >nul 2>&1
    timeout /t 2 /nobreak >nul
)
echo  [OK]  Port 5090 free

:: ── Check .env ──
if not exist "%PROJECT_DIR%.env" (
    echo  [*]   Creating .env from .env.example...
    copy "%PROJECT_DIR%.env.example" "%PROJECT_DIR%.env" >nul
    echo  [OK]  Created .env (SELF_HOSTED_MODE=true by default)
)

:: ── Ensure dirs ──
if not exist "%PROJECT_DIR%uploads" mkdir "%PROJECT_DIR%uploads"
if not exist "%PROJECT_DIR%logs" mkdir "%PROJECT_DIR%logs"
echo  [OK]  Directories ready

:: ── Start ──
cd /d "%PROJECT_DIR%"
echo.
echo  ----------------------------------------------
echo    Frontend : http://127.0.0.1:5090
echo    Health   : http://127.0.0.1:5090/api/health
echo    Logs     : logs\server.log
echo  ----------------------------------------------
echo.

echo  [RUN]  Starting server...
!PYTHON_EXE! app.py
pause
