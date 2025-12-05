# Data Management Guide

## Overview
The Data Management tab in the Admin Dashboard provides powerful tools to clean up and manage Redis database data. These features help maintain database health and remove unwanted data.

⚠️ **IMPORTANT**: Always create a backup before performing any deletion operations!

---

## Features

### 📊 Database Statistics
View real-time statistics about your database:
- Total users, profiles, active users
- Queue and chat statistics
- Reports count
- Cache entries
- Banned and warned users
- Bad words and blocked media types
- Moderation logs count

**Refresh stats** regularly to monitor your database health.

---

## Deletion Operations

### 1. 👤 Delete User Data
**Purpose**: Remove all data for a specific user

**What gets deleted**:
- User profile
- Preferences
- Chat history
- Activity records
- All associated data

**Usage**:
1. Enter the User ID
2. Click "Delete User Data"
3. Confirm the action

**Warning**: This action cannot be undone!

---

### 2. 💬 Delete Chat History
**Purpose**: Remove only chat history for a user (keeps profile)

**What gets deleted**:
- Chat history records only

**What's kept**:
- User profile
- Preferences
- Other user data

**Usage**:
1. Enter the User ID
2. Click "Delete Chat History"
3. Confirm the action

---

### 3. 📋 Manage Reports

#### Delete Individual Report
Remove a specific user's report:
1. Enter the User ID
2. Click "Delete This Report"

#### Delete Old Reports
Remove reports older than X days:
1. Set the number of days (default: 30)
2. Click "Delete Old Reports"
3. Reports older than specified days will be deleted

#### Delete ALL Reports (Danger Zone)
Remove all user reports from the database:
1. Click "Delete ALL Reports"
2. Confirm TWICE (double confirmation required)
3. All reports will be permanently deleted

**Use cases**:
- Clean up old resolved reports
- Start fresh with report system
- Remove spam reports

---

### 4. 😴 Delete Inactive Users
**Purpose**: Remove users who haven't been active for X days

**Default**: 90 days

**What gets deleted**:
- All data for users inactive for specified period
- Helps maintain a clean active user base

**Usage**:
1. Set the number of inactive days (minimum: 30)
2. Click "Delete Inactive Users"
3. Confirm the action

**Warning**: This is a bulk operation affecting multiple users!

---

### 5. 🗑️ Delete Banned Users List
**Purpose**: Clear the entire ban list

**What happens**:
- All ban records are removed
- Previously banned users can use the bot again
- Individual bans or bulk clear available

**Usage**:
- **Bulk**: Go to Moderation tab → "Clear All Bans"
- **Individual**: Select ban record → "Delete"

**Use cases**:
- Second chance policies
- Reset moderation system
- Remove expired bans

---

### 6. ⚠️ Delete Warned Users List
**Purpose**: Clear warning records

**What happens**:
- All warning records are removed
- Fresh start for warned users

**Usage**:
- **Bulk**: Go to Moderation tab → "Clear All Warnings"
- **Individual**: Select warning → "Delete"

---

### 7. 🚫 Clear Blocked Media Types
**Purpose**: Remove all media type restrictions

**What happens**:
- All blocked media types are cleared
- Users can send all media types until you set restrictions again

**Usage**:
1. Click "Clear Blocked Media"
2. Confirm the action

**Warning**: This removes all media restrictions!

---

### 8. 🔤 Clear Bad Words List
**Purpose**: Remove all bad words from content filter

**What happens**:
- Bad word filtering is disabled
- Users can use any words until list is rebuilt

**Usage**:
1. Click "Clear Bad Words"
2. Confirm the action

**Warning**: Content filtering will be disabled!

---

### 9. 📜 Clear Moderation Logs
**Purpose**: Remove moderation action logs (audit trail)

**Options**:
- **Delete All**: Set "Days to Keep" to 0
- **Delete Old**: Specify days to keep recent logs

**What gets deleted**:
- Moderation action records
- Admin activity logs
- Audit trail entries

**Usage**:
1. Set "Days to Keep" (0 = delete all)
2. Click "Clear Logs"
3. Confirm the action (double confirmation for delete all)

**Critical Warning**: 
- ⚠️ You will lose your audit trail!
- ⚠️ Cannot recover deleted logs!
- ⚠️ Make backup first!

**Best practice**: Keep at least 30-90 days of logs for auditing

---

### 10. 🧹 Clear Cache
**Purpose**: Remove temporary cache data

**What gets deleted**:
- Activity timestamps
- Temporary sessions
- Cache entries

**What's safe**:
- User data is NOT affected
- Profiles remain intact
- Chat history is preserved

**Usage**:
1. Click "Clear Cache"
2. Confirm the action

✅ **Safe operation** - No permanent data loss

---

## Best Practices

### Before Deletion
1. ✅ **Create a backup** in the Backups tab
2. ✅ Check database statistics to understand impact
3. ✅ Test on development environment first
4. ✅ Verify user IDs before individual deletions
5. ✅ Read the warnings carefully

### During Deletion
1. ⚠️ Read all confirmation prompts
2. ⚠️ Double-check IDs and parameters
3. ⚠️ Understand what will be deleted
4. ⚠️ Don't skip confirmations

### After Deletion
1. 📊 Refresh statistics to verify changes
2. 💾 Keep backups for at least 30 days
3. 📝 Document what was deleted and why
4. 🔍 Monitor for any issues

---

## Safety Features

### Double Confirmations
High-risk operations require double confirmation:
- Delete ALL reports
- Delete ALL moderation logs
- Delete inactive users (bulk operation)

### Warning Messages
Color-coded warnings:
- 🔴 **Red (Danger)**: Irreversible, high-impact operations
- 🟡 **Yellow (Warning)**: Moderate risk, review carefully
- 🔵 **Blue (Info)**: Safe operations, low risk

### Moderation Logging
All deletion actions are logged (except when clearing logs):
- Who performed the action
- What was deleted
- When it happened
- Affected user IDs

---

## Common Scenarios

### Scenario 1: Database Cleanup
**Goal**: Remove old, inactive data

**Steps**:
1. Create backup
2. Check statistics
3. Delete inactive users (90+ days)
4. Delete old reports (30+ days)
5. Clear cache
6. Verify statistics

### Scenario 2: User Data Removal Request
**Goal**: GDPR compliance - delete specific user data

**Steps**:
1. Create backup
2. Note user ID
3. Use "Delete User Data" feature
4. Verify deletion in statistics
5. Log the request fulfillment

### Scenario 3: Reset Moderation System
**Goal**: Fresh start with bans/warnings

**Steps**:
1. Create backup
2. Clear all warnings
3. Clear all bans
4. Optionally clear moderation logs
5. Document the reset

### Scenario 4: Content Filter Update
**Goal**: Rebuild bad words list

**Steps**:
1. Export current bad words (if needed)
2. Clear bad words list
3. Add new bad words through bot commands
4. Test filtering

---

## Emergency Recovery

### If Something Goes Wrong

1. **Stop immediately**: Don't perform more deletions
2. **Check backups**: Go to Backups tab
3. **Download latest backup**: Before the deletion
4. **Contact support**: If you need help restoring

### Prevention

- 💾 Enable automatic daily backups
- ☁️ Use GitHub cloud storage for backups
- 🔄 Keep at least 7 days of backups
- 📋 Test backup restoration regularly

---

## API Endpoints

For developers integrating with the dashboard:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/data/stats` | GET | Get database statistics |
| `/api/data/delete-user` | POST | Delete specific user data |
| `/api/data/delete-chat-history` | POST | Delete user chat history |
| `/api/data/delete-all-reports` | POST | Delete all reports |
| `/api/data/delete-single-report` | POST | Delete specific report |
| `/api/data/delete-old-reports` | POST | Delete reports by age |
| `/api/data/delete-inactive-users` | POST | Delete inactive users |
| `/api/data/delete-banned-users` | POST | Clear ban list |
| `/api/data/delete-warned-users` | POST | Clear warning list |
| `/api/data/delete-single-ban` | POST | Delete specific ban |
| `/api/data/delete-single-warning` | POST | Delete specific warning |
| `/api/data/clear-blocked-media` | POST | Clear blocked media |
| `/api/data/clear-bad-words` | POST | Clear bad words |
| `/api/data/clear-moderation-logs` | POST | Clear moderation logs |
| `/api/data/clear-cache` | POST | Clear temporary cache |

All POST endpoints require authentication and admin privileges.

---

## Troubleshooting

### Issue: "Error: Failed to delete data"
**Solutions**:
- Check Redis connection
- Verify admin authentication
- Check server logs
- Ensure user ID exists

### Issue: "Statistics not updating"
**Solutions**:
- Click "Refresh Stats"
- Check Redis connection
- Reload dashboard page

### Issue: "Cannot delete user"
**Solutions**:
- Verify user ID is correct
- Check if user is currently active
- Try again in a few minutes
- Check Redis for locks

---

## Technical Details

### Redis Key Patterns Affected

- `user:{user_id}:*` - User data
- `profile:{user_id}` - User profiles
- `chat_history:*` - Chat history
- `report:*` - User reports
- `ban:{user_id}` - Ban records
- `warning:{user_id}` - Warning records
- `blocked_media:*` - Blocked media types
- `bad_words` - Bad words set
- `moderation_logs` - Moderation logs
- `activity:*` - Activity timestamps
- `cache:*` - Temporary cache

---

## Support

For issues or questions:
1. Check server logs: `admin_dashboard.py` and `bot.py`
2. Review Redis data directly if needed
3. Check GitHub backup repository
4. Refer to main documentation files

---

## Related Documentation

- `ADMIN_DASHBOARD.md` - Main dashboard documentation
- `BACKUP_SYSTEM.md` - Backup system details
- `ADMIN_BAN_GUIDE.md` - Ban system documentation
- `WEB_DASHBOARD_MODERATION.md` - Moderation features

---

**Last Updated**: December 2024  
**Dashboard Version**: 2.0  
**Feature Status**: Production Ready ✅
