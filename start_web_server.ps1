# MeetGrid Landing Page Server Startup Script (PowerShell)

Write-Host "Starting MeetGrid Landing Page Server..." -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
    Write-Host "Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "No virtual environment found, using system Python" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting server on http://localhost:8080" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Run the web server
python web_server.py
