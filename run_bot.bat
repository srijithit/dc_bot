@echo off
title Discord Multi-Bot Runner
echo ==========================================
echo Starting Discord Multi-Bot (10 Instances)
echo ==========================================
echo.

:: Automatically check and install requirements
echo Verifying dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python is not installed or not added to your system PATH.
    echo Please install Python 3.11+ and check "Add Python to PATH" during setup.
    echo.
    pause
    exit /b
)

echo.
echo Launching all bots...
echo Keep this window open to stay online!
echo.
python bot.py

echo.
echo Bots have been stopped.
pause
