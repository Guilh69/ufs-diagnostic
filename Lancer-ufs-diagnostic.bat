@echo off
rem Lanceur Windows pour ufs-diagnostic (application de bureau)
rem Fichier 100%% ASCII : aucun accent, pour eviter tout probleme d'encodage.
cd /d "%%~dp0"
echo Dossier de lancement : %%CD%%
if not exist "desktop\app.py" (
  echo ERREUR : desktop\app.py introuvable dans %%CD%%
  echo Re-telecharge le ZIP complet depuis https://github.com/Guilh69/ufs-diagnostic
  pause
  exit /b 1
)
set PYEXE=
where python >nul 2>nul && set PYEXE=python
if not defined PYEXE where py >nul 2>nul && set PYEXE=py
if not defined PYEXE for /d %%%%D in ("%%LOCALAPPDATA%%\Programs\Python\Python3*") do if exist "%%D\python.exe" set PYEXE="%%D\python.exe"
if not defined PYEXE if exist "%%ProgramFiles%%\Python314\python.exe" set PYEXE="%%ProgramFiles%%\Python314\python.exe"
if not defined PYEXE (
  echo ERREUR : Python 3 introuvable. Installe-le depuis https://www.python.org/downloads/ en cochant Add python.exe to PATH.
  pause
  exit /b 1
)
echo Python : %%PYEXE%%
%%PYEXE%% --version
echo Lancement de l application...
%%PYEXE%% desktop\app.py
echo Si une erreur Python apparait ci-dessus, copie-la ici.
pause
