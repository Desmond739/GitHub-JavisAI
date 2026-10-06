@echo off
setlocal
title MoneroAI Non-Voice Validation

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: MoneroAI virtual environment was not found.
    echo Run Setup_MoneroAI.bat first.
    if /i not "%~1"=="--from-setup" pause
    exit /b 1
)

set "VOICE_ENABLED=false"
set "AUTOMATION_ENABLED=false"
set "OLLAMA_WARMUP_ENABLED=false"

".venv\Scripts\python.exe" validate_moneroai.py
set "VALIDATION_EXIT=%ERRORLEVEL%"

if not "%VALIDATION_EXIT%"=="0" goto :validation_done

".venv\Scripts\python.exe" validate_voice_tuning_offline.py
set "VALIDATION_EXIT=%ERRORLEVEL%"

:validation_done
if /i not "%~1"=="--from-setup" pause
exit /b %VALIDATION_EXIT%
