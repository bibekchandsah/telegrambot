# Admin Dashboard Testing Guide

## 🧪 Testing the Admin Dashboard

This guide will help you test all features of the admin dashboard to ensure everything works correctly.

## Prerequisites

Before testing:
- ✅ Redis is running
- ✅ Telegram bot is running
- ✅ At least 2-3 test users have interacted with the bot
- ✅ Dashboard is running (`python admin_dashboard.py`)
- ✅ Browser is open to http://localhost:5000

## Quick Test Setup

### 1. Create Test Data
```bash
# Use your bot with multiple Telegram accounts to create test data:
# Account 1: /start, create profile
# Account 2: /start, create profile, /chat
# Account 3: /start, create profile, /chat
```

## Manual Testing Checklist

### ✅ Dashboard Access & Loading

#### Test 1: Access Dashboard
- [ ] Open http://localhost:5000 in browser
- [ ] Page loads without errors
- [ ] All sections visible (header, stats, tabs, tables)
- [ ] No console errors (F12 → Console)

**Expected:** Clean UI with purple gradient, all elements visible

#### Test 2: Initial Data Load
- [ ] Statistics cards show numbers (not dashes)
- [ ] "All Users" tab loads automatically
- [ ] User table displays users
- [ ] Current time displays and updates

**Expected:** All statistics populated with real numbers

---

### ✅ Statistics Cards

#### Test 3: Statistics Display
- [ ] Total Users shows correct count
- [ ] Users with Profiles shows count
- [ ] Active Users shows count
- [ ] Users in Queue shows count
- [ ] Users in Chat shows count

**Expected:** Numbers match actual Redis data

**Verify manually:**
```bash
# Check total users
redis-cli SCARD bot:all_users

# Check queue
redis-cli LLEN queue:waiting

# Check pairs
redis-cli KEYS "pair:*" | wc -l
```

#### Test 4: Auto-refresh
- [ ] Wait 30 seconds
- [ ] Statistics update automatically
- [ ] No page reload required
- [ ] New values reflect current state

**Expected:** Stats refresh every 30 seconds

---

### ✅ All Users Tab

#### Test 5: User List Display
- [ ] Click "All Users" tab
- [ ] User table shows users
- [ ] Columns: User ID, Username, Age, Gender, Country, Actions
- [ ] "View Details" button present for each user
- [ ] Pagination info shows (e.g., "Showing 1-20 of 50")

**Expected:** Properly formatted table with all columns

#### Test 6: Pagination (if > 20 users)
- [ ] Pagination controls visible at bottom
- [ ] "Previous" button disabled on page 1
- [ ] Click "Next" button
- [ ] Page 2 loads
- [ ] Pagination info updates (e.g., "Showing 21-40 of 50")
- [ ] Click page number directly
- [ ] Jump to that page
- [ ] Click "Previous" to go back

**Expected:** Smooth pagination, correct page numbers

#### Test 7: Manual Refresh
- [ ] Click "🔄 Refresh" button
- [ ] Table shows loading state
- [ ] Data reloads
- [ ] Table updates with current data

**Expected:** Quick refresh, no errors

---

### ✅ Online Users Tab

#### Test 8: Online Users Display
- [ ] Click "Online Users" tab
- [ ] Active users displayed
- [ ] Shows users in queue + users in chat
- [ ] If no online users: "No online users" message

**Expected:** Only active users shown

**To test:**
1. Have 1-2 users use `/chat` command
2. Refresh dashboard
3. See them in "Online Users"

---

### ✅ In Chat Tab

#### Test 9: Chat Sessions Display
- [ ] Click "In Chat" tab
- [ ] Users in active chats displayed
- [ ] Extra column: "Partner ID"
- [ ] Partner IDs populated
- [ ] If no chats: "No users in chat" message

**Expected:** Chat pairs shown with partner IDs

**To test:**
1. Start chat between 2 test users
2. Refresh "In Chat" tab
3. See both users with each other's IDs as partners

#### Test 10: Chat Pair Verification
- [ ] User A has Partner ID = User B's ID
- [ ] User B has Partner ID = User A's ID
- [ ] IDs are numbers (not "N/A")

**Expected:** Correct partner pairing

---

### ✅ In Queue Tab

#### Test 11: Queue Display
- [ ] Click "In Queue" tab
- [ ] Users waiting for match displayed
- [ ] Shows users who used `/chat` but not matched yet
- [ ] If queue empty: "No users in queue" message

**Expected:** Only queued users shown

**To test:**
1. Have 1 user use `/chat` (odd number = stays in queue)
2. Refresh "In Queue" tab
3. See user waiting

---

### ✅ Search Functionality

#### Test 12: Search by User ID
- [ ] Click "Search Users" tab
- [ ] Enter a known User ID
- [ ] Click "🔍 Search"
- [ ] Correct user displayed
- [ ] Only that user shown

**Expected:** Exact match found

#### Test 13: Search by Username
- [ ] Enter partial username (e.g., "john" for "johnny123")
- [ ] Click "🔍 Search"
- [ ] All matching users displayed
- [ ] Partial matches work

**Expected:** Case-insensitive partial match

#### Test 14: Search by Gender
- [ ] Select "Male" from Gender dropdown
- [ ] Click "🔍 Search"
- [ ] Only male users displayed

**Expected:** Gender filter works

#### Test 15: Search by Country
- [ ] Enter country name (e.g., "USA")
- [ ] Click "🔍 Search"
- [ ] Only users from that country displayed

**Expected:** Country filter works

#### Test 16: Combined Search
- [ ] Enter Username AND select Gender
- [ ] Click "🔍 Search"
- [ ] Results match BOTH criteria
- [ ] Users must satisfy all filters

**Expected:** AND logic, not OR

#### Test 17: Clear Search
- [ ] After a search, click "Clear" button
- [ ] All fields reset
- [ ] Table shows placeholder text

**Expected:** Form clears, ready for new search

#### Test 18: No Results
- [ ] Search for non-existent user (ID: 99999999)
- [ ] Click "🔍 Search"
- [ ] "No users found" message displayed

**Expected:** Graceful no-results handling

---

### ✅ User Details Modal

#### Test 19: Open User Details
- [ ] Click "View Details" on any user
- [ ] Modal popup appears
- [ ] Modal has close button (X)
- [ ] Dark overlay behind modal
- [ ] Details are loading initially

**Expected:** Smooth modal open animation

#### Test 20: User Details Content
- [ ] User ID displayed
- [ ] Username displayed (or "N/A")
- [ ] Age, Gender, Country shown
- [ ] Interests displayed
- [ ] Bio displayed
- [ ] Current State shown
- [ ] In Queue: Yes/No
- [ ] In Chat: Yes/No

**Expected:** Complete user profile

#### Test 21: User Details - Active Chat
- [ ] View details of user in chat
- [ ] "In Chat" shows "Yes"
- [ ] "Chat Partner ID" field visible
- [ ] Partner ID is correct

**Expected:** Chat status and partner shown

#### Test 22: User Details - Preferences
- [ ] If user has preferences set
- [ ] Preferences section visible
- [ ] JSON formatted data
- [ ] Readable format

**Expected:** Preferences displayed in monospace

#### Test 23: Close Modal
- [ ] Click X button → modal closes
- [ ] Click outside modal (on overlay) → modal closes
- [ ] Press ESC key → modal closes (if implemented)

**Expected:** Multiple ways to close

---

### ✅ Responsive Design

#### Test 24: Desktop View
- [ ] Full screen (1920x1080)
- [ ] All elements visible
- [ ] No horizontal scroll
- [ ] Stats cards in row
- [ ] Tables not truncated

**Expected:** Clean desktop layout

#### Test 25: Tablet View
- [ ] Resize to 768px width
- [ ] Stats cards stack
- [ ] Tabs full width
- [ ] Tables scrollable horizontally
- [ ] All functions work

**Expected:** Responsive tablet layout

#### Test 26: Mobile View
- [ ] Resize to 375px width (phone size)
- [ ] All cards stacked vertically
- [ ] Tabs full width
- [ ] Tables scrollable
- [ ] Buttons full width
- [ ] Search form stacked

**Expected:** Mobile-friendly layout

#### Test 27: Mobile Browser
- [ ] Access from phone: http://YOUR_IP:5000
- [ ] Dashboard loads
- [ ] Touch navigation works
- [ ] Tables scroll with finger swipe
- [ ] All features functional

**Expected:** Fully functional on mobile

---

### ✅ Error Handling

#### Test 28: Redis Disconnected
- [ ] Stop Redis (`docker stop redis` or service)
- [ ] Refresh dashboard
- [ ] Statistics show 0 or error
- [ ] Error messages in console
- [ ] No crashes

**Expected:** Graceful degradation

#### Test 29: Invalid User ID
- [ ] Try to access `/api/users/invalid`
- [ ] 404 or error response
- [ ] Dashboard still functional

**Expected:** Error handled properly

#### Test 30: Network Error
- [ ] Disconnect internet briefly
- [ ] API calls fail
- [ ] Error shown in tables
- [ ] Dashboard doesn't crash

**Expected:** Error messages, no crashes

---

### ✅ API Endpoints

#### Test 31: API - Statistics
```bash
curl http://localhost:5000/api/stats
```
- [ ] Returns JSON
- [ ] Contains: total_users, users_with_profiles, active_users, etc.
- [ ] All numbers are integers

**Expected:** Valid JSON with stats

#### Test 32: API - All Users
```bash
curl http://localhost:5000/api/users?page=1&per_page=20
```
- [ ] Returns JSON
- [ ] Contains: users array, page, per_page, total, total_pages
- [ ] Users have: user_id, username, age, gender, country

**Expected:** Paginated user list

#### Test 33: API - Search
```bash
curl "http://localhost:5000/api/users/search?gender=Male"
```
- [ ] Returns JSON
- [ ] Array of matching users
- [ ] Only male users

**Expected:** Filtered results

#### Test 34: API - User Details
```bash
curl http://localhost:5000/api/users/123456789
```
- [ ] Returns JSON
- [ ] Complete user object
- [ ] Includes state, preferences, status

**Expected:** Full user details

#### Test 35: API - Health Check
```bash
curl http://localhost:5000/health
```
- [ ] Returns: `{"status": "healthy", "timestamp": "..."}`
- [ ] HTTP 200 OK

**Expected:** Health check passes

---

### ✅ Performance

#### Test 36: Load Time
- [ ] Initial page load < 2 seconds
- [ ] API responses < 500ms
- [ ] No lag when switching tabs
- [ ] Smooth animations

**Expected:** Fast, responsive UI

#### Test 37: Large Dataset (100+ users)
- [ ] With 100+ users
- [ ] Pagination handles correctly
- [ ] Search doesn't slow down
- [ ] All features responsive

**Expected:** No performance degradation

#### Test 38: Concurrent Access
- [ ] Open dashboard in 3+ browser tabs
- [ ] All tabs work independently
- [ ] No conflicts
- [ ] Each tab updates correctly

**Expected:** Multi-tab support

---

### ✅ Security (Development Mode)

#### Test 39: No Authentication
- [ ] Dashboard accessible without login
- [ ] Anyone on network can access
- [ ] No password required

**Expected:** Open access (dev mode)

#### Test 40: CORS
- [ ] API accessible from different origin
- [ ] No CORS errors in console

**Expected:** CORS enabled

---

## Automated Testing (Optional)

### Unit Tests (Future)
```python
# test_dashboard.py
import pytest
from src.services.dashboard import DashboardService

def test_get_statistics():
    service = DashboardService(redis_mock)
    stats = await service.get_statistics()
    assert 'total_users' in stats
    assert stats['total_users'] >= 0
```

### Integration Tests
```python
# test_api.py
import requests

def test_stats_endpoint():
    response = requests.get('http://localhost:5000/api/stats')
    assert response.status_code == 200
    data = response.json()
    assert 'total_users' in data
```

### Load Testing
```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost:5000/api/stats

# Expected: Handle 100+ req/sec
```

---

## Test Scenarios

### Scenario 1: New Bot (No Users)
1. Start fresh bot
2. Open dashboard
3. **Expected:** All stats show 0, empty tables

### Scenario 2: Users Join Queue
1. 5 users use `/chat`
2. Refresh dashboard
3. **Expected:** 5 in "Online", 5 in "Queue"

### Scenario 3: Users Get Matched
1. Even number of users chat
2. Refresh dashboard
3. **Expected:** Users move from "Queue" to "In Chat"

### Scenario 4: User Disconnects
1. User in chat uses `/stop`
2. Refresh dashboard
3. **Expected:** User disappears from "In Chat" and "Online"

### Scenario 5: Search Multiple Criteria
1. Search: Gender=Male, Country=USA
2. **Expected:** Only male users from USA

---

## Browser Console Checks

Press F12 → Console tab and verify:

### No Errors
```javascript
// Should NOT see:
❌ 404 Not Found
❌ TypeError: ...
❌ Failed to fetch
❌ CORS error
```

### Network Requests
Check Network tab (F12 → Network):
- [ ] `/api/stats` - Status 200
- [ ] `/api/users` - Status 200
- [ ] All API calls succeed
- [ ] Response times < 500ms

---

## Redis Verification

Check Redis directly:

```bash
# Connect to Redis
redis-cli

# Check user count
SCARD bot:all_users

# Check queue
LLEN queue:waiting

# Check specific user
GET profile:123456789

# Check pairs
KEYS pair:*

# Check all keys
KEYS *
```

---

## Troubleshooting Test Failures

### Stats Show 0 (but users exist)
**Fix:** Check Redis connection, verify keys exist

### Search Returns Nothing
**Fix:** Verify users have complete profiles

### Modal Doesn't Open
**Fix:** Check JavaScript console for errors

### Pagination Doesn't Work
**Fix:** Ensure page numbers are calculated correctly

### Mobile Layout Broken
**Fix:** Check CSS media queries, test different screen sizes

---

## Success Criteria

✅ **All tests pass** means:
- No console errors
- All features work as expected
- Responsive on all devices
- API returns valid JSON
- Performance is good
- Error handling works

---

## Reporting Issues

If tests fail, collect:
1. Browser console errors (F12 → Console)
2. Network tab errors (F12 → Network)
3. Dashboard logs (terminal output)
4. Redis connection status
5. Steps to reproduce

---

## Next Steps After Testing

Once all tests pass:
1. ✅ Deploy to production (with authentication!)
2. ✅ Add monitoring and logging
3. ✅ Implement chat history feature
4. ✅ Add export functionality
5. ✅ Create analytics dashboard

---

**Happy Testing! 🧪✅**
