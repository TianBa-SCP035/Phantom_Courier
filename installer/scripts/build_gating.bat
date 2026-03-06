@echo off
call conda activate Cheems
if not exist "..\dist\bin" mkdir "..\dist\bin"
cd ..\..\src\Gating
python -m PyInstaller --onefile --name Gating --distpath=..\..\dist\bin --workpath=..\..\build\Gating --specpath=..\..\build\Gating main.py
cd ..\..\installer\scripts
echo Done! Output: dist\bin\Gating.exe
pause