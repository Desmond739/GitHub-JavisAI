@echo off
setlocal
cd /d "%~dp0"
if not exist ".env" (
  echo ERROR: Run Configure_Early_Access.bat first.
  pause
  exit /b 1
)
for /f "delims=" %%L in ('".venv\Scripts\python.exe" mobile_pairing_info.py') do echo %%L
echo.
echo Starting Naya with authenticated local-network access...
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --no-access-log
pause
