@echo off
setlocal
title MoneroAI

cd /d "%~dp0"

if errorlevel 1 (
    echo ERROR: Could not open the MoneroAI backend folder.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo       STARTING MONEROAI - NAYA
echo ==========================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: MoneroAI virtual environment was not found.
    pause
    exit /b 1
)

if not exist "app\main.py" (
    echo ERROR: app\main.py was not found.
    pause
    exit /b 1
)

echo Running safe non-voice startup validation...
call Validate_MoneroAI.bat --from-setup

if errorlevel 1 (
    echo ERROR: MoneroAI validation failed. Startup was cancelled.
    pause
    exit /b 1
)

where ollama >nul 2>&1

if errorlevel 1 (
    echo ERROR: Ollama was not found in PATH.
    pause
    exit /b 1
)

ollama list >nul 2>&1

if errorlevel 1 (
    echo Starting Ollama...
    start "" /min ollama serve

    for /l %%I in (1,1,20) do (
        ollama list >nul 2>&1
        if not errorlevel 1 goto :ollama_ready
        timeout /t 1 /nobreak >nul
    )

    echo ERROR: Ollama did not become ready within 20 seconds.
    pause
    exit /b 1
)

:ollama_ready
ollama list 2>nul | findstr /i /c:"qwen3:8b" >nul

if errorlevel 1 (
    echo ERROR: The qwen3:8b model was not found.
    echo Run: ollama pull qwen3:8b
    pause
    exit /b 1
)

ollama list 2>nul | findstr /i /c:"qwen3:1.7b" >nul

if errorlevel 1 (
    echo ERROR: The qwen3:1.7b fast voice model was not found.
    echo Run: ollama pull qwen3:1.7b
    pause
    exit /b 1
)

echo Starting Naya, automation, and the MoneroAI API...
echo Wake phrase: Hey Naya
echo Google access: read-only, explicit sync only
echo API: http://127.0.0.1:8001
echo App: http://127.0.0.1:8001/app/
echo.

start "" "http://127.0.0.1:8001/app/"

".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --no-access-log

echo.
echo MoneroAI has stopped.
pause
endlocal
