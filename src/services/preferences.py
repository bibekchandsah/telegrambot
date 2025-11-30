"""User preference management for matching filters."""
import json
from typing import Optional, Dict
from src.db.redis_client import RedisClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


class UserPreferences:
    """User matching preferences data class."""
    
    def __init__(self, user_id: int, gender_filter: str = "Any", country_filter: str = "Any"):
        self.user_id = user_id
        self.gender_filter = gender_filter  # "Male", "Female", "Any"
        self.country_filter = country_filter  # Country name or "Any"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "gender_filter": self.gender_filter,
            "country_filter": self.country_filter,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "UserPreferences":
        """Create from dictionary."""
        return cls(
            user_id=data["user_id"],
            gender_filter=data.get("gender_filter", "Any"),
            country_filter=data.get("country_filter", "Any"),
        )
    
    def to_display(self) -> str:
        """Format preferences for display."""
        gender_emoji = {
            "Male": "👨",
            "Female": "👩",
            "Any": "🧑",
        }
        
        country_emoji = "🌍" if self.country_filter == "Any" else "📍"
        
        return (
            f"⚙️ **Your Matching Preferences**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"{gender_emoji.get(self.gender_filter, '🧑')} Gender: {self.gender_filter}\n"
            f"{country_emoji} Country: {self.country_filter}"
        )


class PreferenceManager:
    """Manages user matching preferences."""
    
    def __init__(self, redis: RedisClient):
        self.redis = redis
    
    async def set_preferences(
        self,
        user_id: int,
        gender_filter: Optional[str] = None,
        country_filter: Optional[str] = None,
    ) -> UserPreferences:
        """
        Set or update user preferences.
        
        Args:
            user_id: Telegram user ID
            gender_filter: Gender filter ("Male"/"Female"/"Any")
            country_filter: Country filter (country name or "Any")
            
        Returns:
            Updated UserPreferences object
        """
        try:
            # Get existing preferences or create default
            existing = await self.get_preferences(user_id)
            
            if existing:
                # Update only provided fields
                if gender_filter is not None:
                    existing.gender_filter = gender_filter
                if country_filter is not None:
                    existing.country_filter = country_filter
                preferences = existing
            else:
                # Create new preferences
                preferences = UserPreferences(
                    user_id=user_id,
                    gender_filter=gender_filter or "Any",
                    country_filter=country_filter or "Any",
                )
            
            # Store in Redis
            pref_key = f"preferences:{user_id}"
            await self.redis.set(
                pref_key,
                json.dumps(preferences.to_dict()),
                ex=None,  # No expiry - permanent until deleted
            )
            
            logger.info(
                "preferences_set",
                user_id=user_id,
                gender_filter=preferences.gender_filter,
                country_filter=preferences.country_filter,
            )
            
            return preferences
            
        except Exception as e:
            logger.error(
                "preferences_set_error",
                user_id=user_id,
                error=str(e),
            )
            raise
    
    async def get_preferences(self, user_id: int) -> Optional[UserPreferences]:
        """
        Get user preferences.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            UserPreferences if exists, None otherwise (defaults to "Any" for both)
        """
        try:
            pref_key = f"preferences:{user_id}"
            data = await self.redis.get(pref_key)
            
            if not data:
                # Return default preferences
                return UserPreferences(user_id=user_id, gender_filter="Any", country_filter="Any")
            
            pref_dict = json.loads(data.decode())
            return UserPreferences.from_dict(pref_dict)
            
        except Exception as e:
            logger.error(
                "preferences_get_error",
                user_id=user_id,
                error=str(e),
            )
            # Return default on error
            return UserPreferences(user_id=user_id, gender_filter="Any", country_filter="Any")
    
    async def delete_preferences(self, user_id: int) -> bool:
        """
        Delete user preferences (reset to defaults).
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if deleted, False if didn't exist
        """
        try:
            pref_key = f"preferences:{user_id}"
            deleted = await self.redis.delete(pref_key)
            
            if deleted:
                logger.info("preferences_deleted", user_id=user_id)
                return True
            
            return False
            
        except Exception as e:
            logger.error(
                "preferences_delete_error",
                user_id=user_id,
                error=str(e),
            )
            raise
    
    async def has_preferences(self, user_id: int) -> bool:
        """
        Check if user has set custom preferences (not defaults).
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if preferences exist in Redis
        """
        try:
            pref_key = f"preferences:{user_id}"
            return await self.redis.exists(pref_key)
        except Exception as e:
            logger.error(
                "preferences_exists_check_error",
                user_id=user_id,
                error=str(e),
            )
            return False


# Gender filter options
GENDER_FILTERS = ["Male", "Female", "Any"]


def validate_gender_filter(gender: str) -> tuple[bool, str]:
    """
    Validate gender filter.
    
    Returns:
        (is_valid, error_message)
    """
    if gender not in GENDER_FILTERS:
        return False, f"Gender must be one of: {', '.join(GENDER_FILTERS)}"
    
    return True, ""


def validate_country_filter(country: str) -> tuple[bool, str]:
    """
    Validate country filter.
    
    Returns:
        (is_valid, error_message)
    """
    # Import COUNTRIES from profile service
    from src.services.profile import COUNTRIES
    
    if country not in COUNTRIES and country != "Any":
        return False, "Please select a valid country or 'Any'"
    
    return True, ""
