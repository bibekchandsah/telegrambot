# Redis Backup & Restore System

## Overview

This system provides comprehensive backup and restore capabilities for all Redis data in the Telegram bot. It includes:

- **Manual backups** through Admin Dashboard API
- **Automated scheduled backups** with configurable intervals
- **Backup download** for local storage
- **Restore functionality** with overwrite protection
- **Backup management** (list, delete, stats)

## Features

### ✅ What Gets Backed Up

The backup system captures **ALL** Redis data:
- User profiles and preferences
- Chat histories and matches
- Queue data
- Ban records and warnings
- Reports and moderation data
- Activity logs
- All other data stored in Redis

### ✅ Backup Features

- **Complete data preservation**: All Redis key types (strings, hashes, lists, sets, sorted sets)
- **TTL preservation**: Keys with expiration times are restored with their original TTL
- **Binary data support**: Handles both text and binary data correctly
- **Compression**: Optional gzip compression to reduce file size
- **Metadata**: Each backup includes timestamp and key count
- **Security**: Filename validation to prevent path traversal attacks

## Backup File Format

Backups are stored as JSON (optionally gzip compressed) with the following structure:

```json
{
  "timestamp": "20231205_143022",
  "created_at": "2023-12-05T14:30:22.123456",
  "data": {
    "user:123456": {
      "type": "hash",
      "value": {
        "name": "John",
        "age": "25"
      },
      "ttl": null
    },
    "queue:users": {
      "type": "list",
      "value": ["123456", "789012"],
      "ttl": null
    }
  }
}
```

## Using the Backup System

### 1. Manual Backup via Admin Dashboard

#### Create Backup
```bash
POST /api/backup/create
Authorization: Required (TOTP authenticated)

Body (JSON):
{
  "compress": true  // Optional, default: true
}

Response:
{
  "success": true,
  "filename": "redis_backup_20231205_143022.json.gz",
  "filepath": "backups/redis_backup_20231205_143022.json.gz",
  "size": 45678,
  "size_mb": 0.04,
  "timestamp": "20231205_143022",
  "keys_count": 1234,
  "compressed": true
}
```

#### List Backups
```bash
GET /api/backup/list
Authorization: Required (TOTP authenticated)

Response:
{
  "backups": [
    {
      "filename": "redis_backup_20231205_143022.json.gz",
      "filepath": "backups/redis_backup_20231205_143022.json.gz",
      "size": 45678,
      "size_mb": 0.04,
      "created_at": "2023-12-05T14:30:22",
      "timestamp": "20231205_143022",
      "compressed": true
    }
  ]
}
```

#### Download Backup
```bash
GET /api/backup/download/<filename>
Authorization: Required (TOTP authenticated)

Example:
GET /api/backup/download/redis_backup_20231205_143022.json.gz

Response: File download
```

#### Restore Backup
```bash
POST /api/backup/restore
Authorization: Required (TOTP authenticated)

Body (JSON):
{
  "filename": "redis_backup_20231205_143022.json.gz",
  "overwrite": false  // Optional, default: false
}

Response:
{
  "success": true,
  "filename": "redis_backup_20231205_143022.json.gz",
  "restored_count": 1234,
  "skipped_count": 0,
  "error_count": 0,
  "total_keys": 1234
}
```

**Note**: When `overwrite: false`, existing keys will be skipped. Set `overwrite: true` to replace existing data.

#### Delete Backup
```bash
DELETE /api/backup/delete/<filename>
Authorization: Required (TOTP authenticated)

Example:
DELETE /api/backup/delete/redis_backup_20231205_143022.json.gz

Response:
{
  "success": true,
  "filename": "redis_backup_20231205_143022.json.gz"
}
```

#### Get Backup Statistics
```bash
GET /api/backup/stats
Authorization: Required (TOTP authenticated)

Response:
{
  "total_backups": 7,
  "total_size": 320000,
  "total_size_mb": 0.31,
  "latest_backup": {
    "filename": "redis_backup_20231205_143022.json.gz",
    "created_at": "2023-12-05T14:30:22"
  },
  "oldest_backup": {
    "filename": "redis_backup_20231201_030000.json.gz",
    "created_at": "2023-12-01T03:00:00"
  }
}
```

### 2. Automated Scheduled Backups

#### Start Backup Scheduler

Run the scheduler with default settings (24-hour interval, compressed, keep 7 backups):
```bash
python backup_scheduler.py
```

Run with custom settings:
```bash
python backup_scheduler.py <interval_hours> <compress> <max_backups>

# Examples:
python backup_scheduler.py 12 true 14          # Every 12 hours, compressed, keep 14 backups
python backup_scheduler.py 6 false 30          # Every 6 hours, uncompressed, keep 30 backups
```

#### Schedule Configuration

The scheduler runs backups:
1. **At specified intervals** (default: every 24 hours)
2. **Daily at 3 AM** (regardless of interval)

#### Automatic Cleanup

The scheduler automatically deletes old backups, keeping only the `max_backups` most recent files.

### 3. Command Line Backup Tool

Create a manual backup from command line:

```python
# create_backup.py
import asyncio
from src.db.redis_client import RedisClient
from src.services.backup import BackupService

async def main():
    client = RedisClient()
    await client.connect()
    
    backup = BackupService(client)
    result = await backup.create_backup(compress=True)
    
    if result['success']:
        print(f"✅ Backup created: {result['filename']}")
        print(f"   Size: {result['size_mb']} MB")
        print(f"   Keys: {result['keys_count']}")
    else:
        print(f"❌ Backup failed: {result['error']}")
    
    await client.close()

asyncio.run(main())
```

## Backup Storage

Backups are stored in the `backups/` directory in the project root:

```
telegram bot/
├── backups/
│   ├── redis_backup_20231205_143022.json.gz
│   ├── redis_backup_20231205_030000.json.gz
│   ├── redis_backup_20231204_030000.json.gz
│   └── ...
├── src/
├── backup_scheduler.py
└── ...
```

## Disaster Recovery Workflow

### Scenario: Redis Data Loss

1. **Stop the bot** to prevent new data writes:
   ```bash
   # Stop the bot process
   ```

2. **List available backups**:
   ```bash
   GET /api/backup/list
   ```

3. **Download the most recent backup** (recommended):
   ```bash
   GET /api/backup/download/<filename>
   ```
   Save this file to a safe location.

4. **Restore the backup**:
   ```bash
   POST /api/backup/restore
   {
     "filename": "redis_backup_20231205_143022.json.gz",
     "overwrite": true
   }
   ```

5. **Verify the restoration**:
   - Check backup stats: `GET /api/backup/stats`
   - Test bot functionality
   - Check user counts: `GET /api/stats`

6. **Restart the bot** once verified.

### Scenario: Migrate to New Redis Instance

1. **Create backup on old instance**:
   ```bash
   POST /api/backup/create
   ```

2. **Download the backup file**:
   ```bash
   GET /api/backup/download/<filename>
   ```

3. **Update Redis URL** in `.env`:
   ```
   REDIS_URL=redis://new-redis-host:6379/0
   ```

4. **Upload backup to new server** (copy to `backups/` directory)

5. **Restore on new instance**:
   ```bash
   POST /api/backup/restore
   {
     "filename": "redis_backup_20231205_143022.json.gz",
     "overwrite": true
   }
   ```

## Best Practices

### 🔒 Security

1. **Protect backup files**: They contain sensitive user data
2. **Secure storage**: Store backups in encrypted storage
3. **Access control**: Only authorized admins should access backups
4. **Network security**: Use HTTPS for dashboard access

### 📅 Backup Schedule

1. **Development**: Manual backups before major changes
2. **Production**: Automated daily backups (minimum)
3. **High-traffic**: Consider 6-12 hour intervals
4. **Critical periods**: Backup before/after migrations

### 💾 Storage Management

1. **Retention policy**: Keep at least 7 days of backups
2. **Compression**: Always use compression (saves ~70% space)
3. **External storage**: Copy backups to cloud storage (AWS S3, Google Drive, etc.)
4. **Monitor disk space**: Ensure adequate space for backups

### ✅ Testing

1. **Test restores regularly**: Verify backups are valid
2. **Dry run**: Use `overwrite: false` first to test
3. **Staging environment**: Test restores on staging before production

## Integration with Deployment

### Add to systemd (Linux)

Create `/etc/systemd/system/backup-scheduler.service`:

```ini
[Unit]
Description=Redis Backup Scheduler
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/telegram bot
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python backup_scheduler.py 24 true 7
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable backup-scheduler
sudo systemctl start backup-scheduler
sudo systemctl status backup-scheduler
```

### Railway Deployment

Add to your Railway service:

1. **Create a new service** for backup scheduler
2. **Use the same REDIS_URL** environment variable
3. **Run command**: `python backup_scheduler.py 12 true 14`
4. **Add volume** (if supported) to persist backups

### Docker Compose

Add to `docker-compose.yml`:

```yaml
services:
  backup-scheduler:
    build: .
    command: python backup_scheduler.py 24 true 7
    environment:
      - REDIS_URL=${REDIS_URL}
    volumes:
      - ./backups:/app/backups
    depends_on:
      - redis
    restart: unless-stopped
```

## Monitoring

### Check Scheduler Logs

```bash
# If running as systemd service
sudo journalctl -u backup-scheduler -f

# If running in terminal
# Logs will appear in console
```

### Backup Health Check

Monitor these metrics:
- Last backup timestamp
- Backup file sizes
- Backup success/failure rate
- Disk space usage

Example monitoring script:

```python
import asyncio
from src.db.redis_client import RedisClient
from src.services.backup import BackupService

async def check_backup_health():
    client = RedisClient()
    await client.connect()
    
    backup = BackupService(client)
    stats = await backup.get_backup_stats()
    
    print(f"Total backups: {stats['total_backups']}")
    print(f"Total size: {stats['total_size_mb']} MB")
    
    if stats['latest_backup']:
        print(f"Latest: {stats['latest_backup']['created_at']}")
    
    await client.close()

asyncio.run(check_backup_health())
```

## Troubleshooting

### Backup Creation Fails

**Problem**: Backup fails with timeout or memory error

**Solution**:
- Check Redis connection: `test_redis_connection.py`
- Increase memory limits if needed
- Use compression to reduce memory usage

### Restore Fails

**Problem**: Restore completes but some keys are missing

**Solution**:
- Check `error_count` in restore response
- Review logs for specific errors
- Ensure Redis has enough memory
- Check Redis `maxmemory-policy` setting

### Large Backup Files

**Problem**: Backups are very large

**Solutions**:
1. Always use compression: `compress: true`
2. Clean up old/unused data before backup
3. Consider incremental backups (future enhancement)

### Scheduler Not Running

**Problem**: Automated backups not being created

**Solution**:
- Check scheduler process is running
- Review scheduler logs for errors
- Verify Redis connection
- Check disk space for backups

## Dependencies

Add to `requirements.txt` if not already present:

```txt
redis>=4.5.0
schedule>=1.2.0
```

Install:
```bash
pip install -r requirements.txt
```

## Future Enhancements

Potential improvements:
- [ ] Incremental backups
- [ ] Cloud storage integration (S3, Google Drive)
- [ ] Backup encryption
- [ ] Email notifications on backup success/failure
- [ ] Webhook notifications
- [ ] Backup verification/integrity checks
- [ ] Web UI for backup management

## Summary

The Redis backup system provides robust data protection with:

✅ **Easy manual backups** through API  
✅ **Automated scheduled backups** with retention  
✅ **Download capability** for offline storage  
✅ **Fast restore** with overwrite protection  
✅ **Complete data coverage** (all Redis keys)  
✅ **Compression** for efficient storage  
✅ **Monitoring** via statistics endpoint  

**Remember**: Regular backups are your safety net! Test your restore process regularly.
