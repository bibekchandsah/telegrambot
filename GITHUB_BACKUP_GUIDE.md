# GitHub Backup Storage Integration

## Overview

Your Redis backup system now includes **automatic cloud storage on GitHub**! Every backup you create is automatically uploaded to your GitHub repository, giving you:

✅ **Cloud storage** - Backups stored safely on GitHub  
✅ **Version control** - All backups tracked in Git history  
✅ **Easy access** - View and download from GitHub or dashboard  
✅ **Redundancy** - Local + cloud storage for maximum safety  
✅ **Organization** - All backups in one dedicated folder  

## Configuration

### 1. Add to `.env` file:

```env
# GitHub repository (already configured)
GITHUB_REPO=https://github.com/bibekchandsah/webservicelogs
GITHUB_BRANCH=main
GITHUB_TOKEN=your_github_token_here

# Backup storage path on GitHub
MEETGRID_BACKUPS=meetgrid bot/backups/
```

**Already added to your `.env` file!** ✅

### 2. Your GitHub Structure

```
webservicelogs/
└── meetgrid bot/
    ├── photos/          # User photos
    ├── stickers/        # Stickers
    ├── gifs/            # GIFs
    ├── documents/       # Documents
    └── backups/         # ← Backup files stored here!
        ├── redis_backup_20231205_143022.json.gz
        ├── redis_backup_20231205_030000.json.gz
        └── ...
```

## How It Works

### Automatic Upload

When you create a backup:
1. **Local backup** created in `backups/` folder
2. **Automatic upload** to GitHub repository
3. **Confirmation** shown in dashboard with GitHub status

```bash
python create_backup.py

Output:
✅ Backup created successfully!
   📁 Filename: redis_backup_20231205_143022.json.gz
   📊 Size: 2.5 MB
   🔑 Keys: 1234
   ☁️ Uploaded to GitHub: Yes  ← GitHub confirmation
```

### Dual Storage

Every backup exists in **two places**:
- **Local**: `d:\programming exercise\antigravity\telegram bot\backups\`
- **GitHub**: `https://github.com/bibekchandsah/webservicelogs/tree/main/meetgrid bot/backups/`

## Using GitHub Backups

### Via Admin Dashboard

1. **Navigate to** Dashboard → 💾 Backups tab

2. **View backups** in the table:
   - 📁 Local backups (with download/restore options)
   - ☁️ GitHub backups (with view/download options)

3. **Actions available**:
   - **Local backups**: Download, Restore, Delete
   - **GitHub backups**: View on GitHub, Download to local

### Via API

#### List All Backups (Local + GitHub)
```http
GET /api/backup/github/list

Response:
{
  "local": [
    {
      "filename": "redis_backup_20231205_143022.json.gz",
      "size_mb": 2.5,
      "created_at": "2023-12-05T14:30:22"
    }
  ],
  "github": [
    {
      "filename": "redis_backup_20231205_143022.json.gz",
      "size_mb": 2.5,
      "url": "https://github.com/.../backups/redis_backup_...",
      "download_url": "https://raw.githubusercontent.com/..."
    }
  ],
  "github_enabled": true
}
```

#### Download from GitHub to Local
```http
POST /api/backup/github/download
Content-Type: application/json

{
  "filename": "redis_backup_20231205_143022.json.gz"
}

Response:
{
  "success": true,
  "filename": "redis_backup_20231205_143022.json.gz",
  "size_mb": 2.5,
  "filepath": "backups/redis_backup_20231205_143022.json.gz"
}
```

## Benefits

### 🛡️ Disaster Recovery

If your server crashes:
1. **GitHub backups** are safe in the cloud
2. **Download** any backup from GitHub
3. **Restore** on new server
4. **Back online** quickly!

### 📦 Easy Migration

Moving to a new server?
1. **Deploy** bot on new server
2. **Configure** GitHub credentials
3. **Download** latest backup from GitHub
4. **Restore** - done!

### 🔄 Version History

GitHub keeps all versions:
- See when each backup was created
- Compare backup sizes over time
- Restore from any point in time
- Track backup history

### 👥 Team Access

Multiple admins can:
- View all backups on GitHub
- Download backups independently
- Restore on different environments
- Audit backup activity

## Workflows

### Daily Backup to Cloud

```bash
# Start automated scheduler
python backup_scheduler.py 24 true 7

# Every backup automatically:
# 1. Creates local backup
# 2. Uploads to GitHub
# 3. Cleans up old local backups
# 4. GitHub keeps all versions
```

### Download from Cloud

**Scenario**: Need backup but don't have it locally

```bash
# Via dashboard:
1. Navigate to 💾 Backups tab
2. Find GitHub backup (☁️ icon)
3. Click "⬇️ Get" to download to local
4. Now you can restore it

# Via API:
POST /api/backup/github/download
{ "filename": "redis_backup_20231205_143022.json.gz" }
```

### Restore from Cloud Backup

```bash
# 1. Download from GitHub (if not local)
POST /api/backup/github/download
{ "filename": "redis_backup_20231205_143022.json.gz" }

# 2. Restore from local copy
python restore_backup.py redis_backup_20231205_143022.json.gz true
```

## Monitoring

### Check GitHub Storage

```bash
# Via dashboard
Navigate to 💾 Backups → See GitHub backups count

# Via API
GET /api/backup/stats

Response:
{
  "total_backups": 7,           // Local backups
  "github_backups_count": 15,   // GitHub backups
  "github_enabled": true
}
```

### View on GitHub

1. Visit: https://github.com/bibekchandsah/webservicelogs
2. Navigate to: `meetgrid bot/backups/`
3. See all backup files with commit history

## Troubleshooting

### Backup Not Uploading to GitHub

**Check**:
1. GITHUB_TOKEN is valid
2. GITHUB_REPO URL is correct
3. Repository permissions (write access)
4. Backup file size < 100MB

**Fix**:
```bash
# Test GitHub connection
# Check logs for "github_upload_failed"

# Verify configuration
echo $GITHUB_REPO
echo $GITHUB_TOKEN
```

### Cannot Download from GitHub

**Check**:
1. File exists on GitHub
2. GitHub token has read permissions
3. Network connectivity

**Fix**:
```bash
# Try direct GitHub link
# Check dashboard for error messages
```

### Large Backup Files

GitHub has 100MB file limit. If backup > 100MB:

**Solutions**:
1. ✅ Use compression (default)
2. ✅ Clean up old Redis data
3. ✅ Use GitHub LFS (advanced)
4. ✅ Use alternative cloud storage

## Security

### GitHub Token Security

⚠️ **Important**: Keep your GitHub token secure!

- ✅ Use personal access token (PAT)
- ✅ Limit token permissions (only repo access)
- ✅ Don't commit `.env` to Git
- ✅ Rotate token periodically
- ✅ Use GitHub secrets for CI/CD

### Backup Data Security

⚠️ **Important**: Backups contain sensitive user data!

- ✅ Use private repository
- ✅ Limit repository access
- ✅ Consider encryption (advanced)
- ✅ Follow data protection policies
- ✅ Audit access logs

## Best Practices

### Storage Strategy

1. **Local storage**: Quick access, fast restore
2. **GitHub storage**: Cloud backup, disaster recovery
3. **External storage**: Additional backup (Google Drive, etc.)

### Retention Policy

**Local**: Keep 7 recent backups (managed by scheduler)
**GitHub**: Keep all backups (or manually delete old ones)

### Backup Schedule

```bash
# Daily backups with GitHub upload
python backup_scheduler.py 24 true 7

# This ensures:
# - Daily backup at 3 AM
# - Automatic upload to GitHub
# - Local cleanup (keeps 7)
# - GitHub keeps all versions
```

## Advanced Usage

### Manual GitHub Operations

#### List GitHub Backups (API)
```javascript
const response = await fetch('/api/backup/github/list');
const data = await response.json();
console.log('GitHub backups:', data.github);
```

#### Download Specific Backup
```javascript
const response = await fetch('/api/backup/github/download', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename: 'redis_backup_20231205_143022.json.gz' })
});
const result = await response.json();
```

### Batch Operations

Download multiple backups from GitHub:

```bash
# Coming soon: Bulk download feature
# For now, download individually via dashboard
```

## Summary

### What You Have Now

✅ **Automatic cloud backup** - Every backup uploaded to GitHub  
✅ **Dual storage** - Local + cloud redundancy  
✅ **Easy access** - View/download from dashboard or GitHub  
✅ **Version history** - All backups tracked on GitHub  
✅ **Disaster recovery** - Restore from cloud anytime  
✅ **Team access** - Multiple admins can access backups  
✅ **Organized storage** - Dedicated folder structure  

### Quick Reference

```bash
# Create backup (auto-uploads to GitHub)
python create_backup.py

# View all backups
Dashboard → 💾 Backups tab

# Download from GitHub
Click "⬇️ Get" on GitHub backup

# Restore from cloud
1. Download from GitHub
2. python restore_backup.py <filename> true

# Check GitHub storage
GET /api/backup/stats
```

## Next Steps

1. ✅ **Test it**: Create a backup and verify GitHub upload
2. ✅ **Check GitHub**: Visit your repo and see backups folder
3. ✅ **Download test**: Download a backup from GitHub
4. ✅ **Set scheduler**: Enable automated daily backups
5. ✅ **Monitor**: Check GitHub backup count regularly

---

**Your backups are now safely stored in the cloud!** ☁️🛡️

For more information:
- **Complete backup guide**: BACKUP_SYSTEM.md
- **Quick reference**: BACKUP_QUICKSTART.md
- **GitHub repo**: https://github.com/bibekchandsah/webservicelogs
