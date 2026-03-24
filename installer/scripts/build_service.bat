@echo off
call conda activate Cheems
if not exist "..\dist\bin" mkdir "..\dist\bin"

echo Select build mode:
echo   1. main.py
echo   2. launcher.py

set /p choice="Enter choice (1-2): "

if "%choice%"=="1" (
    cd ..\..\src\Service
    python -m PyInstaller --onedir --name Service --distpath=..\..\dist\bin --workpath=..\..\build\Service --specpath=..\..\build\Service main.py
) else if "%choice%"=="2" (
    cd ..\..\src\Service
    python -m PyInstaller --onefile --name Service --distpath=..\..\dist\bin --workpath=..\..\build\Service --specpath=..\..\build\Service launcher.py
) else (
    echo Invalid choice
)

cd ..\..\installer\scripts
if "%choice%"=="1" (
    echo Done! Output: dist\bin\Service\
) else (
    echo Done! Output: dist\bin\Service.exe
)
pause