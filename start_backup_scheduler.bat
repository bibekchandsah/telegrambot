@echo off
REM Start Redis Backup Scheduler
REM This script starts the automated backup scheduler with default settings

echo ============================================================
echo Redis Backup Scheduler - Starting
echo ============================================================
echo.

REM Default settings
set INTERVAL_HOURS=24
set COMPRESS=true
set MAX_BACKUPS=7

REM Parse command line arguments if provided
if not "%1"=="" set INTERVAL_HOURS=%1
if not "%2"=="" set COMPRESS=%2
if not "%3"=="" set MAX_BACKUPS=%3

echo Configuration:
echo   Backup interval: %INTERVAL_HOURS% hours
echo   Compression: %COMPRESS%
echo   Max backups to keep: %MAX_BACKUPS%
echo   Daily backup time: 03:00
echo.

echo Starting backup scheduler...
echo.

REM Run the scheduler
python backup_scheduler.py %INTERVAL_HOURS% %COMPRESS% %MAX_BACKUPS%
