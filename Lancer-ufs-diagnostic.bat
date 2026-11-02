@echo off
rem Lanceur Windows pour ufs-diagnostic (application de bureau)
cd /d "%~dp0"
where python >nul 2>nul
if %errorlevel%==0 (
  python desktop\app.py
) else (
  py desktop\app.py
)
pause
