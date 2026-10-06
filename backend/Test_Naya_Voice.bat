@echo off
setlocal
title Naya Zira Female Voice Test

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: MoneroAI virtual environment was not found.
    echo Run Setup_MoneroAI.bat first.
    pause
    exit /b 1
)

echo This test uses the speaker only.
echo It does not use the microphone, Google, Azure, Piper, or cloud voice.
echo.

".venv\Scripts\python.exe" test_naya_voice.py
set "TEST_EXIT=%ERRORLEVEL%"

pause
exit /b %TEST_EXIT%
