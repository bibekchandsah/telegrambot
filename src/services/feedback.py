"""Anonymous feedback and rating system."""
import json
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from src.db.redis_client import RedisClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


class UserRating:
    """User rating data class."""
    
    def __init__(
        self,
        user_id: int,
        positive_ratings: int = 0,
        negative_ratings: int = 0,
        total_chats: int = 0,
    ):
        self.user_id = user_id
        self.positive_ratings = positive_ratings
        self.negative_ratings = negative_ratings
        self.total_chats = total_chats
    
    @property
    def rating_score(self) -> float:
        """
        Calculate rating score (0-100).
        Formula: (positive / total_rated) * 100
        Returns 50 (neutral) if no ratings yet.
        """
        total_rated = self.positive_ratings + self.negative_ratings
        if total_rated == 0:
            return 50.0  # Neutral score for new users
        
        return (self.positive_ratings / total_rated) * 100
    
    @property
    def is_toxic(self) -> bool:
        """
        Check if user is considered toxic.
        Toxic if: score < 30% AND has at least 5 ratings
        """
        total_rated = self.positive_ratings + self.negative_ratings
        return total_rated >= 5 and self.rating_score < 30.0
    
    @property
    def is_good_user(self) -> bool:
        """
        Check if user has good reputation.
        Good if: score >= 70% AND has at least 3 ratings
        """
        total_rated = self.positive_ratings + self.negative_ratings
        return total_rated >= 3 and self.rating_score >= 70.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "positive_ratings": self.positive_ratings,
            "negative_ratings": self.negative_ratings,
            "total_chats": self.total_chats,
            "rating_score": round(self.rating_score, 2),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "UserRating":
        """Create from dictionary."""
        return cls(
            user_id=data["user_id"],
            positive_ratings=data.get("positive_ratings", 0),
            negative_ratings=data.get("negative_ratings", 0),
            total_chats=data.get("total_chats", 0),
        )
    
    def to_display(self) -> str:
        """Format rating for display."""
        total_rated = self.positive_ratings + self.negative_ratings
        score = self.rating_score
        
        # Rating emoji
        if score >= 80:
            emoji = "🌟"
            status = "Excellent"
        elif score >= 60:
            emoji = "😊"
            status = "Good"
        elif score >= 40:
            emoji = "😐"
            status = "Neutral"
        else:
            emoji = "😔"
            status = "Needs Improvement"
        
        return (
            f"{emoji} **Rating: {status}**\n"
            f"📊 Score: {score:.1f}%\n"
            f"👍 Positive: {self.positive_ratings}\n"
            f"👎 Negative: {self.negative_ratings}\n"
            f"💬 Total Chats: {self.total_chats}"
        )


class FeedbackManager:
    """Manages user feedback and ratings."""
    
    def __init__(self, redis: RedisClient):
        self.redis = redis
    
    async def record_feedback(
        self,
        rater_id: int,
        rated_user_id: int,
        is_positive: bool,
    ) -> bool:
        """
        Record feedback from one user to another.
        
        Args:
            rater_id: User who is giving the rating
            rated_user_id: User being rated
            is_positive: True for positive rating, False for negative
            
        Returns:
            True if feedback recorded, False if already rated in this session
        """
        try:
            # Use timestamp-based key to allow re-rating in different sessions
            # But prevent duplicate ratings within 1 hour (for same chat session)
            import time
            current_hour = int(time.time() / 3600)  # Hour-based grouping
            feedback_key = f"feedback:{rater_id}:{rated_user_id}:{current_hour}"
            
            # Use SET NX (set if not exists) to prevent duplicate ratings
            was_set = await self.redis.set(
                feedback_key,
                "rated",
                ex=3600,  # 1 hour expiry
                nx=True,  # Only set if doesn't exist
            )
            
            if not was_set:
                logger.warning(
                    "duplicate_feedback_attempt",
                    rater_id=rater_id,
                    rated_user_id=rated_user_id,
                )
                return False
            
            # Update rated user's rating
            rating = await self.get_rating(rated_user_id)
            
            if is_positive:
                rating.positive_ratings += 1
            else:
                rating.negative_ratings += 1
            
            # Save updated rating
            await self._save_rating(rating)
            
            logger.info(
                "feedback_recorded",
                rater_id=rater_id,
                rated_user_id=rated_user_id,
                is_positive=is_positive,
                new_score=rating.rating_score,
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "feedback_record_error",
                rater_id=rater_id,
                rated_user_id=rated_user_id,
                error=str(e),
            )
            raise
    
    async def increment_chat_count(self, user_id: int):
        """Increment user's total chat count."""
        try:
            rating = await self.get_rating(user_id)
            rating.total_chats += 1
            await self._save_rating(rating)
            
            logger.debug("chat_count_incremented", user_id=user_id)
            
        except Exception as e:
            logger.error(
                "chat_count_increment_error",
                user_id=user_id,
                error=str(e),
            )
    
    async def get_rating(self, user_id: int) -> UserRating:
        """
        Get user's rating.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            UserRating object (creates new if doesn't exist)
        """
        try:
            rating_key = f"rating:{user_id}"
            data = await self.redis.get(rating_key)
            
            if not data:
                # Return new rating
                return UserRating(user_id=user_id)
            
            rating_dict = json.loads(data.decode())
            return UserRating.from_dict(rating_dict)
            
        except Exception as e:
            logger.error(
                "rating_get_error",
                user_id=user_id,
                error=str(e),
            )
            # Return default on error
            return UserRating(user_id=user_id)
    
    async def _save_rating(self, rating: UserRating):
        """Save rating to Redis."""
        try:
            rating_key = f"rating:{rating.user_id}"
            await self.redis.set(
                rating_key,
                json.dumps(rating.to_dict()),
                ex=None,  # Permanent
            )
        except Exception as e:
            logger.error(
                "rating_save_error",
                user_id=rating.user_id,
                error=str(e),
            )
            raise
    
    async def is_user_limited(self, user_id: int) -> tuple[bool, str]:
        """
        Check if user should be limited due to toxic behavior.
        
        Returns:
            (is_limited, reason)
        """
        try:
            rating = await self.get_rating(user_id)
            
            if rating.is_toxic:
                return True, (
                    f"Your account has been limited due to negative feedback.\n"
                    f"Current rating: {rating.rating_score:.1f}%\n"
                    f"Improve your behavior to regain full access."
                )
            
            return False, ""
            
        except Exception as e:
            logger.error(
                "user_limit_check_error",
                user_id=user_id,
                error=str(e),
            )
            return False, ""
    
    async def get_user_reputation_level(self, user_id: int) -> str:
        """
        Get user's reputation level for matching priority.
        
        Returns:
            "excellent", "good", "neutral", "poor"
        """
        try:
            rating = await self.get_rating(user_id)
            score = rating.rating_score
            
            if score >= 80:
                return "excellent"
            elif score >= 60:
                return "good"
            elif score >= 40:
                return "neutral"
            else:
                return "poor"
                
        except Exception as e:
            logger.error(
                "reputation_level_error",
                user_id=user_id,
                error=str(e),
            )
            return "neutral"
    
    async def has_rated_partner(self, rater_id: int, partner_id: int) -> bool:
        """
        Check if user has already rated their partner in this session (within current hour).
        
        Args:
            rater_id: User who would rate
            partner_id: Partner to be rated
            
        Returns:
            True if already rated in current hour
        """
        try:
            import time
            current_hour = int(time.time() / 3600)
            feedback_key = f"feedback:{rater_id}:{partner_id}:{current_hour}"
            exists = await self.redis.exists(feedback_key)
            return bool(exists)
            
        except Exception as e:
            logger.error(
                "rated_check_error",
                rater_id=rater_id,
                partner_id=partner_id,
                error=str(e),
            )
            return False
    
    async def get_top_users(self, limit: int = 10) -> List[UserRating]:
        """
        Get top-rated users (for leaderboard feature).
        
        Args:
            limit: Maximum number of users to return
            
        Returns:
            List of UserRating objects sorted by score
        """
        try:
            # Get all rating keys
            keys = await self.redis.keys("rating:*")
            
            ratings = []
            for key in keys[:100]:  # Limit to first 100 for performance
                data = await self.redis.get(key)
                if data:
                    rating_dict = json.loads(data.decode())
                    rating = UserRating.from_dict(rating_dict)
                    
                    # Only include users with at least 3 ratings
                    total_rated = rating.positive_ratings + rating.negative_ratings
                    if total_rated >= 3:
                        ratings.append(rating)
            
            # Sort by score descending
            ratings.sort(key=lambda r: r.rating_score, reverse=True)
            
            return ratings[:limit]
            
        except Exception as e:
            logger.error("top_users_error", error=str(e))
            return []


def get_feedback_prompt() -> tuple[str, List[List[Dict]]]:
    """
    Get feedback prompt message and inline keyboard.
    
    Returns:
        (message_text, inline_keyboard_buttons)
    """
    message = (
        "💭 **How was your chat?**\n\n"
        "Please rate your partner to help improve the community:"
    )
    
    keyboard = [
        [
            {"text": "👍 Good", "callback_data": "feedback_positive"},
            {"text": "👎 Bad", "callback_data": "feedback_negative"},
        ],
        [
            {"text": "⏭️ Skip Rating", "callback_data": "feedback_skip"},
        ],
    ]
    
    return message, keyboard
