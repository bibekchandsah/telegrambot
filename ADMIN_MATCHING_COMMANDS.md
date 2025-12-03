# Admin Matching Control Commands

## Overview
New Telegram bot commands for admins to control the matching system directly from the chat interface.

## Commands

### 🎯 Filter Control Commands

#### `/enablegender`
**Description**: Enable gender-based matching filter globally.

**Usage**: `/enablegender`

**Effect**: 
- Users will be matched based on their gender preferences
- Applies to all new matches going forward

**Example**:
```
Admin: /enablegender
Bot: ✅ Gender Filter Enabled
     
     👫 Users will now be matched based on their gender preferences.
     
     This affects all new matches going forward.
```

---

#### `/disablegender`
**Description**: Disable gender-based matching filter globally.

**Usage**: `/disablegender`

**Effect**: 
- Gender preferences will be IGNORED during matching
- Users can match with any gender regardless of their preferences
- Applies to all new matches going forward

**Example**:
```
Admin: /disablegender
Bot: ✅ Gender Filter Disabled
     
     👫 Gender preferences will be IGNORED during matching.
     Users can now match with any gender regardless of preferences.
     
     ⚠️ This affects all new matches going forward.
```

---

#### `/enableregional`
**Description**: Enable regional (country-based) matching filter globally.

**Usage**: `/enableregional`

**Effect**: 
- Users will be matched based on their country preferences
- Applies to all new matches going forward

**Example**:
```
Admin: /enableregional
Bot: ✅ Regional Filter Enabled
     
     🌍 Users will now be matched based on their country preferences.
     
     This affects all new matches going forward.
```

---

#### `/disableregional`
**Description**: Disable regional (country-based) matching filter globally.

**Usage**: `/disableregional`

**Effect**: 
- Country preferences will be IGNORED during matching
- Users can match internationally regardless of their preferences
- Applies to all new matches going forward

**Example**:
```
Admin: /disableregional
Bot: ✅ Regional Filter Disabled
     
     🌍 Country preferences will be IGNORED during matching.
     Users can now match internationally regardless of preferences.
     
     ⚠️ This affects all new matches going forward.
```

---

### 🔧 Matching Operations

#### `/forcematch`
**Description**: Manually pair two specific users, bypassing all filters and queue logic.

**Usage**: `/forcematch <user1_id> <user2_id>`

**Arguments**:
- `user1_id`: Telegram user ID of first user (numeric)
- `user2_id`: Telegram user ID of second user (numeric)

**Validation**:
- Users must have different IDs (cannot match user with themselves)
- Both users must exist in the system
- Neither user can already be in a chat

**Effect**:
- Creates bidirectional pair mapping
- Updates both users' states to IN_CHAT
- Removes both from queue if present
- Sends special notification to both users
- Initializes activity timestamps
- Logs the action for moderation

**Example**:
```
Admin: /forcematch 123456789 987654321
Bot: ✅ Force Match Successful
     
     👥 Matched Users:
     • User 1: 123456789 (was IN_QUEUE)
     • User 2: 987654321 (was IDLE)
     
     Both users have been notified with a special message.
     They can now chat with each other.
```

**User Notification**:
Both users receive this special message:
```
✨ 🎉 Special Match Found! 🎉 ✨

You've been specially matched with someone amazing! 
This is a unique connection just for you. 

💬 Start chatting now and enjoy your conversation! 💫

Use /next to find a new partner or /stop to end the chat.
```

**Error Messages**:
- `❌ Cannot match a user with themselves.`
- `❌ User {id} not found or has no state.`
- `❌ User {id} is already in a chat.`
- `❌ Invalid user ID format. Please use numeric IDs.`

---

#### `/matchstatus`
**Description**: View current matching system status and available commands.

**Usage**: `/matchstatus`

**Shows**:
- Gender filter status (Enabled/Disabled)
- Regional filter status (Enabled/Disabled)
- Current queue size (number of waiting users)
- List of all matching control commands

**Example**:
```
Admin: /matchstatus
Bot: 📊 Matching System Status
     
     Filters:
     👫 Gender Filter: ✅ Enabled
     🌍 Regional Filter: ✅ Enabled
     
     Queue:
     📋 Waiting Users: 5
     
     Commands:
     • /enablegender - Enable gender filter
     • /disablegender - Disable gender filter
     • /enableregional - Enable regional filter
     • /disableregional - Disable regional filter
     • /forcematch <id1> <id2> - Force match users
     • /matchstatus - Show this status
```

---

## Use Cases

### 1. Testing Match Behavior
Disable filters to test matching logic without restrictions:
```
/disablegender
/disableregional
```

### 2. Special Events
Enable international matching for global events:
```
/disableregional
```

### 3. Debugging User Issues
Force match two users to test chat functionality:
```
/forcematch 123456 789012
```

### 4. VIP Matching
Create special matches for VIP users or promotional events:
```
/forcematch 111111 222222
```

### 5. Check System Status
Monitor current filter settings and queue:
```
/matchstatus
```

---

## Integration with Dashboard

These commands complement the web-based admin dashboard:
- **Dashboard**: Visual interface at `http://localhost:5000`
- **Bot Commands**: Quick access from Telegram chat
- **Both sync**: Changes made in either place reflect in both

**When to use dashboard**:
- Complex filter management
- Viewing detailed statistics
- Bulk operations
- Visual monitoring

**When to use bot commands**:
- Quick filter toggles
- Emergency actions
- On-the-go management
- Simple status checks

---

## Redis Keys

These commands interact with Redis:

### Filter Settings
- `matching:gender_filter_enabled`: "1" (enabled) or "0" (disabled)
- `matching:regional_filter_enabled`: "1" (enabled) or "0" (disabled)

### Queue Data
- `queue:waiting`: Redis list of waiting user IDs

### Pair Mappings
- `pair:{user_id}`: Partner user ID (bidirectional)

### State Management
- `state:{user_id}`: User state (IDLE, IN_QUEUE, IN_CHAT)

### Activity Tracking
- `chat:activity:{user_id}`: Last activity timestamp

---

## Logging

All matching control actions are logged:

```python
# Filter changes
logger.info("gender_filter_enabled", admin_id=user_id)
logger.info("gender_filter_disabled", admin_id=user_id)
logger.info("regional_filter_enabled", admin_id=user_id)
logger.info("regional_filter_disabled", admin_id=user_id)

# Force matches
logger.info("force_match_executed",
    admin_id=user_id,
    user1_id=user1_id,
    user2_id=user2_id,
    user1_previous_state=user1_state,
    user2_previous_state=user2_state
)
```

---

## Security & Permissions

### Admin-Only Access
All matching control commands require admin permissions:
- Checked via `AdminManager.is_admin(user_id)`
- Non-admins receive: "⛔ You don't have permission to use this command."

### Admin List
Admins are defined in:
- `src/config.py` → `ADMIN_IDS`
- Environment variable: `ADMIN_IDS` (comma-separated)

### Add Admin
```python
# config.py or .env
ADMIN_IDS=123456789,987654321
```

---

## Best Practices

### 1. **Always Check Status First**
Before making changes:
```
/matchstatus
```

### 2. **Use Force Match Sparingly**
Only for:
- Debugging
- Testing
- VIP/promotional matches
- Emergency situations

### 3. **Document Filter Changes**
When disabling filters:
- Announce to users if permanent
- Set a timeline for temporary changes
- Monitor impact on match quality

### 4. **Test on Staging First**
Test matching control commands on development/staging before production.

### 5. **Monitor Logs**
Watch logs for:
- Filter change patterns
- Force match frequency
- Error rates
- User complaints

---

## Troubleshooting

### Issue: Filter changes not applying
**Solution**: 
- Check Redis connection: `redis-cli ping`
- Verify keys exist: `redis-cli GET matching:gender_filter_enabled`
- Restart bot if needed

### Issue: Force match fails
**Solution**:
- Verify user IDs are correct
- Check users aren't already in chat: `/stats`
- Ensure users have states in Redis

### Issue: Commands not responding
**Solution**:
- Verify admin permissions
- Check bot logs for errors
- Restart bot service

---

## Related Documentation

- **Full Feature Guide**: `MATCHING_CONTROL_FEATURE.md`
- **Dashboard Guide**: `ADMIN_DASHBOARD.md`
- **Bot Commands**: Use `/admin` in Telegram
- **Test Suite**: `test_matching_control.py`

---

## Quick Reference

| Command | Description | Usage |
|---------|-------------|-------|
| `/enablegender` | Enable gender filter | `/enablegender` |
| `/disablegender` | Disable gender filter | `/disablegender` |
| `/enableregional` | Enable regional filter | `/enableregional` |
| `/disableregional` | Disable regional filter | `/disableregional` |
| `/forcematch` | Force match two users | `/forcematch 123 456` |
| `/matchstatus` | Show system status | `/matchstatus` |

---

## Implementation Files

- **Commands**: `src/handlers/commands.py` (lines 4074-4495)
- **Bot Registration**: `src/bot.py` (lines 85-92, 428-435)
- **Matching Engine**: `src/services/matching.py` (lines 208-256)
- **Dashboard Backend**: `admin_dashboard.py` (lines 1300-1456)

---

**Status**: ✅ Fully Implemented and Tested
**Version**: 1.0
**Last Updated**: December 3, 2025
