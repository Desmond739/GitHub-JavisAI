@echo off
setlocal
title Final Naya Voice Pipeline Test

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: MoneroAI virtual environment was not found.
    echo Run Setup_MoneroAI.bat first.
    pause
    exit /b 1
)

echo WARNING: This final test uses your microphone and speaker.
echo It uses local Whisper, Ollama, and Microsoft Zira.
echo It does not use Google, Azure, Piper, or another cloud voice.
echo.
echo Close any running MoneroAI window before this test.
echo.

".venv\Scripts\python.exe" final_naya_voice_test.py
set "TEST_EXIT=%ERRORLEVEL%"

pause
exit /b %TEST_EXIT%
