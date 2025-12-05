# ✅ Redis Backup System - Admin Checklist

## Initial Setup Checklist

### Installation
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Verify Redis connection: `python test_redis_connection.py`
- [ ] Test backup system: `python test_backup_system.py`
- [ ] Create `backups/` directory (auto-created, but verify)

### First Backup
- [ ] Create your first manual backup: `python create_backup.py`
- [ ] Verify backup file exists in `backups/` folder
- [ ] Check backup size is reasonable
- [ ] Download and save backup to safe location

### Dashboard Setup
- [ ] Access admin dashboard
- [ ] Navigate to "💾 Backups" tab
- [ ] Verify you can see backup statistics
- [ ] Test creating a backup from dashboard
- [ ] Test downloading a backup

### Automated Backups
- [ ] Decide on backup frequency (default: 24 hours)
- [ ] Decide on retention period (default: 7 backups)
- [ ] Start backup scheduler
  - [ ] Windows: `.\start_backup_scheduler.ps1`
  - [ ] Linux: `python3 backup_scheduler.py`
- [ ] Verify scheduler is running
- [ ] Wait for first scheduled backup
- [ ] Verify auto-cleanup works (after 8th backup)

---

## Daily Operations Checklist

### Routine Monitoring (Weekly)
- [ ] Check dashboard "💾 Backups" tab
- [ ] Verify latest backup is recent (< 24 hours)
- [ ] Check total backup count (should be ~7)
- [ ] Verify disk space is sufficient
- [ ] Download latest backup for external storage

### Before Major Changes
- [ ] Create manual backup: `python create_backup.py`
- [ ] Download the backup
- [ ] Store in safe location
- [ ] Document what changes you're making
- [ ] Proceed with changes

### After Major Changes
- [ ] Verify bot is working correctly
- [ ] Check for any errors in logs
- [ ] Create another backup (post-change)
- [ ] Keep both pre and post-change backups

---

## Monthly Maintenance Checklist

### Backup Health
- [ ] Review all backups in dashboard
- [ ] Check backup file sizes (should be similar)
- [ ] Delete very old backups (if keeping > 30)
- [ ] Verify at least 3 recent backups exist
- [ ] Test restore process on staging/test environment

### Storage Management
- [ ] Check disk space usage
- [ ] Review `backups/` folder size
- [ ] Archive old backups to external storage
- [ ] Delete unnecessary old backups
- [ ] Verify external backups are accessible

### Testing
- [ ] Test backup creation: `python create_backup.py`
- [ ] Test backup system: `python test_backup_system.py`
- [ ] Test restore (on test environment):
  ```bash
  python restore_backup.py <recent-backup> false
  ```
- [ ] Verify restored data integrity
- [ ] Document test results

---

## Emergency Response Checklist

### Data Loss Detected
- [ ] **STOP** the bot immediately
- [ ] Identify what data was lost
- [ ] Check latest backup timestamp
- [ ] Determine which backup to use
- [ ] Download backup if not local

### Before Restore
- [ ] Document current state
- [ ] Create emergency backup of current state (even if corrupted)
- [ ] Confirm restore file is correct
- [ ] Notify users if needed (service interruption)

### Restore Process
- [ ] Run restore command:
  ```bash
  python restore_backup.py <backup-filename> true
  ```
- [ ] Monitor restore progress
- [ ] Check for errors in output
- [ ] Verify key counts match

### After Restore
- [ ] Test bot functionality
- [ ] Verify user data is present
- [ ] Check queue, chats, settings
- [ ] Restart bot
- [ ] Monitor for issues
- [ ] Create new backup
- [ ] Document incident

---

## Security Checklist

### Access Control
- [ ] Limit admin dashboard access
- [ ] Use HTTPS for dashboard
- [ ] Secure TOTP authentication
- [ ] Limit backup file access
- [ ] Use strong session secrets

### Data Protection
- [ ] Backup files stored securely
- [ ] External backups encrypted (recommended)
- [ ] Access logs enabled
- [ ] Regular security audits
- [ ] Follow data retention policies

### Compliance
- [ ] Document backup procedures
- [ ] Follow GDPR/privacy requirements
- [ ] Secure disposal of old backups
- [ ] Audit trail maintained
- [ ] Incident response plan documented

---

## Deployment Checklist

### Development Environment
- [ ] Manual backups before deployments
- [ ] Test restore on staging
- [ ] Verify backup compatibility

### Production Environment
- [ ] Automated scheduler running
- [ ] Daily backups at 3 AM configured
- [ ] External backup storage configured
- [ ] Monitoring alerts set up
- [ ] Disaster recovery plan documented

### Railway Deployment
- [ ] Backup scheduler service created
- [ ] Environment variables configured
- [ ] Volume storage configured (if available)
- [ ] Logs monitored

### Docker Deployment
- [ ] Backup service in docker-compose.yml
- [ ] Volume mounts configured
- [ ] Container restart policy set
- [ ] Logs accessible

### Linux (systemd)
- [ ] Service file created
- [ ] Service enabled
- [ ] Service running
- [ ] Logs monitored: `journalctl -u backup-scheduler -f`

---

## Performance Checklist

### Backup Performance
- [ ] Backup creation time reasonable (< 5 min)
- [ ] Backup file size reasonable (< 100 MB)
- [ ] Compression working (file size ~30% smaller)
- [ ] No timeout errors

### Restore Performance
- [ ] Restore time reasonable (< 10 min)
- [ ] No memory errors
- [ ] Redis memory sufficient
- [ ] All keys restored successfully

### System Resources
- [ ] Disk space monitored
- [ ] Redis memory monitored
- [ ] CPU usage acceptable
- [ ] Network bandwidth sufficient

---

## Documentation Checklist

### Internal Documentation
- [ ] Backup procedures documented
- [ ] Admin contacts listed
- [ ] Emergency procedures clear
- [ ] Restore process documented
- [ ] Troubleshooting guide available

### Training
- [ ] Admin team trained on backups
- [ ] Emergency procedures practiced
- [ ] Restore process tested
- [ ] Documentation accessible

---

## Troubleshooting Checklist

### Backup Creation Fails
- [ ] Check Redis connection: `python test_redis_connection.py`
- [ ] Verify disk space available
- [ ] Check Redis memory settings
- [ ] Review error logs
- [ ] Test with smaller compression

### Restore Fails
- [ ] Verify backup file exists
- [ ] Check file integrity (not corrupted)
- [ ] Verify Redis connection
- [ ] Check Redis memory available
- [ ] Try with overwrite=false first

### Scheduler Not Running
- [ ] Check if process is running
- [ ] Review scheduler logs
- [ ] Verify Redis connection
- [ ] Check disk space
- [ ] Restart scheduler

### Dashboard Issues
- [ ] Verify authentication works
- [ ] Check API endpoints accessible
- [ ] Review browser console errors
- [ ] Check network connectivity
- [ ] Verify TOTP working

---

## Best Practices Checklist

### Backup Strategy
- [ ] Automated daily backups enabled
- [ ] Manual backups before changes
- [ ] External backup storage used
- [ ] At least 7 days retention
- [ ] Compression enabled

### Monitoring
- [ ] Weekly backup checks
- [ ] Monthly restore tests
- [ ] Disk space monitoring
- [ ] Error log reviews
- [ ] Performance monitoring

### Security
- [ ] Backups stored securely
- [ ] Access controlled
- [ ] Encryption used (external storage)
- [ ] Audit logs maintained
- [ ] Compliance followed

---

## Annual Review Checklist

### System Review
- [ ] Review backup strategy effectiveness
- [ ] Assess storage requirements
- [ ] Review retention policy
- [ ] Evaluate automation
- [ ] Update procedures if needed

### Disaster Recovery
- [ ] Test full disaster recovery
- [ ] Update recovery documentation
- [ ] Train new admins
- [ ] Review incident reports
- [ ] Improve procedures

### Compliance & Audit
- [ ] Compliance audit passed
- [ ] Data retention reviewed
- [ ] Security audit passed
- [ ] Documentation updated
- [ ] Training completed

---

## Quick Reference

### Essential Commands
```bash
# Create backup
python create_backup.py

# Restore backup (safe mode)
python restore_backup.py <filename> false

# Restore backup (overwrite mode)
python restore_backup.py <filename> true

# Test system
python test_backup_system.py

# Start scheduler (Windows)
.\start_backup_scheduler.ps1

# Start scheduler (Linux)
python3 backup_scheduler.py
```

### Files to Monitor
- `backups/` - Backup files
- Application logs - Errors and status
- Disk space - Storage capacity
- Redis memory - Data capacity

### Key Metrics
- Last backup age: < 24 hours
- Total backups: ~7 (or configured retention)
- Backup size: Consistent across backups
- Disk space: > 20% free

---

## Need Help?

- **Quick guide**: BACKUP_QUICKSTART.md
- **Full docs**: BACKUP_SYSTEM.md
- **Visual guide**: BACKUP_WORKFLOW.md
- **Test system**: `python test_backup_system.py`

---

*Print this checklist and keep it handy for regular backup operations!*
