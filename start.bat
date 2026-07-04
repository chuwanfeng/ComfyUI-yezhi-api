@echo off
chcp 65001 >nul
title ComfyUI-Yezhi-API - AI Image Generation
setlocal enabledelayedexpansion

:: ---- Kill any existing python processes (avoid port conflict) ----
taskkill /f /im python.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo  [OK]  Port 5000 released

:: ---- Check .env ----
if not exist "%PROJECT_DIR%.env" (
    echo  [*]   Creating .env from .env.example...
    copy "%PROJECT_DIR%.env.example" "%PROJECT_DIR%.env" >nul
    echo  [OK]  Created .env (SELF_HOSTED_MODE=true by default)
)

:: ---- Check upload dir ----
if not exist "%PROJECT_DIR%uploads" mkdir "%PROJECT_DIR%uploads"
echo  [OK]  Upload directory ready

:: ---- Start ----
cd /d "%PROJECT_DIR%"
echo.
echo  ----------------------------------------------
echo    Frontend : http://127.0.0.1:5000
echo    Health   : http://127.0.0.1:5000/api/health
echo  ----------------------------------------------
echo.

echo  [RUN]  Starting server with %PYTHON_EXE%...
python app.py
pause
