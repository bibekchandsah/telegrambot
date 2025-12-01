@echo off
REM Admin Dashboard Startup Script

echo ========================================
echo   Telegram Bot - Admin Dashboard
echo ========================================
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found
    echo Using global Python installation
)

echo.
echo Starting Admin Dashboard...
echo Dashboard will be available at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the dashboard
echo.

python admin_dashboard.py

pause
