@echo off
rem Lanceur Windows pour ufs-diagnostic (application de bureau)
chcp 65001 >nul
cd /d "%~dp0"

set PYEXE=
where python >nul 2>nul && set PYEXE=python
if not defined PYEXE where py >nul 2>nul && set PYEXE=py
if not defined PYEXE if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set PYEXE="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PYEXE if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set PYEXE="%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
if not defined PYEXE if exist "%ProgramFiles%\Python312\python.exe" set PYEXE="%ProgramFiles%\Python312\python.exe"
if not defined PYEXE if exist "%ProgramFiles%\Python313\python.exe" set PYEXE="%ProgramFiles%\Python313\python.exe"

if not defined PYEXE (
  echo.
  echo ERREUR : Python 3 est introuvable sur ce PC.
  echo Installe-le depuis https://www.python.org/downloads/ en cochant "Add python.exe to PATH".
  echo (Ne l'installe PAS depuis le Microsoft Store.)
  echo.
  pause
  exit /b 1
)

%PYEXE% desktop\app.py
pause
