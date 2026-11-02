@echo off
rem Lanceur Windows pour ufs-diagnostic (application de bureau)
chcp 65001 >nul
cd /d "%~dp0"
echo Dossier de lancement : %CD%
if not exist "desktop\app.py" (
  echo.
  echo ERREUR : desktop\app.py introuvable dans %CD%
  echo Le dossier du projet est incomplet : re-télécharge le ZIP complet depuis
  echo https://github.com/Guilh69/ufs-diagnostic (Code ^> Download ZIP) et dézippe-le ENTIER.
  echo.
  pause
  exit /b 1
)

set PYEXE=
where python >nul 2>nul && set PYEXE=python
if not defined PYEXE where py >nul 2>nul && set PYEXE=py
if not defined PYEXE (
  for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" set PYEXE="%%D\python.exe"
  )
)
if not defined PYEXE if exist "%ProgramFiles%\Python314\python.exe" set PYEXE="%ProgramFiles%\Python314\python.exe"

if not defined PYEXE (
  echo.
  echo ERREUR : Python 3 introuvable. Installe-le depuis https://www.python.org/downloads/
  echo en cochant "Add python.exe to PATH" (PAS depuis le Microsoft Store).
  echo.
  pause
  exit /b 1
)

echo Python utilisé : %PYEXE%
%PYEXE% --version
echo Lancement de l'application...
%PYEXE% desktop\app.py
echo.
echo (Si une erreur Python s'est affichée ci-dessus, copie-la ici.)
pause
