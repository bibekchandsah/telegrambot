# Admin Dashboard Startup Script for PowerShell

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Telegram Bot - Admin Dashboard" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "Warning: Virtual environment not found" -ForegroundColor Yellow
    Write-Host "Using global Python installation" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting Admin Dashboard..." -ForegroundColor Green
Write-Host "Dashboard will be available at: http://localhost:5000" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the dashboard" -ForegroundColor Yellow
Write-Host ""

python admin_dashboard.py

Write-Host ""
Write-Host "Dashboard stopped." -ForegroundColor Red
Read-Host "Press Enter to exit"
