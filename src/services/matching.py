"""Matching engine for pairing users."""
from typing import Optional, Tuple
from src.db.redis_client import RedisClient
from src.services.queue import QueueManager
from src.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MatchingEngine:
    """Handles user pairing and chat state management."""
    
    def __init__(self, redis: RedisClient):
        self.redis = redis
        self.queue = QueueManager(redis)
    
    async def find_partner(self, user_id: int) -> Optional[int]:
        """
        Find a chat partner for the user.
        
        Returns:
            Partner ID if found, None if added to queue
        """
        try:
            # Check if user is already in a chat or queue
            state = await self.get_user_state(user_id)
            if state in ["IN_CHAT", "IN_QUEUE"]:
                logger.warning(
                    "user_already_active",
                    user_id=user_id,
                    state=state,
                )
                return None
            
            # Set user state to IN_QUEUE
            await self.set_user_state(user_id, "IN_QUEUE")
            
            # Try to find a partner
            partner_id = await self.queue.join_queue(user_id)
            
            if partner_id:
                # Match found, create the pair
                await self.create_pair(user_id, partner_id)
                return partner_id
            
            # No partner found, user is now waiting
            return None
            
        except Exception as e:
            logger.error(
                "find_partner_error",
                user_id=user_id,
                error=str(e),
            )
            # Clean up on error
            await self.set_user_state(user_id, "IDLE")
            await self.queue.leave_queue(user_id)
            raise
    
    async def create_pair(self, user1_id: int, user2_id: int):
        """
        Create a bidirectional pair between two users.
        
        Both users' pair mappings are stored with TTL for auto-cleanup.
        """
        try:
            # Use pipeline for atomic operation
            pipe = self.redis.pipeline(transaction=True)
            
            # Store bidirectional pairing
            pipe.set(f"pair:{user1_id}", str(user2_id), ex=Config.CHAT_TIMEOUT)
            pipe.set(f"pair:{user2_id}", str(user1_id), ex=Config.CHAT_TIMEOUT)
            
            # Update states to IN_CHAT
            pipe.set(f"state:{user1_id}", "IN_CHAT", ex=Config.CHAT_TIMEOUT)
            pipe.set(f"state:{user2_id}", "IN_CHAT", ex=Config.CHAT_TIMEOUT)
            
            await pipe.execute()
            
            logger.info(
                "pair_created",
                user1=user1_id,
                user2=user2_id,
            )
            
        except Exception as e:
            logger.error(
                "create_pair_error",
                user1=user1_id,
                user2=user2_id,
                error=str(e),
            )
            raise
    
    async def end_chat(self, user_id: int) -> Optional[int]:
        """
        End the chat for a user and their partner.
        
        Returns:
            Partner ID if they were in a chat, None otherwise
        """
        try:
            # Get partner ID
            partner_id = await self.get_partner(user_id)
            
            if not partner_id:
                logger.warning(
                    "no_active_chat",
                    user_id=user_id,
                )
                return None
            
            # Use pipeline for atomic cleanup
            pipe = self.redis.pipeline(transaction=True)
            
            # Delete pair mappings
            pipe.delete(f"pair:{user_id}", f"pair:{partner_id}")
            
            # Update states to IDLE
            pipe.set(f"state:{user_id}", "IDLE", ex=3600)
            pipe.set(f"state:{partner_id}", "IDLE", ex=3600)
            
            await pipe.execute()
            
            logger.info(
                "chat_ended",
                user_id=user_id,
                partner_id=partner_id,
            )
            
            return partner_id
            
        except Exception as e:
            logger.error(
                "end_chat_error",
                user_id=user_id,
                error=str(e),
            )
            raise
    
    async def get_partner(self, user_id: int) -> Optional[int]:
        """Get the partner ID for a user."""
        try:
            partner = await self.redis.get(f"pair:{user_id}")
            return int(partner) if partner else None
        except Exception as e:
            logger.error(
                "get_partner_error",
                user_id=user_id,
                error=str(e),
            )
            return None
    
    async def get_user_state(self, user_id: int) -> str:
        """Get current state of a user."""
        try:
            state = await self.redis.get(f"state:{user_id}")
            return state.decode() if state else "IDLE"
        except Exception as e:
            logger.error(
                "get_state_error",
                user_id=user_id,
                error=str(e),
            )
            return "IDLE"
    
    async def set_user_state(self, user_id: int, state: str):
        """Set user state with TTL."""
        try:
            await self.redis.set(
                f"state:{user_id}",
                state,
                ex=Config.CHAT_TIMEOUT,
            )
        except Exception as e:
            logger.error(
                "set_state_error",
                user_id=user_id,
                state=state,
                error=str(e),
            )
            raise
    
    async def is_in_chat(self, user_id: int) -> bool:
        """Check if user is currently in a chat."""
        partner = await self.get_partner(user_id)
        return partner is not None
    
    async def get_active_pairs_count(self) -> int:
        """Get count of active chat pairs."""
        try:
            keys = await self.redis.keys("pair:*")
            # Divide by 2 since each pair has two entries
            return len(keys) // 2
        except Exception as e:
            logger.error("active_pairs_count_error", error=str(e))
            return 0
