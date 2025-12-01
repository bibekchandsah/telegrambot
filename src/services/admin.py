"""Admin management for broadcast messages."""
from typing import List, Optional
from src.db.redis_client import RedisClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AdminManager:
    """Manages admin operations and broadcast functionality."""
    
    def __init__(self, redis: RedisClient, admin_ids: List[int]):
        """
        Initialize admin manager.
        
        Args:
            redis: Redis client instance
            admin_ids: List of Telegram user IDs who are admins
        """
        self.redis = redis
        self.admin_ids = set(admin_ids)
    
    def is_admin(self, user_id: int) -> bool:
        """
        Check if user is an admin.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if user is admin
        """
        return user_id in self.admin_ids
    
    async def register_user(self, user_id: int) -> None:
        """
        Register a user in the bot (called when they use /start).
        
        Args:
            user_id: Telegram user ID
        """
        try:
            # Add user to a set of all users
            await self.redis.sadd("bot:all_users", str(user_id))
            logger.debug("user_registered", user_id=user_id)
        except Exception as e:
            logger.error("register_user_error", user_id=user_id, error=str(e))
    
    async def get_all_users(self) -> List[int]:
        """
        Get list of all users who have interacted with the bot.
        
        Returns:
            List of user IDs
        """
        try:
            user_ids = set()
            
            # First try to get from the dedicated user set
            try:
                all_users_set = await self.redis.smembers("bot:all_users")
                for user_id_bytes in all_users_set:
                    try:
                        if isinstance(user_id_bytes, bytes):
                            user_id_bytes = user_id_bytes.decode('utf-8')
                        user_ids.add(int(user_id_bytes))
                    except (ValueError, AttributeError):
                        continue
            except Exception:
                pass
            
            # Fallback: Scan for user data in Redis keys
            # Get all users who have profiles
            pattern = "profile:*"
            cursor = 0
            
            while True:
                cursor, partial_keys = await self.redis.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100,
                )
                
                for key in partial_keys:
                    try:
                        if isinstance(key, bytes):
                            key = key.decode('utf-8')
                        user_id = int(key.split(':')[1])
                        user_ids.add(user_id)
                    except (IndexError, ValueError):
                        continue
                
                if cursor == 0:
                    break
            
            # Also get users from state keys (they've used /start or commands)
            state_pattern = "state:*"
            cursor = 0
            
            while True:
                cursor, partial_keys = await self.redis.scan(
                    cursor=cursor,
                    match=state_pattern,
                    count=100,
                )
                
                for key in partial_keys:
                    try:
                        if isinstance(key, bytes):
                            key = key.decode('utf-8')
                        user_id = int(key.split(':')[1])
                        user_ids.add(user_id)
                    except (IndexError, ValueError):
                        continue
                
                if cursor == 0:
                    break
            
            # Also get users from rating keys
            rating_pattern = "rating:*"
            cursor = 0
            
            while True:
                cursor, partial_keys = await self.redis.scan(
                    cursor=cursor,
                    match=rating_pattern,
                    count=100,
                )
                
                for key in partial_keys:
                    try:
                        if isinstance(key, bytes):
                            key = key.decode('utf-8')
                        user_id = int(key.split(':')[1])
                        user_ids.add(user_id)
                    except (IndexError, ValueError):
                        continue
                
                if cursor == 0:
                    break
            
            # Also get users from preferences keys
            pref_pattern = "preferences:*"
            cursor = 0
            
            while True:
                cursor, partial_keys = await self.redis.scan(
                    cursor=cursor,
                    match=pref_pattern,
                    count=100,
                )
                
                for key in partial_keys:
                    try:
                        if isinstance(key, bytes):
                            key = key.decode('utf-8')
                        user_id = int(key.split(':')[1])
                        user_ids.add(user_id)
                    except (IndexError, ValueError):
                        continue
                
                if cursor == 0:
                    break
            
            # Get users in pairs (active chats)
            pair_pattern = "pair:*"
            cursor = 0
            
            while True:
                cursor, partial_keys = await self.redis.scan(
                    cursor=cursor,
                    match=pair_pattern,
                    count=100,
                )
                
                for key in partial_keys:
                    try:
                        if isinstance(key, bytes):
                            key = key.decode('utf-8')
                        user_id = int(key.split(':')[1])
                        user_ids.add(user_id)
                    except (IndexError, ValueError):
                        continue
                
                if cursor == 0:
                    break
            
            logger.info("fetched_all_users", count=len(user_ids))
            return list(user_ids)
            
        except Exception as e:
            logger.error("get_all_users_error", error=str(e))
            return []
    
    async def get_active_users(self) -> List[int]:
        """
        Get list of users currently in chat or queue.
        
        Returns:
            List of user IDs
        """
        try:
            user_ids = set()
            
            # Get users in the waiting queue (single key: queue:waiting)
            queue_key = "queue:waiting"
            members = await self.redis.lrange(queue_key, 0, -1)
            for member in members:
                if isinstance(member, bytes):
                    member = member.decode('utf-8')
                try:
                    user_ids.add(int(member))
                except ValueError:
                    continue
            
            # Get users in active chats (pair:user_id keys)
            pair_pattern = "pair:*"
            cursor = 0
            
            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match=pair_pattern,
                    count=100,
                )
                
                for key in keys:
                    if isinstance(key, bytes):
                        key = key.decode('utf-8')
                    
                    try:
                        user_id = int(key.split(':')[1])
                        user_ids.add(user_id)
                    except (IndexError, ValueError):
                        continue
                
                if cursor == 0:
                    break
            
            logger.info("fetched_active_users", count=len(user_ids))
            return list(user_ids)
            
        except Exception as e:
            logger.error("get_active_users_error", error=str(e))
            return []
    
    async def record_broadcast(
        self,
        admin_id: int,
        message: str,
        target_type: str,
        success_count: int,
        failed_count: int,
    ) -> None:
        """
        Record broadcast message in history.
        
        Args:
            admin_id: Admin who sent the broadcast
            message: Broadcast message content
            target_type: Type of recipients (all/active)
            success_count: Number of successful deliveries
            failed_count: Number of failed deliveries
        """
        try:
            import time
            timestamp = int(time.time())
            
            key = f"broadcast:{timestamp}:{admin_id}"
            data = {
                "admin_id": admin_id,
                "message": message[:200],  # Store first 200 chars
                "target_type": target_type,
                "success": success_count,
                "failed": failed_count,
                "timestamp": timestamp,
            }
            
            import json
            await self.redis.set(key, json.dumps(data), ex=2592000)  # 30 days
            
            logger.info(
                "broadcast_recorded",
                admin_id=admin_id,
                target_type=target_type,
                success=success_count,
                failed=failed_count,
            )
            
        except Exception as e:
            logger.error("record_broadcast_error", error=str(e))
