@echo off
setlocal
title Naya Voice Preparation

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: MoneroAI virtual environment was not found.
    echo Run Setup_MoneroAI.bat first.
    pause
    exit /b 1
)

echo Preparing Naya's local speech recognition and Zira female voice...
echo The tiny.en speech model may download once.
echo Voice responses use the preinstalled qwen3:1.7b fast model.
echo Zira has no Piper loading or fallback wait.
echo This process does not use the microphone, speaker, or Google.
echo.

".venv\Scripts\python.exe" prepare_voice_runtime.py
set "PREPARE_EXIT=%ERRORLEVEL%"

pause
exit /b %PREPARE_EXIT%
