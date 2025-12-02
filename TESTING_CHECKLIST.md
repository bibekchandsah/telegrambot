# Testing Checklist - Ban/Unban System

## Pre-Testing Setup

### Prerequisites
- [ ] Bot is running
- [ ] Redis is connected
- [ ] Admin IDs configured in `.env`
- [ ] Test user accounts available

### Environment Variables
```env
BOT_TOKEN=your_bot_token_here
REDIS_URL=redis://localhost:6379
ADMIN_IDS=your_admin_id_here
```

---

## Test Cases

### 1. Ban System Tests

#### 1.1 Basic Ban Flow
- [ ] Admin runs `/ban` command
- [ ] System prompts for user ID
- [ ] Admin enters valid user ID
- [ ] System shows ban reason options
- [ ] Admin selects reason
- [ ] System shows duration options
- [ ] Admin selects duration
- [ ] System confirms ban
- [ ] Banned user receives notification
- [ ] Ban is stored in Redis

**Expected Result**: User is banned successfully with proper notifications

#### 1.2 Temporary Ban (1 Hour)
- [ ] Ban user for 1 hour
- [ ] Check ban status with `/checkban`
- [ ] Verify expiry time is correct
- [ ] Wait 1 hour or manually delete Redis key
- [ ] Verify ban auto-expires
- [ ] User can use bot after expiry

**Expected Result**: Temporary ban expires automatically

#### 1.3 Permanent Ban
- [ ] Ban user permanently
- [ ] Check ban status shows "Permanent"
- [ ] Ban does not expire
- [ ] Only manual unban removes it

**Expected Result**: Permanent ban remains until manually removed

#### 1.4 Each Ban Reason
Test all 5 reasons:
- [ ] Nudity / Explicit Content
- [ ] Spam
- [ ] Abuse
- [ ] Fake Reports
- [ ] Harassment

**Expected Result**: All reasons work correctly

#### 1.5 Invalid User ID
- [ ] Enter invalid user ID (letters/symbols)
- [ ] System shows error message
- [ ] Can retry with valid ID

**Expected Result**: Validation works, clear error message

### 2. Unban System Tests

#### 2.1 Basic Unban Flow
- [ ] Ban a user first
- [ ] Admin runs `/unban` command
- [ ] Admin enters banned user ID
- [ ] System validates user is banned
- [ ] Ban is removed
- [ ] User receives notification
- [ ] User can use bot again

**Expected Result**: Unban works correctly

#### 2.2 Unban Non-Banned User
- [ ] Try to unban user who isn't banned
- [ ] System shows "not currently banned"

**Expected Result**: Proper validation message

#### 2.3 Unban History
- [ ] Unban a user
- [ ] Check unban is recorded in history
- [ ] History includes admin ID and timestamp

**Expected Result**: History is maintained

### 3. Warning System Tests

#### 3.1 Basic Warning Flow
- [ ] Admin runs `/warn` command
- [ ] Admin enters user ID
- [ ] Admin enters warning reason
- [ ] System records warning
- [ ] Warning count increments
- [ ] User receives notification
- [ ] User added to warning list

**Expected Result**: Warning recorded and user notified

#### 3.2 Multiple Warnings
- [ ] Warn same user multiple times
- [ ] Check warning count increases
- [ ] Each warning stored in history

**Expected Result**: Multiple warnings tracked correctly

#### 3.3 Warning Before Ban
- [ ] Warn user first
- [ ] Then ban user
- [ ] Warning list removes user
- [ ] Ban takes precedence

**Expected Result**: Ban overrides warning

### 4. Auto-Ban Tests

#### 4.1 Report Counter
- [ ] Have 5 different users report same user
- [ ] Check report count increments each time
- [ ] Verify counter stored in Redis

**Expected Result**: Report counter works

#### 4.2 Auto-Ban Trigger
- [ ] User receives 5th report
- [ ] Auto-ban triggers automatically
- [ ] Ban duration is 7 days
- [ ] Reason is "abuse"
- [ ] `is_auto_ban` flag set to true
- [ ] User receives notification

**Expected Result**: Auto-ban triggers at threshold

#### 4.3 Auto-Ban Prevention (Already Banned)
- [ ] Ban a user manually
- [ ] Have users report banned user
- [ ] Auto-ban doesn't trigger again

**Expected Result**: No duplicate bans

### 5. Ban Status Check Tests

#### 5.1 Check Banned User
- [ ] Ban a user
- [ ] Admin runs `/checkban <user_id>`
- [ ] System shows:
  - [ ] Ban status (BANNED)
  - [ ] Reason
  - [ ] Ban date
  - [ ] Expiry date (if temporary)
  - [ ] Time remaining
  - [ ] Who banned them
  - [ ] Auto-ban indicator

**Expected Result**: Complete ban information displayed

#### 5.2 Check Non-Banned User
- [ ] Run `/checkban` on unbanned user
- [ ] System shows "NOT banned"
- [ ] Shows warning count if any

**Expected Result**: Clear status message

#### 5.3 Check Auto-Banned User
- [ ] Check user who was auto-banned
- [ ] System shows "(Auto-ban)" indicator
- [ ] Shows "System" as banner

**Expected Result**: Auto-ban clearly indicated

### 6. List Commands Tests

#### 6.1 Banned List
- [ ] Ban multiple users
- [ ] Admin runs `/bannedlist`
- [ ] System shows all banned users
- [ ] Each entry shows:
  - [ ] User ID
  - [ ] Ban reason
  - [ ] Ban type (Permanent/Temporary)
  - [ ] Auto-ban indicator
- [ ] Shows count of banned users
- [ ] Limits to first 20 with overflow indicator

**Expected Result**: Comprehensive list of bans

#### 6.2 Warning List
- [ ] Warn multiple users
- [ ] Admin runs `/warninglist`
- [ ] System shows all warned users
- [ ] Each entry shows:
  - [ ] User ID
  - [ ] Warning count
- [ ] Shows count of warned users
- [ ] Limits to first 20 with overflow indicator

**Expected Result**: Comprehensive list of warnings

#### 6.3 Empty Lists
- [ ] Clear all bans/warnings
- [ ] Run `/bannedlist` and `/warninglist`
- [ ] Both show "No users" message

**Expected Result**: Proper empty state messages

### 7. Message Blocking Tests

#### 7.1 Banned User Sends Message
- [ ] Ban a user
- [ ] Banned user tries to send message
- [ ] Message is blocked
- [ ] User receives ban notification
- [ ] Message not forwarded to partner

**Expected Result**: Messages blocked, user notified

#### 7.2 Banned User in Chat
- [ ] User is in active chat
- [ ] Ban the user
- [ ] User tries to send message
- [ ] Message blocked
- [ ] Chat terminated

**Expected Result**: Active chat terminated

### 8. Queue Blocking Tests

#### 8.1 Banned User Joins Queue
- [ ] Ban a user
- [ ] User tries `/chat` command
- [ ] System blocks queue join
- [ ] User receives ban notification

**Expected Result**: Cannot join queue while banned

#### 8.2 User Banned While in Queue
- [ ] User joins queue
- [ ] Ban the user
- [ ] User removed from queue
- [ ] Cannot match with partner

**Expected Result**: Removed from queue

### 9. Admin Panel Tests

#### 9.1 Admin Command
- [ ] Admin runs `/admin`
- [ ] System shows:
  - [ ] Broadcast commands
  - [ ] Ban/moderation commands
  - [ ] Statistics commands
- [ ] All ban commands listed

**Expected Result**: Complete admin panel

#### 9.2 Non-Admin Access
- [ ] Non-admin user runs `/ban`
- [ ] System denies access
- [ ] Shows permission error

**Expected Result**: Admin-only enforcement

### 10. Integration Tests

#### 10.1 Profile Integration
- [ ] User has profile
- [ ] Ban user
- [ ] Profile data preserved
- [ ] Can view profile while banned
- [ ] Cannot edit profile

**Expected Result**: Profile preserved during ban

#### 10.2 Rating Integration
- [ ] User has ratings
- [ ] Ban user
- [ ] Ratings preserved
- [ ] Cannot rate partners while banned

**Expected Result**: Ratings preserved during ban

#### 10.3 Preferences Integration
- [ ] User has preferences
- [ ] Ban user
- [ ] Preferences preserved
- [ ] Cannot modify preferences

**Expected Result**: Preferences preserved during ban

### 11. Notification Tests

#### 11.1 Ban Notification (Temporary)
- [ ] Ban user temporarily
- [ ] User receives message with:
  - [ ] Ban emoji (🚫)
  - [ ] "temporarily banned" text
  - [ ] Reason
  - [ ] Expiry date/time
  - [ ] Cannot use bot message

**Expected Result**: Clear, formatted notification

#### 11.2 Ban Notification (Permanent)
- [ ] Ban user permanently
- [ ] User receives message with:
  - [ ] Ban emoji (🚫)
  - [ ] "permanently banned" text
  - [ ] Reason
  - [ ] Cannot use bot message
  - [ ] Contact support message

**Expected Result**: Clear, formatted notification

#### 11.3 Warning Notification
- [ ] Warn user
- [ ] User receives message with:
  - [ ] Warning emoji (⚠️)
  - [ ] Warning reason
  - [ ] Total warning count
  - [ ] Multiple warnings warning
  - [ ] Follow rules message

**Expected Result**: Clear warning notification

#### 11.4 Unban Notification
- [ ] Unban user
- [ ] User receives message with:
  - [ ] Success emoji (✅)
  - [ ] "ban lifted" text
  - [ ] Can use bot message
  - [ ] Follow rules reminder

**Expected Result**: Clear unban notification

### 12. Edge Cases

#### 12.1 Ban Self (Admin)
- [ ] Admin tries to ban themselves
- [ ] System allows it (no special protection)

**Expected Result**: Self-ban possible (admin responsibility)

#### 12.2 Ban Another Admin
- [ ] Admin tries to ban another admin
- [ ] System allows it

**Expected Result**: Admin can ban admin (admin responsibility)

#### 12.3 Rapid Multiple Bans
- [ ] Ban same user multiple times quickly
- [ ] Only one ban active
- [ ] Latest ban overwrites

**Expected Result**: Latest ban is active

#### 12.4 Ban Then Warn
- [ ] Ban a user
- [ ] Try to warn same user
- [ ] Warning works
- [ ] Ban remains active

**Expected Result**: Both can coexist

#### 12.5 Very Long Reason
- [ ] Enter very long warning reason (500+ chars)
- [ ] System accepts it
- [ ] Stores complete reason

**Expected Result**: No truncation issues

#### 12.6 Special Characters in Reason
- [ ] Use emojis and special chars in reason
- [ ] System handles correctly
- [ ] Displays properly

**Expected Result**: Proper Unicode handling

### 13. Performance Tests

#### 13.1 Ban Check Speed
- [ ] Measure time for ban check
- [ ] Should be < 5ms

**Expected Result**: Fast Redis lookup

#### 13.2 Large Ban List
- [ ] Ban 100+ users
- [ ] Run `/bannedlist`
- [ ] Returns quickly
- [ ] Shows first 20 with overflow

**Expected Result**: Efficient even with many bans

#### 13.3 Concurrent Operations
- [ ] Multiple admins ban different users simultaneously
- [ ] All bans recorded
- [ ] No conflicts

**Expected Result**: Thread-safe operations

### 14. Redis Data Tests

#### 14.1 Ban Data Structure
- [ ] Ban a user
- [ ] Check Redis key `ban:{user_id}`
- [ ] Verify JSON structure:
  - [ ] user_id
  - [ ] banned_by
  - [ ] reason
  - [ ] banned_at
  - [ ] expires_at
  - [ ] is_permanent
  - [ ] is_auto_ban

**Expected Result**: Correct data structure

#### 14.2 Ban Set Membership
- [ ] Ban a user
- [ ] Check `bot:banned_users` set
- [ ] User ID is member

**Expected Result**: Set maintained correctly

#### 14.3 TTL on Temporary Ban
- [ ] Ban user for 1 hour
- [ ] Check Redis TTL on `ban:{user_id}`
- [ ] TTL is ~3600 seconds

**Expected Result**: Correct TTL set

#### 14.4 No TTL on Permanent Ban
- [ ] Ban user permanently
- [ ] Check Redis TTL on `ban:{user_id}`
- [ ] TTL is -1 (no expiry)

**Expected Result**: No expiry for permanent

### 15. Error Handling Tests

#### 15.1 Redis Connection Lost
- [ ] Disconnect Redis
- [ ] Try to ban user
- [ ] System shows error
- [ ] Logs error

**Expected Result**: Graceful error handling

#### 15.2 Invalid Data in Redis
- [ ] Manually corrupt ban data in Redis
- [ ] Try to check ban status
- [ ] System handles error
- [ ] Doesn't crash

**Expected Result**: Robust error handling

#### 15.3 User Not Found
- [ ] Try to ban non-existent user ID
- [ ] System still creates ban
- [ ] Notification attempt fails gracefully

**Expected Result**: Ban recorded, notification failure logged

### 16. Cancellation Tests

#### 16.1 Cancel Ban Operation
- [ ] Start `/ban` command
- [ ] Use `/cancel` command
- [ ] Operation cancelled
- [ ] No ban recorded

**Expected Result**: Clean cancellation

#### 16.2 Cancel Unban Operation
- [ ] Start `/unban` command
- [ ] Use `/cancel` command
- [ ] Operation cancelled

**Expected Result**: Clean cancellation

#### 16.3 Cancel Warning Operation
- [ ] Start `/warn` command
- [ ] Use `/cancel` command
- [ ] Operation cancelled
- [ ] No warning recorded

**Expected Result**: Clean cancellation

---

## Regression Tests

After any code changes, verify:
- [ ] Existing features still work
- [ ] Ban system doesn't break other commands
- [ ] Performance hasn't degraded
- [ ] No new errors in logs

---

## Load Tests

For production readiness:
- [ ] 100 users banned simultaneously
- [ ] 1000 ban status checks per minute
- [ ] 50 admin commands per minute
- [ ] System remains responsive
- [ ] No data corruption

---

## Documentation Tests

Verify documentation is accurate:
- [ ] All commands in docs work as described
- [ ] Examples are correct
- [ ] Screenshots/diagrams match actual UI
- [ ] No outdated information

---

## Security Tests

- [ ] Non-admin cannot use ban commands
- [ ] Cannot bypass ban with different command
- [ ] Cannot manipulate Redis directly to avoid ban
- [ ] Audit trail is complete
- [ ] All actions logged

---

## Test Results Template

```
Test Date: _______________
Tester: _______________
Environment: _______________

Tests Passed: ___ / ___
Tests Failed: ___ / ___
Tests Skipped: ___ / ___

Critical Issues: _______________
Minor Issues: _______________
Notes: _______________

Overall Status: [ ] PASS [ ] FAIL
```

---

## Sign-Off

```
□ All critical tests passed
□ All features working as expected
□ Documentation is accurate
□ No blocking issues
□ Ready for production

Tested by: _______________
Date: _______________
Signature: _______________
```

---

**Note**: This checklist should be completed before deploying to production. Any failed tests should be documented and resolved.
