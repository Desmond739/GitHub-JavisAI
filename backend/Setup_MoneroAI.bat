@echo off
setlocal
title MoneroAI Setup

cd /d "%~dp0"

if errorlevel 1 (
    echo ERROR: Could not open the MoneroAI backend folder.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo          MONEROAI SAFE SETUP
echo ==========================================
echo This setup does not use the microphone, speaker, or Google OAuth.
echo.

if not exist "app\main.py" (
    echo ERROR: app\main.py was not found.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating the Python virtual environment...
    py -3 --version >nul 2>&1

    if not errorlevel 1 (
        py -3 -m venv .venv
    ) else (
        python --version >nul 2>&1

        if errorlevel 1 (
            echo ERROR: Python 3 was not found.
            echo Install Python 3.11 or newer, then run this setup again.
            pause
            exit /b 1
        )

        python -m venv .venv
    )

    if errorlevel 1 (
        echo ERROR: The virtual environment could not be created.
        pause
        exit /b 1
    )
)

echo Installing pinned Python dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip

if errorlevel 1 goto :setup_failed

".venv\Scripts\python.exe" -m pip install -r requirements.txt

if errorlevel 1 goto :setup_failed

where ollama >nul 2>&1

if errorlevel 1 (
    echo ERROR: Ollama was not found in PATH.
    echo Install Ollama, then ensure qwen3:8b is available.
    pause
    exit /b 1
)

ollama list 2>nul | findstr /i /c:"qwen3:8b" >nul

if errorlevel 1 (
    echo ERROR: The qwen3:8b Ollama model was not found.
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

call Validate_MoneroAI.bat --from-setup

if errorlevel 1 goto :setup_failed

echo Preparing Naya's speech, fast voice model, and Zira female voice...
".venv\Scripts\python.exe" prepare_voice_runtime.py

if errorlevel 1 goto :setup_failed

echo.
echo MONEROAI SETUP: COMPLETE
echo Run Start_MoneroAI.bat when you are ready to start Naya.
pause
exit /b 0

:setup_failed
echo.
echo ERROR: MoneroAI setup did not complete.
pause
exit /b 1
