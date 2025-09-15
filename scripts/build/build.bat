@echo off
REM Windows build script for Input Link

echo Building Input Link for Windows...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found in PATH
    exit /b 1
)

REM Install build dependencies if needed
echo Installing build dependencies...
pip install -e ".[build]" --quiet

REM Run build script
python scripts\build\build.py

echo.
echo Build complete! Check the dist\ directory for executables.
pause