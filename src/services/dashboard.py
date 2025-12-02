"""Dashboard service for admin panel."""
import json
from typing import List, Dict, Optional, Any
from src.db.redis_client import RedisClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DashboardService:
    """Service for admin dashboard operations."""
    
    def __init__(self, redis: RedisClient):
        """Initialize dashboard service."""
        self.redis = redis
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall dashboard statistics.
        
        Returns:
            Dict with statistics about users, chats, queue
        """
        try:
            # Get all user IDs
            all_users_set = await self.redis.smembers("bot:all_users")
            total_users = len(all_users_set)
            
            # Get users in queue
            queue_count = await self.redis.llen("queue:waiting")
            
            # Get users in chat (pairs)
            pair_pattern = "pair:*"
            cursor = 0
            chat_count = 0
            
            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match=pair_pattern,
                    count=100
                )
                chat_count += len(keys)
                if cursor == 0:
                    break
            
            # Active users = in queue + in chat
            active_users = queue_count + chat_count
            
            # Get users with profiles
            profile_pattern = "profile:*"
            cursor = 0
            profile_count = 0
            
            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match=profile_pattern,
                    count=100
                )
                profile_count += len(keys)
                if cursor == 0:
                    break
            
            return {
                "total_users": total_users,
                "users_with_profiles": profile_count,
                "active_users": active_users,
                "users_in_queue": queue_count,
                "users_in_chat": chat_count
            }
        except Exception as e:
            logger.error("get_statistics_error", error=str(e))
            return {
                "total_users": 0,
                "users_with_profiles": 0,
                "active_users": 0,
                "users_in_queue": 0,
                "users_in_chat": 0
            }
    
    async def get_all_users_paginated(self, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        Get all users with pagination.
        
        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            
        Returns:
            Dict with users list and pagination info
        """
        try:
            # Get all users
            all_users_set = await self.redis.smembers("bot:all_users")
            user_ids = []
            
            for user_id_bytes in all_users_set:
                try:
                    if isinstance(user_id_bytes, bytes):
                        user_id_bytes = user_id_bytes.decode('utf-8')
                    user_ids.append(int(user_id_bytes))
                except (ValueError, AttributeError):
                    continue
            
            # Sort user IDs
            user_ids.sort()
            
            # Calculate pagination
            total = len(user_ids)
            total_pages = (total + per_page - 1) // per_page
            start = (page - 1) * per_page
            end = start + per_page
            
            # Get user details for this page
            page_user_ids = user_ids[start:end]
            users = []
            
            for user_id in page_user_ids:
                user_info = await self._get_user_info(user_id)
                users.append(user_info)
            
            return {
                "users": users,
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages
            }
        except Exception as e:
            logger.error("get_all_users_paginated_error", error=str(e))
            return {
                "users": [],
                "page": page,
                "per_page": per_page,
                "total": 0,
                "total_pages": 0
            }
    
    async def get_online_users(self) -> List[Dict[str, Any]]:
        """
        Get currently online/active users (in queue or chat).
        
        Returns:
            List of user info dicts
        """
        try:
            user_ids = set()
            
            # Get users in queue
            queue_members = await self.redis.lrange("queue:waiting", 0, -1)
            for member in queue_members:
                if isinstance(member, bytes):
                    member = member.decode('utf-8')
                try:
                    user_ids.add(int(member))
                except ValueError:
                    continue
            
            # Get users in chat
            pair_pattern = "pair:*"
            cursor = 0
            
            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match=pair_pattern,
                    count=100
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
            
            # Get user details
            users = []
            for user_id in user_ids:
                user_info = await self._get_user_info(user_id)
                users.append(user_info)
            
            return users
        except Exception as e:
            logger.error("get_online_users_error", error=str(e))
            return []
    
    async def get_users_in_chat(self) -> List[Dict[str, Any]]:
        """
        Get users currently in chat.
        
        Returns:
            List of user info dicts with partner info
        """
        try:
            user_ids = set()
            pair_pattern = "pair:*"
            cursor = 0
            
            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match=pair_pattern,
                    count=100
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
            
            # Get user details with partner info
            users = []
            for user_id in user_ids:
                user_info = await self._get_user_info(user_id)
                
                # Get partner ID
                pair_key = f"pair:{user_id}"
                partner_id_bytes = await self.redis.get(pair_key)
                if partner_id_bytes:
                    try:
                        partner_id = int(partner_id_bytes.decode('utf-8'))
                        user_info['partner_id'] = partner_id
                    except (ValueError, AttributeError):
                        pass
                
                users.append(user_info)
            
            return users
        except Exception as e:
            logger.error("get_users_in_chat_error", error=str(e))
            return []
    
    async def get_users_in_queue(self) -> List[Dict[str, Any]]:
        """
        Get users currently in queue.
        
        Returns:
            List of user info dicts
        """
        try:
            user_ids = []
            queue_members = await self.redis.lrange("queue:waiting", 0, -1)
            
            for member in queue_members:
                if isinstance(member, bytes):
                    member = member.decode('utf-8')
                try:
                    user_ids.append(int(member))
                except ValueError:
                    continue
            
            # Get user details
            users = []
            for user_id in user_ids:
                user_info = await self._get_user_info(user_id)
                users.append(user_info)
            
            return users
        except Exception as e:
            logger.error("get_users_in_queue_error", error=str(e))
            return []
    
    async def search_users(
        self,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        gender: Optional[str] = None,
        country: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search users by various criteria.
        
        Args:
            user_id: User ID to search for
            username: Username to search for (partial match)
            gender: Gender filter
            country: Country filter
            
        Returns:
            List of matching user info dicts
        """
        try:
            matching_users = []
            
            # If searching by user_id, just get that user
            if user_id:
                try:
                    uid = int(user_id)
                    user_info = await self._get_user_info(uid)
                    if user_info['user_id'] != 0:  # User exists
                        matching_users.append(user_info)
                    return matching_users
                except ValueError:
                    return []
            
            # Otherwise, get all users and filter
            all_users_set = await self.redis.smembers("bot:all_users")
            
            for user_id_bytes in all_users_set:
                try:
                    if isinstance(user_id_bytes, bytes):
                        user_id_bytes = user_id_bytes.decode('utf-8')
                    uid = int(user_id_bytes)
                    
                    user_info = await self._get_user_info(uid)
                    
                    # Apply filters
                    matches = True
                    
                    if username:
                        user_username = user_info.get('username', '').lower()
                        if username.lower() not in user_username:
                            matches = False
                    
                    if gender:
                        if user_info.get('gender', '').lower() != gender.lower():
                            matches = False
                    
                    if country:
                        if user_info.get('country', '').lower() != country.lower():
                            matches = False
                    
                    if matches:
                        matching_users.append(user_info)
                
                except (ValueError, AttributeError):
                    continue
            
            return matching_users
        except Exception as e:
            logger.error("search_users_error", error=str(e))
            return []
    
    async def get_user_details(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with user details or None
        """
        try:
            user_info = await self._get_user_info(user_id)
            
            if user_info['user_id'] == 0:
                return None
            
            # Get additional details
            # Check if in queue
            queue_members = await self.redis.lrange("queue:waiting", 0, -1)
            user_info['in_queue'] = str(user_id).encode() in queue_members or str(user_id) in [
                m.decode('utf-8') if isinstance(m, bytes) else m for m in queue_members
            ]
            
            # Check if in chat
            pair_key = f"pair:{user_id}"
            partner_id_bytes = await self.redis.get(pair_key)
            if partner_id_bytes:
                try:
                    partner_id = int(partner_id_bytes.decode('utf-8'))
                    user_info['in_chat'] = True
                    user_info['partner_id'] = partner_id
                except (ValueError, AttributeError):
                    user_info['in_chat'] = False
            else:
                user_info['in_chat'] = False
            
            # Get preferences
            pref_key = f"preferences:{user_id}"
            pref_bytes = await self.redis.get(pref_key)
            if pref_bytes:
                try:
                    preferences = json.loads(pref_bytes.decode('utf-8'))
                    user_info['preferences'] = preferences
                except (json.JSONDecodeError, AttributeError):
                    user_info['preferences'] = {}
            else:
                user_info['preferences'] = {}
            
            # Get state
            state_key = f"state:{user_id}"
            state_bytes = await self.redis.get(state_key)
            if state_bytes:
                try:
                    user_info['state'] = state_bytes.decode('utf-8')
                except AttributeError:
                    user_info['state'] = str(state_bytes)
            else:
                user_info['state'] = 'unknown'
            
            # Get user statistics
            message_count = await self.redis.get(f"stats:{user_id}:messages")
            user_info['message_count'] = int(message_count) if message_count else 0
            
            # Get user rating (includes total_chats which has historical data)
            rating_key = f"rating:{user_id}"
            rating_bytes = await self.redis.get(rating_key)
            if rating_bytes:
                try:
                    rating_data = json.loads(rating_bytes.decode('utf-8'))
                    positive = rating_data.get('positive_ratings', 0)
                    negative = rating_data.get('negative_ratings', 0)
                    total_chats = rating_data.get('total_chats', 0)
                    total_rated = positive + negative
                    
                    # Calculate rating score (same formula as UserRating class)
                    if total_rated > 0:
                        rating_score = (positive / total_rated) * 100
                    else:
                        rating_score = 50.0  # Neutral for new users
                    
                    user_info['rating_score'] = round(rating_score, 2)
                    user_info['positive_ratings'] = positive
                    user_info['negative_ratings'] = negative
                    user_info['total_rated'] = total_rated
                    user_info['total_chats'] = total_chats  # Use this as the authoritative chat count
                    user_info['chat_count'] = total_chats  # Also set chat_count to match
                except (json.JSONDecodeError, AttributeError, ZeroDivisionError):
                    user_info['rating_score'] = 50.0
                    user_info['positive_ratings'] = 0
                    user_info['negative_ratings'] = 0
                    user_info['total_rated'] = 0
                    user_info['total_chats'] = 0
                    user_info['chat_count'] = 0
            else:
                user_info['rating_score'] = 50.0
                user_info['positive_ratings'] = 0
                user_info['negative_ratings'] = 0
                user_info['total_rated'] = 0
                user_info['total_chats'] = 0
                user_info['chat_count'] = 0
            
            return user_info
        except Exception as e:
            logger.error("get_user_details_error", user_id=user_id, error=str(e))
            return None
    
    async def get_user_chat_history(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get user's chat history.
        
        Args:
            user_id: User ID
            
        Returns:
            List of chat sessions
        """
        try:
            # Note: This implementation assumes chat history is stored
            # You may need to implement history storage in your bot
            history = []
            
            # Try to get from a hypothetical history key
            history_pattern = f"history:{user_id}:*"
            cursor = 0
            
            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match=history_pattern,
                    count=100
                )
                
                for key in keys:
                    if isinstance(key, bytes):
                        key = key.decode('utf-8')
                    
                    data_bytes = await self.redis.get(key)
                    if data_bytes:
                        try:
                            data = json.loads(data_bytes.decode('utf-8'))
                            history.append(data)
                        except (json.JSONDecodeError, AttributeError):
                            continue
                
                if cursor == 0:
                    break
            
            return history
        except Exception as e:
            logger.error("get_user_chat_history_error", user_id=user_id, error=str(e))
            return []
    
    async def _get_user_info(self, user_id: int) -> Dict[str, Any]:
        """
        Helper to get basic user info.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with user info
        """
        try:
            # Get Telegram username from user info (if stored)
            telegram_username = None
            first_name = None
            last_name = None
            language_code = None
            is_bot = None
            is_premium = None
            account_created_at = None
            last_activity_at = None
            user_info_key = f"user_info:{user_id}"
            user_info_bytes = await self.redis.get(user_info_key)
            
            if user_info_bytes:
                try:
                    user_info_data = json.loads(user_info_bytes.decode('utf-8'))
                    telegram_username = user_info_data.get('username')
                    first_name = user_info_data.get('first_name')
                    last_name = user_info_data.get('last_name')
                    language_code = user_info_data.get('language_code')
                    is_bot = user_info_data.get('is_bot')
                    is_premium = user_info_data.get('is_premium')
                    account_created_at = user_info_data.get('account_created_at')
                    last_activity_at = user_info_data.get('last_activity_at')
                except (json.JSONDecodeError, AttributeError):
                    pass
            
            # Get profile
            profile_key = f"profile:{user_id}"
            profile_bytes = await self.redis.get(profile_key)
            
            profile_nickname = None
            profile_data = {}
            
            if profile_bytes:
                try:
                    profile_data = json.loads(profile_bytes.decode('utf-8'))
                    profile_nickname = profile_data.get('nickname')
                except (json.JSONDecodeError, AttributeError):
                    pass
            
            # Build username display based on available info
            # Priority: @telegram_username (Profile Nickname) > @telegram_username > Profile Nickname > First Name > User ID
            username_display = f"User {user_id}"  # Fallback to showing user ID instead of N/A
            
            if telegram_username and profile_nickname:
                # Both telegram username and profile nickname exist
                username_display = f"@{telegram_username} ({profile_nickname})"
            elif telegram_username:
                # Only telegram username
                username_display = f"@{telegram_username}"
            elif profile_nickname:
                # Only profile nickname
                username_display = profile_nickname
            elif first_name:
                # Only first name
                username_display = first_name
            
            return {
                'user_id': user_id,
                'username': username_display,
                'first_name': first_name,
                'last_name': last_name,
                'language_code': language_code,
                'is_bot': is_bot,
                'is_premium': is_premium,
                'account_created_at': account_created_at,
                'last_activity_at': last_activity_at,
                'gender': profile_data.get('gender', 'N/A'),
                'country': profile_data.get('country', 'N/A')
            }
        except Exception as e:
            logger.error("_get_user_info_error", user_id=user_id, error=str(e))
            return {
                'user_id': 0,
                'username': 'Error',
                'first_name': None,
                'last_name': None,
                'language_code': None,
                'is_bot': None,
                'is_premium': None,
                'account_created_at': None,
                'last_activity_at': None,
                'gender': 'N/A',
                'country': 'N/A'
            }
