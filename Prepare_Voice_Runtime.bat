@echo off
setlocal
cd /d "%~dp0backend"

if errorlevel 1 (
    echo ERROR: The MoneroAI backend folder could not be opened.
    pause
    exit /b 1
)

call Prepare_Voice_Runtime.bat
exit /b %ERRORLEVEL%
