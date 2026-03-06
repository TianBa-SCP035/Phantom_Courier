@echo off
call conda activate Cheems
if not exist "..\dist\bin" mkdir "..\dist\bin"
cd ..\..\src\Service
python -m PyInstaller --onefile --name Service --distpath=..\..\dist\bin --workpath=..\..\build\Service --specpath=..\..\build\Service main.py
cd ..\..\installer\scripts
echo Done! Output: dist\bin\Service.exe
pause