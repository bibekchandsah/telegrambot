@echo off
echo Starting MeetGrid Landing Page Server...
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo Virtual environment activated
) else (
    echo No virtual environment found, using system Python
)

echo.
echo Starting server on http://localhost:8080
echo Press Ctrl+C to stop
echo.

python web_server.py

pause
