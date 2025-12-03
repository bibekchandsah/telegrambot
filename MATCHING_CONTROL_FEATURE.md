# Matching Control Feature

## Overview
Added a comprehensive **Matching Control** tab to the admin dashboard, allowing administrators to:
- Enable/disable gender-based matching filters globally
- Enable/disable regional (country-based) matching filters globally
- Monitor the matching queue size in real-time
- Force match two specific users (debug feature)

## Features

### 1. Filter Toggles
Administrators can enable or disable matching filters globally:

#### Gender Filter
- **Default**: Enabled (ON)
- **When disabled**: Users' gender preferences are ignored during matching
- **Effect**: Allows matching between any genders regardless of preferences

#### Regional Filter
- **Default**: Enabled (ON)
- **When disabled**: Users' country preferences are ignored during matching
- **Effect**: Allows international matches regardless of preferences

**Note**: Even when filters are disabled globally, the matching engine still:
- Filters out toxic users based on ratings
- Prioritizes users with better ratings
- Ensures mutual compatibility on enabled filters

### 2. Queue Statistics
Real-time monitoring of the matching queue:
- **Queue Size**: Current number of users waiting for matches
- **Last Updated**: Timestamp of the last queue size check
- **Auto-refresh**: Statistics refresh when the tab is opened

### 3. Force Match (Debug Feature)
Manually pair two specific users:
- **Input**: Two user IDs
- **Validation**: 
  - Users must be different
  - Both users must exist in the system
  - Neither user can already be in a chat
- **Effect**: 
  - Creates bidirectional pair mapping
  - Updates both users' states to IN_CHAT
  - Removes both from queue if present
  - Initializes activity timestamps
  - **Sends special notification to both users** ✨
  - Logs the action for moderation tracking

**Special Notification**: Both users receive a unique message with emojis:
```
✨ 🎉 Special Match Found! 🎉 ✨

You've been specially matched with someone amazing! 
This is a unique connection just for you. 

💬 Start chatting now and enjoy your conversation! 💫

Use /next to find a new partner or /stop to end the chat.
```

**⚠️ Warning**: This bypasses all matching logic and filters. Use only for debugging.

## Technical Implementation

### Backend (admin_dashboard.py)

#### New API Endpoints

1. **GET /api/matching/settings**
   ```json
   Response:
   {
     "success": true,
     "settings": {
       "gender_filter_enabled": true,
       "regional_filter_enabled": true
     }
   }
   ```

2. **POST /api/matching/settings**
   ```json
   Request:
   {
     "admin_id": "admin",
     "gender_filter_enabled": true,
     "regional_filter_enabled": false
   }
   
   Response:
   {
     "success": true,
     "message": "Matching settings updated successfully",
     "updated_settings": {
       "gender_filter_enabled": true,
       "regional_filter_enabled": false
     }
   }
   ```

3. **GET /api/matching/queue-size**
   ```json
   Response:
   {
     "success": true,
     "queue_size": 12,
     "timestamp": "2025-12-03T05:12:37.123456"
   }
   ```

4. **POST /api/matching/force-match**
   ```json
   Request:
   {
     "admin_id": "admin",
     "user1_id": 123456789,
     "user2_id": 987654321
   }
   
   Response:
   {
     "success": true,
     "message": "Successfully forced match between users 123456789 and 987654321",
     "details": {
       "user1_id": 123456789,
       "user1_previous_state": "IN_QUEUE",
       "user2_id": 987654321,
       "user2_previous_state": "IDLE"
     }
   }
   ```
   
   **Side Effects**:
   - Both users receive special notification message with emojis
   - Activity timestamps initialized for both users
   - Users removed from queue if present
   - Action logged in moderation history

### Redis Keys

#### Filter Settings
- **matching:gender_filter_enabled**: `"1"` (enabled) or `"0"` (disabled)
- **matching:regional_filter_enabled**: `"1"` (enabled) or `"0"` (disabled)
- **Default**: Both enabled (backward compatible)

#### Queue Data
- **queue:waiting**: Redis list containing user IDs waiting for matches

#### Pair Mappings (Created by Force Match)
- **pair:{user1_id}**: Stores partner ID (user2_id)
- **pair:{user2_id}**: Stores partner ID (user1_id)
- **TTL**: CHAT_TIMEOUT (from config)

#### State Management
- **state:{user_id}**: User state (IDLE, IN_QUEUE, IN_CHAT)

### Matching Engine (src/services/matching.py)

Updated `_are_compatible()` method to respect global filter settings:

```python
# Check if gender filter is enabled globally
gender_filter_enabled = await self.redis.get("matching:gender_filter_enabled")
gender_filter_enabled = gender_filter_enabled is None or gender_filter_enabled == "1"

# Check if regional filter is enabled globally
regional_filter_enabled = await self.redis.get("matching:regional_filter_enabled")
regional_filter_enabled = regional_filter_enabled is None or regional_filter_enabled == "1"

# Only apply gender filter if enabled globally
if gender_filter_enabled and user_preferences.gender_filter != "Any":
    if partner_profile.gender != user_preferences.gender_filter:
        return False

# Only apply regional filter if enabled globally
if regional_filter_enabled and user_preferences.country_filter != "Any":
    if partner_profile.country != user_preferences.country_filter:
        return False
```

**Backward Compatibility**: If Redis keys don't exist (None), filters default to enabled.

### Frontend (templates/dashboard.html)

Added new tab section with three main areas:

1. **Filter Controls** (lines ~543-561)
   - Custom toggle switches for gender and regional filters
   - Onchange handlers call `updateMatchingFilters()`

2. **Queue Statistics** (lines ~564-577)
   - Display current queue size
   - Show last updated timestamp

3. **Force Match Form** (lines ~580-603)
   - Warning-styled container (yellow background)
   - Two number inputs for user IDs
   - Submit button calls `forceMatchUsers()`

### JavaScript (static/js/dashboard.js)

#### New Functions

1. **loadMatchingSettings()**
   - Fetches current filter settings from API
   - Updates checkbox states
   - Auto-loads queue size

2. **updateMatchingFilters()**
   - Reads checkbox states
   - POSTs changes to API
   - Shows success notification
   - Reverts UI on error

3. **loadQueueSize()**
   - Fetches current queue size
   - Updates display and timestamp
   - Handles errors gracefully

4. **forceMatchUsers()**
   - Validates input (both IDs present, different)
   - Shows confirmation dialog with warning
   - POSTs force match request
   - Clears inputs on success
   - Refreshes statistics

5. **showNotification()**
   - Displays success/error messages
   - Currently logs to console (can be enhanced)

#### Tab Loader Integration
Updated `loadTabData()` switch statement:
```javascript
case 'matching-control':
    loadMatchingSettings();
    break;
```

### CSS (static/css/dashboard.css)

Added comprehensive styling:

#### Toggle Switch Styles
- Custom toggle switch design (50px × 24px)
- Smooth animations (0.4s transition)
- Purple color (#667eea) when enabled
- Proper label alignment

#### Statistics Display
- Flexbox layout for stat rows
- Large value display (36px font)
- Light gray background (#f8f9fa)
- Rounded corners (8px)

#### Force Match Container
- Warning-styled box (yellow #fff3cd background)
- Yellow border (#ffc107)
- Dark yellow text (#856404)
- Input groups with proper spacing

#### Responsive Design
- Stacks on mobile (max-width: 768px)
- Full-width inputs on small screens
- Vertical layout for stat rows

## Usage

### Accessing Matching Control
1. Open admin dashboard: `http://localhost:5000`
2. Click on **🎯 Matching Control** tab

### Disabling Gender Filter
1. Navigate to Matching Control tab
2. Toggle **Enable Gender-Based Matching** OFF
3. Settings save automatically
4. Users will now match regardless of gender preferences

### Disabling Regional Filter
1. Navigate to Matching Control tab
2. Toggle **Enable Regional Matching** OFF
3. Settings save automatically
4. Users will now match regardless of country preferences

### Monitoring Queue
- Queue size updates when tab is opened
- Click **Refresh** button for manual update
- View last updated timestamp

### Force Matching Users
1. Navigate to Matching Control tab
2. Enter **User 1 ID** and **User 2 ID**
3. Click **Force Match**
4. Confirm warning dialog
5. Both users are now matched and can chat
6. **Both users receive a special notification** making them feel uniquely matched ✨

**⚠️ Important**: Force match is for debugging only. Use with caution.

## Error Handling

### Filter Update Errors
- If update fails, UI reverts to previous state
- Error message displayed to admin
- Settings reloaded from server

### Force Match Validation
- **Same User ID**: "Cannot match a user with themselves"
- **User Not Found**: "User {id} not found or has no state"
- **Already in Chat**: "User {id} is already in a chat"
- **Missing IDs**: "Please enter both user IDs"

### Queue Size Errors
- Display shows "Error" on failure
- Timestamp shows "-" on error
- Error logged to console

## Logging

All matching control actions are logged:

```python
# Filter updates
logger.info("matching_settings_updated", 
    admin_id=admin_id,
    gender_filter=gender_filter_enabled,
    regional_filter=regional_filter_enabled
)

# Force matches
logger.info("force_match_executed",
    admin_id=admin_id,
    user1_id=user1_id,
    user2_id=user2_id,
    user1_previous_state=user1_state,
    user2_previous_state=user2_state
)
```

## Testing

### Test Filter Toggles
1. Disable gender filter
2. Have two users with incompatible gender preferences join queue
3. Verify they get matched (bypassing gender check)

### Test Regional Filter
1. Disable regional filter
2. Have users from different countries join queue
3. Verify they get matched (bypassing country check)

### Test Force Match
1. Get two user IDs (from Users tab)
2. Use force match feature
3. **Verify both users receive special notification** with emojis and unique message
4. Verify they can exchange messages
5. Check that chat functions normally (message forwarding, /next, /stop)

### Test Validation
1. Try force matching a user with themselves → Error
2. Try force matching non-existent users → Error
3. Try force matching users already in chat → Error

## Security Considerations

- **Authentication**: Admin dashboard should be behind authentication (not implemented yet)
- **Rate Limiting**: Consider rate limiting force match to prevent abuse
- **Audit Log**: All actions logged with admin_id for accountability
- **Special Notifications**: Force-matched users receive unique notifications to enhance user experience
- **Error Handling**: Notification failures are logged but don't block the force match operation

## Future Enhancements

1. **Auto-refresh Queue Size**: Update every 5-10 seconds
2. **Customizable Special Messages**: Allow admins to customize force match notification text
3. **Undo Force Match**: Ability to quickly end a forced match
4. **Queue Details**: Show list of users in queue with their profiles
5. **Match History**: Log all force matches with timestamps
6. **Filter Analytics**: Track how filter changes affect match rates
7. **Bulk Operations**: Force match multiple pairs at once
8. **Temporary Overrides**: Time-limited filter disabling (e.g., for events)
9. **VIP Matching**: Mark certain users for priority or special matching
10. **A/B Testing**: Test different matching algorithms with different user groups

## Files Modified

1. **templates/dashboard.html** (~720 lines)
   - Added Matching Control tab button
   - Added filter toggles section
   - Added queue statistics section
   - Added force match form

2. **admin_dashboard.py** (~1520 lines)
   - Added 4 new API endpoints
   - Added validation logic
   - Added moderation logging

3. **static/js/dashboard.js** (~1690 lines)
   - Added 5 new functions
   - Updated tab loader
   - Added error handling

4. **static/css/dashboard.css** (~1070 lines)
   - Added toggle switch styles
   - Added statistics display styles
   - Added force match container styles
   - Added responsive design rules

5. **src/services/matching.py** (~410 lines)
   - Updated `_are_compatible()` method
   - Added Redis key checks for filter settings
   - Maintained backward compatibility

## Dependencies

No new dependencies required. Uses existing:
- Flask (backend framework)
- Redis (data storage)
- Bootstrap CSS (UI framework)
- Vanilla JavaScript (no additional libraries)

## Compatibility

- **Backward Compatible**: If filter keys don't exist, defaults to enabled (ON)
- **Existing Chats**: Not affected by filter changes
- **Queue Users**: Filter changes apply immediately to new matches
- **User Preferences**: Individual preferences still respected when filters are enabled

## Conclusion

The Matching Control feature provides administrators with powerful tools to manage the matching system. It balances automation with manual control, ensuring flexibility for debugging and special situations while maintaining the integrity of the matching algorithm.
