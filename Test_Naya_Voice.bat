@echo off
setlocal
cd /d "%~dp0backend"

if errorlevel 1 (
    echo ERROR: The MoneroAI backend folder could not be opened.
    pause
    exit /b 1
)

call Test_Naya_Voice.bat
exit /b %ERRORLEVEL%
