# Feedback System Documentation

## Overview

The Anonymous Feedback System allows users to rate their chat partners after each conversation, helping to improve matching quality and automatically limit toxic users. The system uses a simple thumbs up (👍 Good) or thumbs down (👎 Bad) rating mechanism.

## Features

### 1. Anonymous Rating System
- **Rating Options**: Good (👍) or Bad (👎)
- **Anonymous**: Ratings are completely anonymous - partners never see who rated them
- **One-Time Rating**: Each user can rate their partner once per chat session (24-hour window)
- **Optional**: Users can skip rating if they prefer

### 2. User Rating Score
- **Score Range**: 0-100% based on positive vs negative ratings
- **New User Default**: 50% (neutral) for users with no ratings yet
- **Formula**: `(positive_ratings / total_ratings) × 100`

### 3. Rating Categories
- 🌟 **Excellent** (80%+): Top-tier users with great reputation
- 😊 **Good** (60-79%): Positive reputation
- 😐 **Neutral** (40-59%): Average or new users
- 😔 **Needs Improvement** (<40%): Poor reputation

### 4. Toxic User Auto-Limiting
- **Toxic Threshold**: Score < 30% with at least 5 ratings
- **Automatic Action**: Toxic users are blocked from using `/chat`
- **Warning Message**: Clear explanation shown to limited users
- **Recovery**: Users can improve by receiving better ratings over time

### 5. Matching Priority
- **Good User Priority**: Users with ratings ≥ 70% (with ≥3 ratings) get matched first
- **Rating-Based Sorting**: Queue sorted by rating score (highest first)
- **Toxic User Filter**: Automatically excluded from matching
- **Fair System**: New users (neutral rating) match normally

## Commands

### `/rating`
View your current rating statistics:
- Rating score percentage
- Positive rating count
- Negative rating count
- Total chat count
- Rating category and emoji

## How It Works

### Rating Flow

1. **Chat Ends** (via `/stop` or `/next`)
   - Both users receive feedback prompt
   - Three options shown: Good (👍), Bad (👎), Skip (⏭️)
   - Prompt expires after 5 minutes

2. **User Selects Rating**
   - Rating recorded in Redis
   - Partner's score updated instantly
   - Confirmation message shown with new score
   - Duplicate ratings prevented (24-hour window)

3. **Partner Not Notified**
   - Complete anonymity maintained
   - No notification about who rated them
   - Only overall score changes

### Matching Algorithm Integration

1. **Pre-Match Checks**
   - User tries to use `/chat`
   - System checks if user is toxic
   - If toxic: Show warning, block matching
   - If not: Proceed to matching

2. **Queue Scanning**
   - Collect all compatible partners
   - Filter out toxic users from results
   - Sort remaining partners by rating score
   - Match with highest-rated compatible partner

3. **Priority Matching**
   - Excellent users (80%+) matched first
   - Good users (60-79%) matched second
   - Neutral users (40-59%) matched third
   - Poor users (30-39%) matched last
   - Toxic users (<30% with ≥5 ratings) excluded

### Chat Count Tracking
- Incremented when match is created
- Used to track user activity
- Shown in `/rating` command
- Separate from ratings received

## Data Structures

### Rating Storage
```
Key: rating:{user_id}
Value: {
  "user_id": 123456789,
  "positive_ratings": 15,
  "negative_ratings": 3,
  "total_chats": 20,
  "rating_score": 83.33
}
TTL: None (permanent)
```

### Feedback Session Lock
```
Key: feedback:{rater_id}:{rated_user_id}
Value: "rated"
TTL: 86400 seconds (24 hours)
```
Prevents duplicate ratings for same chat session.

### Pending Feedback
```
Key: pending_feedback:{user_id}
Value: {partner_id}
TTL: 300 seconds (5 minutes)
```
Temporarily stores partner ID for feedback callback.

## Implementation Details

### Core Components

#### 1. FeedbackManager (`src/services/feedback.py`)
- **record_feedback()**: Records rating with duplicate prevention
- **increment_chat_count()**: Tracks total chats
- **get_rating()**: Retrieves user rating
- **is_user_limited()**: Checks if user is toxic
- **get_user_reputation_level()**: Returns reputation category
- **has_rated_partner()**: Checks for duplicate ratings
- **get_top_users()**: Leaderboard functionality (future use)

#### 2. UserRating Class
- **rating_score** property: Calculates 0-100 score
- **is_toxic** property: True if score < 30% with ≥5 ratings
- **is_good_user** property: True if score ≥ 70% with ≥3 ratings
- **to_display()**: Formats rating for user display

#### 3. Feedback Handlers (`src/handlers/commands.py`)
- **show_feedback_prompt()**: Displays rating buttons after chat
- **feedback_callback()**: Processes rating button clicks
- **rating_command()**: Shows user's own rating

#### 4. Modified Components
- **stop_command**: Shows feedback prompt to both users
- **next_command**: Shows feedback prompt before finding new partner
- **chat_command**: Checks for toxic user limitation
- **MatchingEngine.find_partner()**: Validates user not toxic
- **MatchingEngine._find_compatible_partner()**: Prioritizes by rating

## User Experience

### Positive Feedback Loop
1. User is respectful and friendly
2. Partner rates them 👍 Good
3. Rating score increases
4. User gets matched faster (priority queue)
5. Encouraged to maintain good behavior

### Negative Feedback Consequences
1. User is toxic or abusive
2. Multiple partners rate them 👎 Bad
3. Rating score drops below 30%
4. After 5 bad ratings: Account limited
5. Cannot use `/chat` until score improves

### Recovery Mechanism
- Limited users can still receive chats (if someone rates them positively)
- Each good rating helps recover score
- Once score rises above 30%, limitation lifted
- Encourages behavior improvement

## Benefits

### For Users
- ✅ Better match quality (avoid toxic users)
- ✅ Faster matching for good users (priority)
- ✅ Community self-regulation
- ✅ Anonymous and fair system

### For System
- ✅ Reduces moderation burden
- ✅ Toxic users naturally filtered out
- ✅ Encourages positive behavior
- ✅ Data for future improvements

## Configuration

### Toxic User Thresholds
```python
# In UserRating.is_toxic property
TOXIC_SCORE_THRESHOLD = 30.0  # Below 30%
TOXIC_MIN_RATINGS = 5  # At least 5 ratings needed
```

### Good User Thresholds
```python
# In UserRating.is_good_user property
GOOD_SCORE_THRESHOLD = 70.0  # At or above 70%
GOOD_MIN_RATINGS = 3  # At least 3 ratings needed
```

### Timeouts
```python
FEEDBACK_SESSION_TTL = 86400  # 24 hours (duplicate prevention)
PENDING_FEEDBACK_TTL = 300  # 5 minutes (prompt expiry)
```

## Rating Categories Breakdown

| Score | Category | Emoji | Min Ratings | Effect |
|-------|----------|-------|-------------|--------|
| 80-100% | Excellent | 🌟 | 3+ | Highest priority matching |
| 60-79% | Good | 😊 | 3+ | High priority matching |
| 40-59% | Neutral | 😐 | Any | Normal matching |
| 30-39% | Needs Improvement | 😔 | 5+ | Low priority matching |
| 0-29% | Toxic | 😔 | 5+ | Blocked from matching |

## Anti-Abuse Measures

1. **Duplicate Rating Prevention**
   - 24-hour lock per chat session
   - Prevents rating manipulation

2. **Minimum Rating Requirement**
   - Toxic status requires 5+ ratings
   - Prevents false positives from few bad ratings

3. **Anonymous Ratings**
   - No way to know who rated you
   - Prevents retaliation

4. **Fair Default Score**
   - New users start at 50% (neutral)
   - Not penalized for being new

5. **Gradual Limitations**
   - Need multiple bad ratings to be limited
   - One bad rating won't ruin account

## Future Enhancements

Potential improvements:
- **Rating Reasons**: Optional context for bad ratings
- **Appeal System**: Manual review for disputed limitations
- **Rating Decay**: Old ratings matter less over time
- **Detailed Analytics**: View rating trends over time
- **Leaderboard**: Top-rated users (opt-in)
- **Reputation Badges**: Visual indicators for good users
- **Smart Matching**: Weight compatibility + rating together
- **Report Integration**: Link reports with ratings

## Testing Scenarios

### Test Case 1: New User
- User A (new): 0 ratings, score 50%
- Should match normally
- Not limited, normal priority

### Test Case 2: Good User
- User B: 8 positive, 2 negative = 80%
- Should get priority matching
- Matched before neutral users

### Test Case 3: Toxic User
- User C: 2 positive, 8 negative = 20% (10 total)
- Should be blocked from `/chat`
- Shows limitation message

### Test Case 4: Recovery
- User C gets 3 good ratings
- New score: 5 positive, 8 negative = 38%
- Still low priority but can match again

### Test Case 5: Duplicate Rating
- User A rates User B as Good
- User A tries to rate User B again
- Shows "already rated" message

## Monitoring Metrics

Key metrics to track:
- Average rating score across all users
- Percentage of toxic users
- Rating distribution (excellent/good/neutral/poor)
- Ratings per chat (engagement rate)
- Time to limitation for toxic users
- Recovery rate for limited users

## Privacy & Ethics

- ✅ **Fully Anonymous**: No identifying information in ratings
- ✅ **Fair System**: Requires multiple ratings for limitation
- ✅ **Transparent**: Users see their own scores
- ✅ **Recoverable**: Limited users can improve
- ✅ **Optional**: Users can skip rating
- ✅ **Community-Driven**: No manual admin intervention needed

---

**Feature Status**: ✅ Fully Implemented and Tested
**Version**: 1.0
**Last Updated**: December 2025
