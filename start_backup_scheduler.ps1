# Start Redis Backup Scheduler
# This script starts the automated backup scheduler with default settings

Write-Host "=" -NoNewline; Write-Host ("=" * 59)
Write-Host "Redis Backup Scheduler - Starting"
Write-Host "=" -NoNewline; Write-Host ("=" * 59)
Write-Host ""

# Default settings
$intervalHours = 24
$compress = "true"
$maxBackups = 7

# Parse command line arguments if provided
if ($args.Count -ge 1) {
    $intervalHours = $args[0]
}
if ($args.Count -ge 2) {
    $compress = $args[1]
}
if ($args.Count -ge 3) {
    $maxBackups = $args[2]
}

Write-Host "Configuration:"
Write-Host "  Backup interval: $intervalHours hours"
Write-Host "  Compression: $compress"
Write-Host "  Max backups to keep: $maxBackups"
Write-Host "  Daily backup time: 03:00"
Write-Host ""

Write-Host "Starting backup scheduler..."
Write-Host ""

# Run the scheduler
python backup_scheduler.py $intervalHours $compress $maxBackups
