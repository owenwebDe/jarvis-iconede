@echo off
setlocal
title Jarvis AI OS - Desktop Launcher

set "BACKEND_DIR=%~dp0backend"
set "FRONTEND_DIR=%~dp0frontend"
set "ELECTRON_EXE=%~dp0frontend\node_modules\electron\dist\electron.exe"

echo ===================================================
echo           JARVIS AI OS - DESKTOP EDITION
echo ===================================================
echo.

:: [1/3] Check & Launch Backend Server (port 8000)
echo [1/3] Checking Jarvis FastAPI Backend...
netstat -ano | findstr :8000 | findstr LISTENING >nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Backend server is active on port 8000.
) else (
    echo [..] Launching Backend Server on port 8000...
    start "Jarvis Backend" cmd /k "cd /d "%BACKEND_DIR%" ^&^& title Jarvis Backend ^&^& call .venv\Scripts\activate.bat ^&^& python -m uvicorn server:app --host 127.0.0.1 --port 8000"
    ping 127.0.0.1 -n 4 >nul
)

:: [2/3] Check & Launch Frontend Dev Server (port 3000)
echo.
echo [2/3] Checking Jarvis Frontend Server...
netstat -ano | findstr :3000 | findstr LISTENING >nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Frontend server is active on port 3000.
) else (
    echo [..] Launching Frontend Server on port 3000...
    start "Jarvis Frontend Server" cmd /k cd /d "%FRONTEND_DIR%" ^&^& title Jarvis Frontend Server ^&^& npm run dev
    ping 127.0.0.1 -n 4 >nul
)

:: [3/3] Launch Electron Desktop GUI App directly
echo.
echo [3/3] Launching Jarvis Desktop Window (Electron)...
cd /d "%FRONTEND_DIR%"
if exist "%ELECTRON_EXE%" (
    start "" "%ELECTRON_EXE%" .
) else (
    start "" cmd /c npm run desktop
)

echo.
echo ===================================================
echo   Jarvis AI OS Desktop is running!
echo   - Press [Alt + J] anytime to summon Jarvis.
echo   - Jarvis minimizes to your System Tray on close.
echo ===================================================
ping 127.0.0.1 -n 3 >nul
exit /b 0
