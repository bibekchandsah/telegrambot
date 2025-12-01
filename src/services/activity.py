"""User activity tracking for typing indicators and online status."""
from typing import Optional
from src.db.redis_client import RedisClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ActivityManager:
    """Manages user activity status and typing indicators."""
    
    def __init__(self, redis: RedisClient):
        self.redis = redis
    
    async def set_online(self, user_id: int):
        """
        Mark user as online.
        
        Args:
            user_id: Telegram user ID
        """
        try:
            online_key = f"online:{user_id}"
            await self.redis.set(online_key, "1", ex=30)  # 30 second expiry
            
            logger.debug("user_online", user_id=user_id)
            
        except Exception as e:
            logger.error("set_online_error", user_id=user_id, error=str(e))
    
    async def is_online(self, user_id: int) -> bool:
        """
        Check if user is online.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if user is online (active in last 30 seconds)
        """
        try:
            online_key = f"online:{user_id}"
            return await self.redis.exists(online_key)
            
        except Exception as e:
            logger.error("is_online_error", user_id=user_id, error=str(e))
            return False
    
    async def set_typing(self, user_id: int):
        """
        Mark user as currently typing.
        
        Args:
            user_id: Telegram user ID
        """
        try:
            typing_key = f"typing:{user_id}"
            await self.redis.set(typing_key, "1", ex=5)  # 5 second expiry
            
            logger.debug("user_typing", user_id=user_id)
            
        except Exception as e:
            logger.error("set_typing_error", user_id=user_id, error=str(e))
    
    async def is_typing(self, user_id: int) -> bool:
        """
        Check if user is currently typing.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if user is typing (typed in last 5 seconds)
        """
        try:
            typing_key = f"typing:{user_id}"
            return await self.redis.exists(typing_key)
            
        except Exception as e:
            logger.error("is_typing_error", user_id=user_id, error=str(e))
            return False
    
    async def get_status_text(self, user_id: int) -> str:
        """
        Get user's current status text.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Status text ("🟢 Online" or "⚫ Offline")
        """
        try:
            if await self.is_online(user_id):
                return "🟢 Online"
            return "⚫ Offline"
            
        except Exception as e:
            logger.error("get_status_text_error", user_id=user_id, error=str(e))
            return "⚫ Offline"
