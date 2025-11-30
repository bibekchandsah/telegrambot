"""Queue management system with atomic operations."""
from typing import Optional
from src.db.redis_client import RedisClient
from src.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Lua script for atomic queue pop-and-pair operation
# This prevents race conditions when multiple users try to join simultaneously
ATOMIC_PAIR_SCRIPT = """
local user_id = ARGV[1]
local queue_key = KEYS[1]

-- Try to pop a waiting user from the queue
local partner_id = redis.call('RPOP', queue_key)

if partner_id then
    -- Found a partner, return their ID
    return partner_id
else
    -- No partner available, add to queue
    redis.call('LPUSH', queue_key, user_id)
    return nil
end
"""


class QueueManager:
    """Manages the waiting queue for users looking for chat partners."""
    
    QUEUE_KEY = "queue:waiting"
    
    def __init__(self, redis: RedisClient):
        self.redis = redis
    
    async def join_queue(self, user_id: int) -> Optional[int]:
        """
        Join the waiting queue atomically.
        
        Returns:
            Partner ID if a match was found, None if added to queue
        """
        try:
            # Check queue size limit
            queue_size = await self.redis.llen(self.QUEUE_KEY)
            if queue_size >= Config.MAX_QUEUE_SIZE:
                logger.warning(
                    "queue_full",
                    user_id=user_id,
                    queue_size=queue_size,
                )
                raise QueueFullError("Queue is full, please try again later")
            
            # Use Lua script for atomic operation
            result = await self.redis.eval(
                ATOMIC_PAIR_SCRIPT,
                1,  # Number of keys
                self.QUEUE_KEY,
                str(user_id),
            )
            
            partner_id = int(result) if result else None
            
            if partner_id:
                logger.info(
                    "match_found",
                    user_id=user_id,
                    partner_id=partner_id,
                )
            else:
                logger.info(
                    "added_to_queue",
                    user_id=user_id,
                    queue_size=await self.redis.llen(self.QUEUE_KEY),
                )
            
            return partner_id
            
        except Exception as e:
            logger.error(
                "queue_join_error",
                user_id=user_id,
                error=str(e),
            )
            raise
    
    async def leave_queue(self, user_id: int) -> bool:
        """
        Remove user from waiting queue.
        
        Returns:
            True if user was in queue, False otherwise
        """
        try:
            removed = await self.redis.lrem(
                self.QUEUE_KEY,
                0,  # Remove all occurrences
                str(user_id),
            )
            
            if removed > 0:
                logger.info(
                    "left_queue",
                    user_id=user_id,
                    removed_count=removed,
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(
                "queue_leave_error",
                user_id=user_id,
                error=str(e),
            )
            raise
    
    async def get_queue_size(self) -> int:
        """Get current queue size."""
        try:
            return await self.redis.llen(self.QUEUE_KEY)
        except Exception as e:
            logger.error("queue_size_error", error=str(e))
            return 0
    
    async def is_in_queue(self, user_id: int) -> bool:
        """Check if user is currently in queue."""
        try:
            state = await self.redis.get(f"state:{user_id}")
            return state and state.decode() == "IN_QUEUE"
        except Exception as e:
            logger.error(
                "queue_check_error",
                user_id=user_id,
                error=str(e),
            )
            return False
    
    async def get_all_in_queue(self) -> list[int]:
        """
        Get all user IDs currently in the queue.
        
        Returns:
            List of user IDs in the queue
        """
        try:
            queue_items = await self.redis.lrange(self.QUEUE_KEY, 0, -1)
            return [int(user_id) for user_id in queue_items]
        except Exception as e:
            logger.error("queue_get_all_error", error=str(e))
            return []


class QueueFullError(Exception):
    """Raised when queue reaches maximum capacity."""
    pass
