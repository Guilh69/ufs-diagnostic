@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === DIAGNOSTIC PYTHON POUR ufs-diagnostic === > diagnostic.txt
echo. >> diagnostic.txt
echo [where python] >> diagnostic.txt
where python >> diagnostic.txt 2>&1
echo. >> diagnostic.txt
echo [where py] >> diagnostic.txt
where py >> diagnostic.txt 2>&1
echo. >> diagnostic.txt
echo [py --version] >> diagnostic.txt
py --version >> diagnostic.txt 2>&1
echo. >> diagnostic.txt
echo [python --version] >> diagnostic.txt
python --version >> diagnostic.txt 2>&1
echo. >> diagnostic.txt
echo [dossier Python utilisateur] >> diagnostic.txt
dir "%LOCALAPPDATA%\Programs\Python" >> diagnostic.txt 2>&1
echo. >> diagnostic.txt
echo [dossier Python systeme] >> diagnostic.txt
dir "%ProgramFiles%\Python*" >> diagnostic.txt 2>&1
echo. >> diagnostic.txt
echo [PATH] >> diagnostic.txt
echo %PATH% >> diagnostic.txt
echo. >> diagnostic.txt
echo === FIN === >> diagnostic.txt
type diagnostic.txt
