# Web Dashboard Moderation Guide

This guide explains how to use the web dashboard's moderation features to manage user bans, warnings, and violations.

## Overview

The web dashboard provides a comprehensive moderation interface that mirrors the bot's command-based moderation system. Administrators can perform all moderation tasks through an intuitive web interface.

## Accessing the Moderation Panel

1. Start the dashboard:
   ```bash
   python admin_dashboard.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

3. Click on the **"Moderation"** tab in the navigation bar

## Features

### 1. Ban User

Ban a user from the platform with a specific reason and duration.

**How to Use:**
1. Enter the **User ID** of the user to ban
2. Select a **Reason** from the dropdown:
   - Nudity/Sexual Content
   - Spam/Advertising
   - Verbal Abuse/Harassment
   - Fake Reports
   - Persistent Harassment
3. Select a **Duration**:
   - 1 Hour
   - 24 Hours
   - 7 Days
   - 30 Days
   - Permanent
4. Click **"🚫 Ban User"**

**What Happens:**
- User is immediately banned from the platform
- Ban is logged with timestamp and admin ID
- User cannot send/receive messages or join queue
- Ban history is saved for reference

### 2. Unban User

Remove a ban from a user, allowing them to use the platform again.

**How to Use:**
1. Enter the **User ID** of the banned user
2. Click **"✅ Unban User"**

**What Happens:**
- User's ban is immediately removed
- User can access all platform features again
- Unban action is logged in the system

### 3. Warn User

Issue a warning to a user for minor violations.

**How to Use:**
1. Enter the **User ID** of the user to warn
2. Enter a **Warning Reason** (free text)
3. Click **"⚠️ Issue Warning"**

**What Happens:**
- Warning is added to user's record
- Warning count increases
- Warning is logged with timestamp and reason
- User is notified via bot (if implemented)

**Note:** Users with 3+ warnings may be candidates for temporary bans.

### 4. Check Ban Status

Check if a specific user is currently banned and view ban details.

**How to Use:**
1. Enter the **User ID** to check
2. Click **"🔍 Check Status"**

**Results Display:**
- **If Banned:**
  - User ID
  - Ban reason
  - Duration
  - Banned at (timestamp)
  - Expires at (timestamp or "Permanent")
  - Banned by (admin ID)
  - Auto-ban indicator (if auto-banned)
  
- **If Not Banned:**
  - Confirmation that user is not banned

### 5. Banned Users List

View all currently banned users with detailed information.

**How to Use:**
1. Click **"🔄 Refresh"** to load the list

**Displayed Information:**
- User ID
- Ban reason
- Duration
- Banned at (timestamp)
- Expires at (timestamp or "Permanent")
- Banned by (admin ID)
- Quick unban action button

**Quick Actions:**
- Click **"Unban"** button in any row to immediately unban that user

### 6. Warned Users List

View all users who have received warnings.

**How to Use:**
1. Click **"🔄 Refresh"** to load the list

**Displayed Information:**
- User ID
- Warning count
- View details button (links to user profile)

## Ban Reasons Explained

### Nudity/Sexual Content
- Sharing inappropriate sexual content
- Sending nude photos or videos
- Requesting sexual content from others

**Recommended Duration:** 7 days - Permanent

### Spam/Advertising
- Sending promotional messages
- Advertising products/services
- Bot-like behavior
- Repetitive messages

**Recommended Duration:** 24 hours - 7 days

### Verbal Abuse/Harassment
- Using offensive language
- Insulting or threatening others
- Hate speech
- Discriminatory behavior

**Recommended Duration:** 7 days - 30 days

### Fake Reports
- Reporting users without valid reason
- Abusing the report system
- False accusations

**Recommended Duration:** 7 days - 30 days

### Persistent Harassment
- Continuing to harass after warnings
- Stalking behavior
- Repeated violations after previous bans

**Recommended Duration:** 30 days - Permanent

## Auto-Ban System

The system automatically bans users who are reported 5 or more times:

- **Trigger:** 5 reports from different users
- **Duration:** 7 days automatic ban
- **Reason:** Auto-assigned based on report patterns
- **Indicator:** Shows as "Auto-banned" in ban status
- **Can be unbanned:** Yes, admins can manually unban if reports were false

## API Endpoints Used

The dashboard uses these REST API endpoints:

### POST /api/moderation/ban
Ban a user
```json
{
  "user_id": 123456789,
  "reason": "spam",
  "duration": "7d"
}
```

### POST /api/moderation/unban
Unban a user
```json
{
  "user_id": 123456789
}
```

### POST /api/moderation/warn
Warn a user
```json
{
  "user_id": 123456789,
  "reason": "Inappropriate language"
}
```

### GET /api/moderation/check-ban/{user_id}
Check if user is banned

### GET /api/moderation/banned-users
Get list of all banned users

### GET /api/moderation/warned-users
Get list of all warned users

## Best Practices

### When to Ban vs Warn

**Use Warnings For:**
- First-time minor violations
- Accidental rule breaks
- Behavior that can be corrected
- Users with good history

**Use Temporary Bans For:**
- Repeated warnings ignored
- Moderate violations
- Need to cool down situation
- Pattern of minor violations

**Use Permanent Bans For:**
- Severe violations (illegal content)
- Persistent harassment
- Multiple ban evasions
- Threats of violence
- Sharing personal information

### Investigation Tips

Before banning a user:
1. Check their profile in the "All Users" tab
2. Review their chat/message count
3. Check if they have previous warnings
4. Look at report history (if available)
5. Verify the violation evidence

### Ban Duration Guidelines

- **1 Hour:** Very minor first-time violations
- **24 Hours:** Minor violations, cooling off period
- **7 Days:** Moderate violations, repeated warnings
- **30 Days:** Serious violations, multiple infractions
- **Permanent:** Severe violations, repeated bans

### Communication

After taking moderation action:
1. Document the reason clearly
2. Users are notified via bot when banned
3. Consider sending a warning message before banning
4. Keep records of moderation decisions

## Troubleshooting

### User Not Found
- Verify the User ID is correct
- Check if user has ever used the bot
- User may have deleted their Telegram account

### Ban Not Working
- Check Redis connection
- Verify admin permissions
- Check browser console for errors
- Ensure API endpoint is accessible

### Dashboard Not Loading
1. Verify dashboard is running: `python admin_dashboard.py`
2. Check console for errors
3. Ensure port 5000 is not in use
4. Check Redis is running and connected

### Changes Not Reflecting in Bot
- Redis acts as real-time database
- Changes should be instant
- User may need to send a new message
- Try unbanning and rebanning if issue persists

## Security Notes

- Only authorized admins should have dashboard access
- Always verify ban reasons before taking action
- Keep admin credentials secure
- Monitor for abuse of moderation powers
- Log all moderation actions for accountability

## Related Documentation

- `BAN_SYSTEM.md` - Complete ban system overview
- `ADMIN_BAN_GUIDE.md` - Bot command-based moderation
- `DASHBOARD_QUICKSTART.md` - Dashboard setup guide
- `ADMIN_DASHBOARD.md` - General dashboard features

## Support

If you encounter issues with the moderation system:
1. Check the console logs for errors
2. Verify Redis is running
3. Review this documentation
4. Check the bot's admin command equivalents
5. Restart both bot and dashboard if needed
