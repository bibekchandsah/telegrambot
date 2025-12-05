# Redis Backup Quick Start Guide

## For Administrators

This is a quick reference guide for managing Redis backups. For detailed documentation, see `BACKUP_SYSTEM.md`.

## Quick Commands

### Create a Manual Backup

```bash
# Windows
python create_backup.py

# Linux/Mac
python3 create_backup.py
```

**Result**: Creates a compressed backup in the `backups/` folder.

---

### View Available Backups

Via Admin Dashboard:
```
GET https://your-dashboard-url/api/backup/list
```

Or check the `backups/` folder directly.

---

### Download a Backup

Via Admin Dashboard:
```
GET https://your-dashboard-url/api/backup/download/<filename>
```

Or copy directly from the `backups/` folder.

---

### Restore from Backup

```bash
# Windows (without overwriting existing keys)
python restore_backup.py redis_backup_20231205_143022.json.gz

# Windows (with overwriting existing keys)
python restore_backup.py redis_backup_20231205_143022.json.gz true

# Linux/Mac (without overwriting)
python3 restore_backup.py redis_backup_20231205_143022.json.gz

# Linux/Mac (with overwriting)
python3 restore_backup.py redis_backup_20231205_143022.json.gz true
```

**⚠️ WARNING**: Use `true` flag carefully - it will overwrite all existing data!

---

### Start Automated Backup Scheduler

#### Windows

Using PowerShell:
```powershell
.\start_backup_scheduler.ps1
```

Using Command Prompt:
```cmd
start_backup_scheduler.bat
```

With custom settings:
```powershell
# Every 12 hours, compressed, keep 14 backups
.\start_backup_scheduler.ps1 12 true 14
```

#### Linux/Mac

```bash
python3 backup_scheduler.py 24 true 7
```

**Settings**:
- First number: Hours between backups (e.g., 24 = daily)
- Second parameter: Compress (true/false)
- Third number: Max backups to keep (old ones deleted automatically)

---

## Emergency Recovery

### If Redis Data is Lost or Corrupted

1. **Stop the bot immediately**
2. **Find the latest backup**:
   ```bash
   python create_backup.py  # This will also show stats
   ```
3. **Restore the backup**:
   ```bash
   python restore_backup.py <latest-backup-filename> true
   ```
4. **Restart the bot**

### If You Need to Migrate to New Redis Server

1. **Create backup on old server**
2. **Download the backup file** (from `backups/` folder)
3. **Update `REDIS_URL` in `.env`** to point to new server
4. **Copy backup file to new server's `backups/` folder**
5. **Restore**:
   ```bash
   python restore_backup.py <backup-filename> true
   ```
6. **Test and verify**

---

## Admin Dashboard API

All API endpoints require TOTP authentication.

### Create Backup
```http
POST /api/backup/create
Content-Type: application/json

{
  "compress": true
}
```

### List Backups
```http
GET /api/backup/list
```

### Download Backup
```http
GET /api/backup/download/<filename>
```

### Restore Backup
```http
POST /api/backup/restore
Content-Type: application/json

{
  "filename": "redis_backup_20231205_143022.json.gz",
  "overwrite": false
}
```

### Delete Backup
```http
DELETE /api/backup/delete/<filename>
```

### Get Statistics
```http
GET /api/backup/stats
```

---

## Best Practices

### ✅ DO:

- **Create backups before major changes** (migrations, updates, etc.)
- **Download important backups** and store them somewhere safe (cloud storage, external drive)
- **Run automated scheduler in production** (daily minimum)
- **Test restore process** regularly to ensure backups work
- **Keep at least 7 days of backups**
- **Use compression** to save disk space

### ❌ DON'T:

- **Don't restore with overwrite=true** unless you're absolutely sure
- **Don't delete all backups** - keep at least one recent backup
- **Don't store backups only on the same server** - use external storage too
- **Don't skip testing restores** - a backup you can't restore is useless
- **Don't ignore disk space** - monitor available space for backups

---

## Troubleshooting

### "Backup file not found"
- Check the `backups/` folder exists
- Verify the filename is correct (case-sensitive)
- Ensure you're in the project root directory

### "Connection refused" when creating backup
- Check if Redis is running
- Verify `REDIS_URL` in `.env` is correct
- Test connection: `python test_redis_connection.py`

### Backup scheduler not creating backups
- Check if the scheduler process is running
- Review logs for errors
- Ensure disk space is available
- Verify Redis connection

### Restore shows many "skipped" keys
- This is normal if `overwrite=false` (default)
- Keys that already exist are skipped
- Use `overwrite=true` to replace existing keys

---

## File Locations

```
telegram bot/
├── backups/                           # Backup files stored here
│   ├── redis_backup_YYYYMMDD_HHMMSS.json.gz
│   └── ...
├── create_backup.py                   # Manual backup tool
├── restore_backup.py                  # Manual restore tool
├── backup_scheduler.py                # Automated scheduler
├── start_backup_scheduler.ps1         # Windows PowerShell launcher
├── start_backup_scheduler.bat         # Windows batch launcher
├── BACKUP_SYSTEM.md                   # Detailed documentation
└── BACKUP_QUICKSTART.md              # This file
```

---

## Get Help

- **Detailed docs**: See `BACKUP_SYSTEM.md`
- **Test Redis**: Run `python test_redis_connection.py`
- **Check logs**: Review application logs for error details
- **Backup stats**: `GET /api/backup/stats` via dashboard

---

## Summary

**Most common tasks**:

1. **Manual backup**: `python create_backup.py`
2. **Start scheduler**: `.\start_backup_scheduler.ps1` (Windows) or `python3 backup_scheduler.py` (Linux)
3. **Emergency restore**: `python restore_backup.py <filename> true`
4. **Download backup**: Copy from `backups/` folder or use dashboard

**Remember**: Backups are your insurance policy - use them wisely! 🛡️
