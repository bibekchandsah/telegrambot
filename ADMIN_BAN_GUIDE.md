# Admin Quick Guide - Ban/Unban System

## Quick Command Reference

### Main Commands
```
/admin           - Show admin panel
/ban             - Ban a user
/unban           - Unban a user  
/warn            - Warn a user
/checkban        - Check if user is banned
/bannedlist      - View all banned users
/warninglist     - View all warned users
```

## How to Ban a User

### Step 1: Start Ban Command
```
/ban
```

### Step 2: Enter User ID
```
123456789
```

### Step 3: Select Reason
Choose from:
- 📵 Nudity / Explicit Content
- ⚠️ Spam
- 🚨 Abuse
- ❌ Fake Reports
- 😡 Harassment

### Step 4: Select Duration
- ⏰ 1 Hour
- ⏰ 24 Hours
- ⏰ 7 Days
- ⏰ 30 Days
- 🔒 Permanent

### Result
User is banned and both you and the user receive notifications.

## How to Unban a User

### Simple Process
```
/unban
123456789
```

System checks if user is banned, removes ban, and notifies the user.

## How to Warn a User

### Step 1: Start Warn Command
```
/warn
```

### Step 2: Enter User ID
```
123456789
```

### Step 3: Enter Reason
```
Sending inappropriate messages
```

### Result
Warning is recorded and user is notified.

## How to Check Ban Status

### Check Any User
```
/checkban 123456789
```

### Output Shows
- Ban status (banned/not banned)
- Reason for ban
- When banned
- When expires (if temporary)
- Time remaining
- Who banned them
- Warning count

## View Lists

### See All Banned Users
```
/bannedlist
```
Shows up to 20 banned users with reasons and types.

### See All Warned Users
```
/warninglist
```
Shows up to 20 warned users with warning counts.

## Auto-Ban System

### How It Works
- Users can report others with `/report`
- System tracks reports automatically
- After **5 reports**, user is **auto-banned for 7 days**
- You can check auto-banned users with `/checkban`

### Check Reports
1. Use `/checkban <user_id>` to see report count
2. Auto-ban is marked as "(Auto-ban)" in the status
3. You can manually extend or make permanent if needed

## Tips & Best Practices

### Before Banning
1. ✅ Check user's warning count
2. ✅ Review report history
3. ✅ Consider a warning first
4. ✅ Choose appropriate duration

### Choosing Duration
- **1 Hour**: Minor infractions (e.g., accidental spam)
- **24 Hours**: First-time violations (e.g., inappropriate language)
- **7 Days**: Repeated violations (e.g., continuous harassment)
- **30 Days**: Severe violations (e.g., explicit content sharing)
- **Permanent**: Extreme cases (e.g., repeated severe violations)

### Warning First
Consider using `/warn` before banning for:
- First-time offenders
- Minor rule violations
- Giving users a chance to improve

### Regular Checks
- Review `/bannedlist` weekly
- Check `/warninglist` for patterns
- Monitor auto-bans for false positives

## Common Scenarios

### Scenario 1: User Sharing Explicit Content
```
Action: Immediate ban
Duration: 30 days or Permanent
Reason: Nudity / Explicit Content

Steps:
/ban → Enter User ID → Select Nudity → Select 30 Days or Permanent
```

### Scenario 2: Spam Behavior
```
Action: Warning first, then ban if continues
Duration: 24 hours - 7 days
Reason: Spam

First Time:
/warn → Enter User ID → "Spam behavior"

If Continues:
/ban → Enter User ID → Select Spam → Select 24 Hours or 7 Days
```

### Scenario 3: User Harassment
```
Action: Immediate ban
Duration: 7 days - Permanent
Reason: Harassment

Steps:
/ban → Enter User ID → Select Harassment → Select 7 Days or Permanent
```

### Scenario 4: Fake Reports
```
Action: Warning first, then ban
Duration: 7 days
Reason: Fake Reports

First Time:
/warn → Enter User ID → "Submitting fake reports"

If Continues:
/ban → Enter User ID → Select Fake Reports → Select 7 Days
```

### Scenario 5: Check Multiple Reports
```
Steps:
1. /checkban 123456789
2. Review report count and warnings
3. If threshold reached, auto-ban already applied
4. Consider extending duration or making permanent
```

## Notifications

### What Users See

#### When Banned (Temporary)
```
🚫 You are temporarily banned

Reason: Spam
Ban expires: 2024-12-09 15:30:00

You cannot use the bot until the ban expires.
```

#### When Banned (Permanent)
```
🚫 You are permanently banned

Reason: Harassment

You cannot use the bot.
If you believe this is a mistake, please contact support.
```

#### When Warned
```
⚠️ You have received a warning

Reason: Inappropriate behavior
Total Warnings: 2

⚠️ Multiple warnings may result in a ban.
Please follow the rules to avoid further action.
```

#### When Unbanned
```
✅ Your ban has been lifted

You can now use the bot again.
Please follow the rules to avoid future bans.
```

### What You See

#### After Banning
```
✅ User Banned Successfully

User ID: 123456789
Reason: Spam
Duration: 7 Days
Banned by: Admin 987654321
```

#### After Unbanning
```
✅ User Unbanned Successfully

User ID: 123456789
Unbanned by: Admin 987654321
```

#### After Warning
```
⚠️ Warning Added Successfully

User ID: 123456789
Reason: Inappropriate content
Total Warnings: 2
Warned by: Admin 987654321
```

## Troubleshooting

### "User is not currently banned"
- Check user ID is correct
- User might have already been unbanned
- Temporary ban might have expired

### "Failed to ban user"
- Check Redis connection
- Verify user ID is valid
- Check logs for detailed error

### User Still Sending Messages
- Ban might not be applied yet
- Check with `/checkban <user_id>`
- User might be using cached session (will be blocked on next message)

### Auto-Ban Not Working
- Verify report count with `/checkban`
- Threshold is 5 reports
- Check logs for errors

## Advanced Tips

### Bulk Moderation
1. Keep a list of reported user IDs
2. Use `/checkban` on each
3. Apply bans in batch
4. Document decisions

### Pattern Recognition
1. Monitor `/warninglist` regularly
2. Look for users with multiple warnings
3. Track common violation types
4. Adjust policies accordingly

### Appeals Process
1. User contacts you
2. Check ban status: `/checkban <user_id>`
3. Review history and reason
4. Decide to maintain or lift ban
5. Use `/unban` if lifting

### Documentation
1. Keep notes on serious bans
2. Document reasoning for permanent bans
3. Track patterns and trends
4. Review policies periodically

## Quick Reference Card

```
┌─────────────────────────────────────────┐
│         BAN/UNBAN QUICK REFERENCE        │
├─────────────────────────────────────────┤
│ Ban User:      /ban                      │
│ Unban User:    /unban                    │
│ Warn User:     /warn                     │
│ Check Status:  /checkban <user_id>       │
│ View Bans:     /bannedlist               │
│ View Warnings: /warninglist              │
│                                          │
│ Auto-Ban:      5 reports = 7 day ban     │
│                                          │
│ Durations:                               │
│ • 1 Hour    - Minor                      │
│ • 24 Hours  - First violation            │
│ • 7 Days    - Repeated issues            │
│ • 30 Days   - Severe violation           │
│ • Permanent - Extreme cases              │
└─────────────────────────────────────────┘
```

## Support

Need help?
1. Check `/admin` for command list
2. Use `/checkban` to investigate issues
3. Review logs in `logs/` directory
4. Check `BAN_SYSTEM.md` for detailed documentation

---

**Quick Start**: Type `/admin` to see all available commands!
