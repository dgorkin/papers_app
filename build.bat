@echo off
REM Build script for Windows
REM Run from the project root directory

echo Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Building executable with PyInstaller...
pyinstaller literaturemanager.spec --clean

echo.
echo Build complete! Output in dist\LiteratureManager\
echo Run dist\LiteratureManager\LiteratureManager.exe to launch.
pause
