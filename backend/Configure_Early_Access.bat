@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo ERROR: Run Setup_MoneroAI.bat first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" configure_early_access.py
pause
