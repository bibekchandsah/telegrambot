# 👤 User Profile Feature

## Overview

Users can now create and edit their own profiles containing:
- **Nickname** (2-30 characters, not their Telegram name)
- **Gender** (Male/Female/Other)
- **Country** (from a list of 200+ countries)

When users are matched with a partner, they can see each other's profiles!

## New Commands

### `/profile`
- View your current profile
- Shows nickname, gender, and country with emojis
- Includes an "Edit Profile" button

### `/editprofile`
- Create a new profile or edit existing one
- Interactive conversation flow:
  1. Enter nickname (validated for length and characters)
  2. Select gender from buttons
  3. Choose country (popular countries shown first)
- Can be cancelled with `/cancel` at any time

## Features

### Profile Display
When matched with a partner, both users see:
```
✅ Partner found!

👤 Partner's Profile:
📝 Alex
👨 Male
🌍 United States

👋 Say hi and start chatting!
```

### Validation
- **Nickname**: 2-30 characters, alphanumeric + spaces/underscores/hyphens only
- **Gender**: Must be Male, Female, or Other
- **Country**: From validated list of 200+ countries

### Storage
- Profiles stored in Redis as JSON
- Key format: `profile:{user_id}`
- No expiration (permanent until deleted)
- Can be edited anytime

## User Flow

### First Time User
1. `/start` - See welcome message mentioning profile creation
2. `/editprofile` - Start profile creation
3. Enter nickname → Select gender → Choose country
4. Profile created! ✅
5. `/chat` - Start matching (profile shown to partners)

### Existing User
1. `/profile` - View current profile
2. Click "Edit Profile" button or use `/editprofile`
3. Update any field
4. Profile updated! ✅

## Technical Implementation

### New Files
- `src/services/profile.py` - ProfileManager class and validation functions

### Modified Files
- `src/handlers/commands.py` - Added profile commands and conversation handlers
- `src/bot.py` - Registered ProfileManager and ConversationHandler
- `/start` and `/help` commands updated to mention profiles

### Data Structure

**Redis Key**: `profile:{user_id}`
**Value** (JSON):
```json
{
  "user_id": 123456789,
  "nickname": "Alex",
  "gender": "Male",
  "country": "United States"
}
```

### Conversation States
- `NICKNAME` - Waiting for nickname input
- `GENDER` - Waiting for gender selection
- `COUNTRY` - Waiting for country selection

## Security & Privacy

✅ **Anonymous** - Telegram username/name never shared
✅ **Validated** - All inputs validated before saving
✅ **Safe** - Special characters filtered from nicknames
✅ **Optional** - Users can still chat without profiles
✅ **Editable** - Users can update anytime

## Integration with Matching

When two users are matched:
1. Bot fetches both profiles from Redis
2. Shows partner's profile to each user
3. If no profile exists, just shows "Partner found" (backward compatible)

## Country List

Includes 200+ countries:
- Popular countries shown first (India, US, UK, Pakistan, Bangladesh, Nepal, etc.)
- "Other" option for unlisted countries
- Searchable by typing country name

## Gender Options

- 👨 Male
- 👩 Female  
- 🧑 Other

## Example Usage

```
User: /editprofile

Bot: 👋 Welcome! Let's create your profile
     Step 1: Choose a nickname
     Send your nickname (2-30 characters):

User: CoolGuy123

Bot: ✅ Nickname set to: CoolGuy123
     Step 2: Select your gender:
     [Male] [Female] [Other]

User: *clicks Male*

Bot: ✅ Gender set to: Male
     Step 3: Select your country:
     [India] [United States] [United Kingdom] ...
     [See All Countries]

User: *clicks United States*

Bot: ✅ Profile Created Successfully!
     
     👤 Profile
     ━━━━━━━━━━━━━━━
     📝 Nickname: CoolGuy123
     👨 Gender: Male
     🌍 Country: United States
     
     You can:
     • View profile: /profile
     • Edit profile: /editprofile
     • Start chatting: /chat
```

## Benefits

1. **Better Connections** - Users know who they're talking to
2. **Icebreaker** - Profile info helps start conversations
3. **Cultural Exchange** - Know partner's country
4. **Gender Preference** - See partner's gender (future: use for matching filters)
5. **Personalization** - Choose your own identity in the chat

## Future Enhancements

The profile system is designed to support:
- Gender filtering (match only with selected gender)
- Country filtering (match only with specific countries)
- Age field
- Interests/hobbies
- Profile ratings
- Online status
- Profile visibility toggle

## Commands Summary

| Command | Description |
|---------|-------------|
| `/profile` | View your profile |
| `/editprofile` | Create or edit profile |
| `/cancel` | Cancel profile editing |

## Notes

- Profiles are optional but recommended
- Users without profiles can still use the bot
- Profile shown automatically when matched
- No way to hide profile once created (must edit to change)
- Nickname is displayed, not Telegram name
- All profile data stored securely in Redis
