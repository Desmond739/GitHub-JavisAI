@echo off
setlocal
cd /d "%~dp0backend"

if errorlevel 1 (
    echo ERROR: The MoneroAI backend folder could not be opened.
    pause
    exit /b 1
)

call Setup_MoneroAI.bat
exit /b %ERRORLEVEL%
