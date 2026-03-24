@echo off
call conda activate Cheems
if not exist "..\dist\bin" mkdir "..\dist\bin"

cd ..\..\src\Control
python -m PyInstaller --onefile --noconsole --name "Phantom Courier" --icon="Courier.ico" --distpath=..\..\dist\bin --workpath=..\..\build\Control main.py --clean

cd ..\..\installer\scripts
echo Done! Output: dist\bin\Phantom Courier.exe
pause
