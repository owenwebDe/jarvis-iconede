@echo off
setlocal
title Jarvis AI OS - Full Dev Launcher

set "BACKEND_DIR=%~dp0backend"
set "FRONTEND_DIR=%~dp0frontend"

echo ===================================================
echo       JARVIS AI OS - FULL DEVELOPMENT MODE
echo ===================================================
echo.

:: Check backend
netstat -ano | findstr :8000 | findstr LISTENING >nul
if %ERRORLEVEL% neq 0 (
    echo [1/2] Starting Backend Server (port 8000)...
    start "Jarvis Backend" cmd /k cd /d "%BACKEND_DIR%" ^&^& title Jarvis Backend ^&^& .venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload
    ping 127.0.0.1 -n 4 >nul
) else (
    echo [1/2] Backend server is already running on port 8000.
)

echo.
echo [2/2] Starting Frontend Dev Server (port 3000)...
cd /d "%FRONTEND_DIR%"
start "Jarvis Frontend" cmd /k title Jarvis Frontend ^&^& npm run dev

ping 127.0.0.1 -n 4 >nul
echo.
echo ===================================================
echo   Opening Jarvis Dashboard in Browser...
echo ===================================================
start http://localhost:3000

exit /b 0
