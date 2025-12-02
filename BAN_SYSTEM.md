# Ban / Unban System Documentation

## Overview
The ban/unban system provides comprehensive moderation tools for administrators to manage user behavior and maintain a safe community environment.

## Features

### 1. Ban Users (Temporary/Permanent)
Administrators can ban users with flexible duration options:

**Command**: `/ban`

**Process**:
1. Admin enters user ID to ban
2. Selects ban reason from predefined options
3. Chooses ban duration (1 hour, 24 hours, 7 days, 30 days, or permanent)
4. System executes ban and notifies the user

**Ban Reasons**:
- 📵 **Nudity / Explicit Content** - Sharing inappropriate content
- ⚠️ **Spam** - Sending repetitive or unwanted messages
- 🚨 **Abuse** - Abusive behavior or language
- ❌ **Fake Reports** - Submitting false reports
- 😡 **Harassment** - Harassing other users

**Effects**:
- User cannot send messages
- User cannot join chat queue
- User receives ban notification with reason and duration
- Ban data stored in Redis with automatic expiry for temporary bans

### 2. Unban Users
Administrators can remove bans and restore user access:

**Command**: `/unban`

**Process**:
1. Admin enters user ID to unban
2. System checks if user is actually banned
3. Removes ban and notifies the user
4. Records unban in history

**Effects**:
- Ban is removed from system
- User can use bot normally
- User receives notification about unban

### 3. Warning System
Issue warnings to users without banning them:

**Command**: `/warn`

**Process**:
1. Admin enters user ID to warn
2. Admin provides warning reason
3. System records warning and notifies user
4. Warning counter is incremented

**Effects**:
- User receives warning notification
- Warning count is tracked
- User is added to warning list
- Multiple warnings may lead to future action

### 4. Auto-Ban from Reports
Automatic moderation based on user reports:

**Threshold**: 5 reports

**Process**:
1. Users report problematic behavior using `/report`
2. System tracks report count per user
3. When threshold is reached, user is automatically banned
4. Auto-ban is temporary (7 days)
5. System logs auto-ban event

**Features**:
- Prevents abuse without manual intervention
- Gives users a second chance with temporary ban
- Can be reviewed by admins

### 5. Check Ban Status
Query ban information for any user:

**Command**: `/checkban <user_id>`

**Example**: `/checkban 123456789`

**Information Displayed**:
- Ban status (banned/not banned)
- Ban reason
- Ban date and time
- Expiry date (for temporary bans)
- Remaining time
- Who issued the ban
- Auto-ban indicator
- Warning count (if not banned)

### 6. View Banned Users List
Get overview of all currently banned users:

**Command**: `/bannedlist`

**Display**:
- Total count of banned users
- List of up to 20 users with details:
  - User ID
  - Ban reason
  - Duration type (Permanent/Temporary)
  - Auto-ban indicator
- Overflow indicator if more than 20 users

### 7. View Warning List
See all users currently on warning list:

**Command**: `/warninglist`

**Display**:
- Total count of warned users
- List of up to 20 users with:
  - User ID
  - Number of warnings
- Overflow indicator if more than 20 users

## Admin Commands Summary

| Command | Description | Permission |
|---------|-------------|------------|
| `/admin` | Show admin panel with all commands | Admin only |
| `/ban` | Ban a user (temporary/permanent) | Admin only |
| `/unban` | Unban a user | Admin only |
| `/warn` | Add warning to user | Admin only |
| `/checkban <user_id>` | Check ban status | Admin only |
| `/bannedlist` | View all banned users | Admin only |
| `/warninglist` | View users on warning list | Admin only |

## Data Storage

### Redis Keys Used

**Ban Information**:
- `ban:{user_id}` - Current ban data (auto-expires for temporary bans)
- `ban_history:{user_id}` - Historical ban records (last 50)
- `unban_history:{user_id}` - Historical unban records (last 50)
- `bot:banned_users` - Set of all currently banned user IDs

**Warning Information**:
- `warnings:{user_id}` - Warning records (last 100)
- `warning_count:{user_id}` - Total warning count
- `bot:warning_list` - Set of all warned user IDs

**Report Information**:
- `stats:{user_id}:reports` - Report records (last 50)
- `stats:{user_id}:report_count` - Total report count

### Ban Data Structure
```json
{
  "user_id": 123456789,
  "banned_by": 987654321,
  "reason": "spam",
  "banned_at": 1701234567,
  "expires_at": 1701838367,
  "is_permanent": false,
  "is_auto_ban": false
}
```

### Warning Data Structure
```json
{
  "user_id": 123456789,
  "warned_by": 987654321,
  "reason": "Inappropriate behavior",
  "warned_at": 1701234567
}
```

## User Experience

### When Banned
Users receive clear notifications:

**Temporary Ban**:
```
🚫 You are temporarily banned

Reason: Spam
Ban expires: 2024-12-09 15:30:00

You cannot use the bot until the ban expires.
```

**Permanent Ban**:
```
🚫 You are permanently banned

Reason: Harassment

You cannot use the bot.
If you believe this is a mistake, please contact support.
```

### When Warned
```
⚠️ You have received a warning

Reason: Sending inappropriate content
Total Warnings: 2

⚠️ Multiple warnings may result in a ban.
Please follow the rules to avoid further action.
```

### When Unbanned
```
✅ Your ban has been lifted

You can now use the bot again.
Please follow the rules to avoid future bans.
```

## Ban Enforcement

### Message Handler
- All messages are checked for ban status
- Banned users receive ban notification
- Messages from banned users are blocked

### Chat Command
- Users are checked before joining queue
- Banned users cannot start chats
- Clear error message with ban details

### Automatic Expiry
- Temporary bans use Redis TTL
- Expired bans are automatically removed
- No manual cleanup required

## Best Practices

### For Admins

1. **Choose Appropriate Duration**:
   - 1 hour: Minor infractions
   - 24 hours: First-time serious violations
   - 7 days: Repeated violations
   - 30 days: Severe violations
   - Permanent: Extreme cases or repeat offenders

2. **Use Warnings First**:
   - Issue warnings before banning
   - Give users chance to improve
   - Document behavior patterns

3. **Review Auto-Bans**:
   - Check auto-banned users periodically
   - Verify legitimacy of reports
   - Extend ban if necessary

4. **Keep Records**:
   - Note patterns of behavior
   - Track repeat offenders
   - Use `/checkban` before decisions

### For System Maintenance

1. **Monitor Ban List**:
   - Review `/bannedlist` regularly
   - Clean up expired bans manually if needed
   - Track statistics

2. **Review Warning List**:
   - Check `/warninglist` for patterns
   - Convert warnings to bans if needed
   - Reset warnings for reformed users

3. **Report Threshold**:
   - Adjust AUTO_BAN_THRESHOLD if needed
   - Currently set to 5 reports
   - Can be modified in `admin.py`

## Integration with Other Systems

### Profile System
- Banned users can still view their profile
- Cannot edit profile while banned
- Profile remains intact after unban

### Rating System
- Ratings remain recorded
- Cannot rate partners while banned
- Historical ratings preserved

### Matching System
- Banned users removed from queue
- Active chats terminated
- Partners notified of termination

## Security Considerations

1. **Admin-Only Access**: All ban commands require admin privileges
2. **User Notification**: Users are informed about bans and reasons
3. **Audit Trail**: All bans/unbans are logged with admin ID
4. **Automatic Protection**: Auto-ban prevents abuse
5. **Data Persistence**: Ban history maintained for reference

## Troubleshooting

### Ban Not Working
- Verify user ID is correct
- Check Redis connection
- Review logs for errors
- Confirm admin permissions

### User Still Active After Ban
- Check if ban was recorded: `/checkban <user_id>`
- Verify Redis key exists: `ban:{user_id}`
- User might be using cached session (will be blocked on next message)

### Auto-Ban Not Triggering
- Verify report count: Check `stats:{user_id}:report_count`
- Confirm threshold setting (default: 5)
- Check logs for auto-ban events

### Temporary Ban Not Expiring
- Redis TTL might not be set correctly
- Manual cleanup: Use `/unban` command
- Check Redis expiry: `TTL ban:{user_id}`

## Future Enhancements

Potential improvements for the ban system:

1. **Appeal System**: Allow users to appeal bans
2. **Ban Reasons Customization**: Add custom ban reasons
3. **Scheduled Unbans**: Schedule automatic unbans
4. **Ban Templates**: Predefined ban configurations
5. **Reporting Categories**: More specific report types
6. **Analytics Dashboard**: Ban statistics and trends
7. **Bulk Operations**: Ban/unban multiple users
8. **IP Bans**: Additional layer of protection
9. **Shadow Ban**: Soft ban for investigation
10. **Timeout**: Short-term muting instead of full ban

## Configuration

### Admin IDs
Set admin user IDs in `.env`:
```env
ADMIN_IDS=123456789,987654321
```

### Auto-Ban Threshold
Modify in `src/services/admin.py`:
```python
AUTO_BAN_THRESHOLD = 5  # Number of reports to trigger auto-ban
```

### Auto-Ban Duration
Modify in `src/services/admin.py`:
```python
duration=604800,  # 7 days in seconds
```

## Support

For issues or questions about the ban system:
1. Check logs in `logs/` directory
2. Review Redis data with Redis CLI
3. Test with `/checkban` command
4. Contact system administrator

---

**Last Updated**: December 2024  
**Version**: 1.0.0  
**Maintainer**: System Administrator
