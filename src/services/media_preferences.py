"""Media privacy preferences management."""
from dataclasses import dataclass, asdict
from typing import Optional
import json
from src.db.redis_client import RedisClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MediaPreferences:
    """User's media privacy preferences."""
    
    allow_images: bool = True
    allow_videos: bool = True
    allow_voice: bool = True
    allow_audio: bool = True
    allow_documents: bool = True
    allow_stickers: bool = True
    allow_video_notes: bool = True
    allow_locations: bool = True
    text_only: bool = False  # If True, all media types are blocked
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "MediaPreferences":
        """Create from dictionary."""
        return cls(**data)
    
    def get_blocked_types(self) -> list[str]:
        """Get list of blocked media types."""
        blocked = []
        if self.text_only:
            return ["all media"]
        
        if not self.allow_images:
            blocked.append("images")
        if not self.allow_videos:
            blocked.append("videos")
        if not self.allow_voice:
            blocked.append("voice notes")
        if not self.allow_audio:
            blocked.append("audio")
        if not self.allow_documents:
            blocked.append("documents")
        if not self.allow_stickers:
            blocked.append("stickers")
        if not self.allow_video_notes:
            blocked.append("video notes")
        if not self.allow_locations:
            blocked.append("locations")
        
        return blocked


class MediaPreferenceManager:
    """Manages user media privacy preferences."""
    
    def __init__(self, redis: RedisClient):
        self.redis = redis
    
    async def get_preferences(self, user_id: int) -> MediaPreferences:
        """
        Get user's media preferences.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            MediaPreferences object with user's settings
        """
        try:
            key = f"media_prefs:{user_id}"
            data = await self.redis.get(key)
            
            if data:
                prefs_dict = json.loads(data)
                return MediaPreferences.from_dict(prefs_dict)
            
            # Return default preferences (all allowed)
            return MediaPreferences()
            
        except Exception as e:
            logger.error(
                "get_media_preferences_error",
                user_id=user_id,
                error=str(e),
            )
            return MediaPreferences()
    
    async def set_preferences(
        self,
        user_id: int,
        preferences: MediaPreferences,
    ) -> bool:
        """
        Save user's media preferences.
        
        Args:
            user_id: Telegram user ID
            preferences: MediaPreferences object
            
        Returns:
            True if saved successfully
        """
        try:
            key = f"media_prefs:{user_id}"
            data = json.dumps(preferences.to_dict())
            await self.redis.set(key, data)
            
            logger.info(
                "media_preferences_saved",
                user_id=user_id,
                text_only=preferences.text_only,
            )
            return True
            
        except Exception as e:
            logger.error(
                "set_media_preferences_error",
                user_id=user_id,
                error=str(e),
            )
            return False
    
    async def update_preference(
        self,
        user_id: int,
        preference_key: str,
        value: bool,
    ) -> bool:
        """
        Update a specific media preference.
        
        Args:
            user_id: Telegram user ID
            preference_key: Key to update (e.g., 'allow_images')
            value: New boolean value
            
        Returns:
            True if updated successfully
        """
        try:
            preferences = await self.get_preferences(user_id)
            
            # Update the specific preference
            if hasattr(preferences, preference_key):
                setattr(preferences, preference_key, value)
                return await self.set_preferences(user_id, preferences)
            
            logger.warning(
                "invalid_preference_key",
                user_id=user_id,
                key=preference_key,
            )
            return False
            
        except Exception as e:
            logger.error(
                "update_preference_error",
                user_id=user_id,
                error=str(e),
            )
            return False
    
    async def set_text_only(self, user_id: int, enabled: bool) -> bool:
        """
        Enable or disable text-only mode.
        
        Args:
            user_id: Telegram user ID
            enabled: True to enable text-only, False to allow media
            
        Returns:
            True if updated successfully
        """
        return await self.update_preference(user_id, "text_only", enabled)
    
    async def is_media_allowed(
        self,
        user_id: int,
        media_type: str,
    ) -> tuple[bool, Optional[str]]:
        """
        Check if a specific media type is allowed for user.
        
        Args:
            user_id: Telegram user ID
            media_type: Type of media (photo, video, voice, audio, document, 
                       sticker, video_note, location)
            
        Returns:
            Tuple of (is_allowed, reason_if_blocked)
        """
        try:
            preferences = await self.get_preferences(user_id)
            
            # Text-only mode blocks all media
            if preferences.text_only:
                return False, "This user only accepts text messages."
            
            # Check specific media type
            media_map = {
                "photo": preferences.allow_images,
                "video": preferences.allow_videos,
                "voice": preferences.allow_voice,
                "audio": preferences.allow_audio,
                "document": preferences.allow_documents,
                "sticker": preferences.allow_stickers,
                "video_note": preferences.allow_video_notes,
                "location": preferences.allow_locations,
            }
            
            allowed = media_map.get(media_type, True)
            
            if not allowed:
                media_names = {
                    "photo": "images",
                    "video": "videos",
                    "voice": "voice notes",
                    "audio": "audio files",
                    "document": "documents",
                    "sticker": "stickers",
                    "video_note": "video notes",
                    "location": "locations",
                }
                reason = f"This user has disabled receiving {media_names.get(media_type, media_type)}."
                return False, reason
            
            return True, None
            
        except Exception as e:
            logger.error(
                "is_media_allowed_error",
                user_id=user_id,
                media_type=media_type,
                error=str(e),
            )
            # Default to allowing on error
            return True, None
