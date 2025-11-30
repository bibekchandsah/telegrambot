# Preferences Feature Documentation

## Overview

The Preferences feature allows users to set matching filters to find chat partners that match their criteria. Users can filter potential matches by gender and country, improving their chat experience.

## Features

### 1. Preference Management
- **Gender Filter**: Choose to match with Male, Female, or Any gender
- **Country Filter**: Choose to match with specific countries or Any
- **Default Settings**: All filters default to "Any" (no filtering)
- **Persistent Storage**: Preferences are stored in Redis permanently

### 2. Preference Commands

#### `/preferences`
Opens the preferences menu with the following options:
- 🔄 **Change Gender Filter** - Set gender preference (Male/Female/Any)
- 🌍 **Change Country Filter** - Set country preference
- 🔄 **Reset to Defaults** - Reset all preferences to "Any"
- ❌ **Cancel** - Exit preferences menu

### 3. Matching Algorithm

The matching system implements **mutual preference matching**:
- User A's preferences must match User B's profile
- User B's preferences must match User A's profile
- Only if both conditions are met will they be matched

#### Example Scenarios

**Scenario 1: Successful Match**
- User A: Gender=Male, Country=USA, Preferences: Female from Any
- User B: Gender=Female, Country=Canada, Preferences: Male from Any
- ✅ Match! A wants Female (B is Female), B wants Male (A is Male)

**Scenario 2: Failed Match**
- User A: Gender=Male, Country=USA, Preferences: Female from India
- User B: Gender=Female, Country=Canada, Preferences: Any from Any
- ❌ No Match! A wants Female from India (B is from Canada)

**Scenario 3: Default Behavior**
- User A: No preferences set (defaults to Any/Any)
- User B: Gender=Female, Preferences: Male from USA
- ✅ Match if User A is Male from USA

## Implementation Details

### Data Structures

#### Preference Storage
```
Key: preferences:{user_id}
Value: {
  "user_id": 123456789,
  "gender_filter": "Male",
  "country_filter": "India"
}
TTL: None (permanent)
```

### Architecture

#### New Components
1. **src/services/preferences.py**
   - `PreferenceManager` class for CRUD operations
   - `UserPreferences` data class
   - Validation functions for gender and country filters

2. **Preference Handlers** (in src/handlers/commands.py)
   - `preferences_command` - Entry point
   - `pref_gender_callback` - Gender filter selection
   - `pref_country_text` - Country filter text input
   - `cancel_preferences` - Cancel operation

3. **Conversation States**
   - `PREF_GENDER` - Waiting for gender selection
   - `PREF_COUNTRY` - Waiting for country input

#### Modified Components
1. **src/services/matching.py**
   - `__init__` now accepts `profile_manager` and `preference_manager`
   - `find_partner` uses preference-based matching
   - New method: `_find_compatible_partner` - Filters queue by preferences
   - New method: `_are_compatible` - Checks mutual preference compatibility

2. **src/services/queue.py**
   - New method: `get_all_in_queue` - Returns all user IDs in queue

3. **src/handlers/commands.py**
   - Updated `/start` and `/help` to mention preferences
   - Updated `/chat` to show tip about preferences for new users

4. **src/bot.py**
   - Added `PreferenceManager` initialization
   - Registered preferences conversation handler
   - Pass managers to `MatchingEngine`

## User Workflow

### Setting Preferences
1. User sends `/preferences`
2. Bot shows current preferences with action buttons
3. User clicks "Change Gender Filter"
4. Bot shows gender options (Male/Female/Any)
5. User selects gender
6. Preference saved, confirmation shown
7. Repeat for country if needed

### Matching with Preferences
1. User sends `/chat` to find partner
2. Bot checks user's preferences and profile
3. Bot scans queue for compatible partners:
   - Checks if user matches partner's preferences
   - Checks if partner matches user's preferences
4. If compatible match found:
   - Both users connected
   - Profiles shown
5. If no match found:
   - User added to queue
   - Waiting message shown

## Validation Rules

### Gender Filter
- Must be one of: "Male", "Female", "Any"
- Case-sensitive

### Country Filter
- Must be from the predefined country list (same as profile)
- OR must be "Any"
- Case-sensitive

## Commands Reference

| Command | Description |
|---------|-------------|
| `/preferences` | Open preferences menu |
| `/cancel` | Cancel preference editing |

## Benefits

1. **Better Matches**: Users find partners who meet their criteria
2. **User Control**: Users customize their experience
3. **Mutual Respect**: Both users must match each other's preferences
4. **Backwards Compatible**: Works with users who haven't set preferences (defaults to "Any")

## Technical Highlights

- **Atomic Operations**: Uses Redis for consistent state management
- **Mutual Filtering**: Both users must satisfy each other's preferences
- **Efficient Scanning**: Iterates through queue to find first compatible match
- **Graceful Fallbacks**: Missing profiles/preferences allow matching (backwards compatibility)
- **Interactive UI**: Uses InlineKeyboardButtons for easy preference selection

## Future Enhancements

Possible improvements for future versions:
- Age range filter
- Language preference filter
- Interest-based matching
- "Recently matched" tracking to avoid immediate rematches
- Preference statistics (e.g., "30% of users prefer Female partners")
- Smart suggestions based on successful matches

## Testing

### Manual Testing Steps
1. Create two test accounts
2. Set preferences on Account A (e.g., Female from India)
3. Set profile on Account B (Female, India)
4. Use `/chat` on both accounts
5. Verify they match
6. Reset Account B's profile to (Male, USA)
7. Use `/chat` again
8. Verify they don't match

### Edge Cases Tested
- User without profile (uses defaults)
- User without preferences (matches anyone)
- Both users without profiles/preferences (matches normally)
- One-sided preference mismatch
- Both-sided preference match
- Queue empty scenario
- Preference reset functionality

## Error Handling

The system handles:
- Invalid gender filter input
- Invalid country filter input
- Redis connection errors (graceful fallback to defaults)
- Missing profile data (allows match)
- Missing preference data (defaults to "Any/Any")
- Race conditions during matching (atomic queue operations)

## Performance Considerations

- **Queue Scanning**: O(n) where n = queue size
  - Acceptable for most cases (queue typically small)
  - First-match algorithm (stops when compatible user found)
- **Redis Operations**: Minimal overhead
  - Preference lookups: O(1)
  - Profile lookups: O(1)
- **Scalability**: Works well for 1000+ users in queue
  - For larger scale, consider:
    - Indexing users by preferences
    - Separate queues per filter combination
    - Caching frequently accessed profiles

---

**Feature Status**: ✅ Fully Implemented and Tested
**Version**: 1.0
**Last Updated**: 2025
