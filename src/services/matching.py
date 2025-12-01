"""Matching engine for pairing users."""
from typing import Optional, Tuple
from src.db.redis_client import RedisClient
from src.services.queue import QueueManager
from src.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MatchingEngine:
    """Handles user pairing and chat state management."""
    
    def __init__(self, redis: RedisClient, profile_manager=None, preference_manager=None, feedback_manager=None):
        self.redis = redis
        self.queue = QueueManager(redis)
        self.profile_manager = profile_manager
        self.preference_manager = preference_manager
        self.feedback_manager = feedback_manager
    
    async def find_partner(self, user_id: int) -> Optional[int]:
        """
        Find a chat partner for the user based on preferences.
        
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
            
            # Check if user is limited due to toxic behavior
            if self.feedback_manager:
                is_limited, limit_reason = await self.feedback_manager.is_user_limited(user_id)
                if is_limited:
                    logger.warning("user_limited", user_id=user_id)
                    raise Exception(limit_reason)
            
            # Set user state to IN_QUEUE
            await self.set_user_state(user_id, "IN_QUEUE")
            
            # Get user's profile and preferences for matching
            user_profile = None
            user_preferences = None
            
            if self.profile_manager:
                user_profile = await self.profile_manager.get_profile(user_id)
            
            if self.preference_manager:
                user_preferences = await self.preference_manager.get_preferences(user_id)
            
            # Try to find a compatible partner
            partner_id = await self._find_compatible_partner(
                user_id, user_profile, user_preferences
            )
            
            if partner_id:
                # Match found, create the pair
                await self.create_pair(user_id, partner_id)
                
                # Increment chat counts for both users
                if self.feedback_manager:
                    await self.feedback_manager.increment_chat_count(user_id)
                    await self.feedback_manager.increment_chat_count(partner_id)
                
                return partner_id
            
            # No compatible partner found, add to queue
            await self.queue.join_queue(user_id)
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
    
    async def _find_compatible_partner(
        self,
        user_id: int,
        user_profile,
        user_preferences,
    ) -> Optional[int]:
        """
        Find a compatible partner from the queue based on mutual preferences and ratings.
        
        Prioritizes users with good ratings.
        
        Checks:
        1. User's preferences match potential partner's profile
        2. Potential partner's preferences match user's profile
        3. Filters out toxic users
        4. Prioritizes partners with good ratings
        
        Returns:
            Partner ID if compatible match found, None otherwise
        """
        try:
            # Get all users in queue
            queue_users = await self.queue.get_all_in_queue()
            
            if not queue_users:
                return None
            
            # Build list of compatible partners with their ratings
            compatible_partners = []
            
            for potential_partner_id in queue_users:
                if potential_partner_id == user_id:
                    continue
                
                # Skip toxic users
                if self.feedback_manager:
                    partner_rating = await self.feedback_manager.get_rating(potential_partner_id)
                    if partner_rating.is_toxic:
                        logger.debug(
                            "skipping_toxic_user",
                            user_id=user_id,
                            partner_id=potential_partner_id,
                        )
                        continue
                
                # Get potential partner's profile and preferences
                partner_profile = None
                partner_preferences = None
                
                if self.profile_manager:
                    partner_profile = await self.profile_manager.get_profile(
                        potential_partner_id
                    )
                
                if self.preference_manager:
                    partner_preferences = await self.preference_manager.get_preferences(
                        potential_partner_id
                    )
                
                # Check mutual compatibility
                if await self._are_compatible(
                    user_profile,
                    user_preferences,
                    partner_profile,
                    partner_preferences,
                ):
                    # Get partner's rating score for prioritization
                    rating_score = 50.0  # Default neutral score
                    if self.feedback_manager:
                        partner_rating = await self.feedback_manager.get_rating(
                            potential_partner_id
                        )
                        rating_score = partner_rating.rating_score
                    
                    compatible_partners.append((potential_partner_id, rating_score))
            
            if not compatible_partners:
                return None
            
            # Sort by rating score (highest first) for priority matching
            compatible_partners.sort(key=lambda x: x[1], reverse=True)
            
            # Select the best-rated compatible partner
            best_partner_id, best_score = compatible_partners[0]
            
            # Remove partner from queue
            await self.queue.leave_queue(best_partner_id)
            
            logger.info(
                "compatible_match_found",
                user_id=user_id,
                partner_id=best_partner_id,
                partner_score=best_score,
            )
            
            return best_partner_id
            
        except Exception as e:
            logger.error(
                "find_compatible_partner_error",
                user_id=user_id,
                error=str(e),
            )
            return None
    
    async def _are_compatible(
        self,
        user_profile,
        user_preferences,
        partner_profile,
        partner_preferences,
    ) -> bool:
        """
        Check if two users are compatible based on mutual preferences.
        
        Returns:
            True if both users match each other's preferences
        """
        # If profiles or preferences are missing, allow match (backwards compatibility)
        if not user_profile or not partner_profile:
            return True
        
        if not user_preferences or not partner_preferences:
            return True
        
        # Check if user's preferences match partner's profile
        # Gender filter
        if user_preferences.gender_filter != "Any":
            if partner_profile.gender != user_preferences.gender_filter:
                return False
        
        # Country filter
        if user_preferences.country_filter != "Any":
            if partner_profile.country != user_preferences.country_filter:
                return False
        
        # Check if partner's preferences match user's profile
        # Gender filter
        if partner_preferences.gender_filter != "Any":
            if user_profile.gender != partner_preferences.gender_filter:
                return False
        
        # Country filter
        if partner_preferences.country_filter != "Any":
            if user_profile.country != partner_preferences.country_filter:
                return False
        
        # Both users match each other's preferences
        return True
    
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
