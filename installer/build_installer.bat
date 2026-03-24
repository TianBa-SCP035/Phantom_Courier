@echo off
cd /d "%~dp0"
if not exist "output" mkdir "output"
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" build_installer.iss
pause
