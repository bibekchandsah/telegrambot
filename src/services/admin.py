"""Admin management for broadcast messages."""
import json
from typing import List, Optional, Dict
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
    
    async def register_user(self, user_id: int, username: str = None, first_name: str = None, 
                           last_name: str = None, language_code: str = None, 
                           is_bot: bool = False, is_premium: bool = False) -> None:
        """
        Register a user in the bot (called when they use /start).
        
        Args:
            user_id: Telegram user ID
            username: Telegram username (optional)
            first_name: Telegram first name (optional)
            last_name: Telegram last name (optional)
            language_code: User's language code (optional)
            is_bot: Whether user is a bot (optional)
            is_premium: Whether user has Telegram Premium (optional)
        """
        try:
            import json
            import time
            
            # Add user to a set of all users
            await self.redis.sadd("bot:all_users", str(user_id))
            
            # Check if user already exists to preserve account_created_at
            user_info_key = f"user_info:{user_id}"
            existing_data = await self.redis.get(user_info_key)
            account_created_at = None
            
            if existing_data:
                try:
                    existing_info = json.loads(existing_data.decode('utf-8'))
                    account_created_at = existing_info.get('account_created_at')
                except:
                    pass
            
            # If no existing timestamp, set it now (first registration)
            if not account_created_at:
                account_created_at = int(time.time())
            
            # Store user info (username and name)
            if username or first_name:
                user_info = {
                    'username': username,
                    'first_name': first_name,
                    'last_name': last_name,
                    'language_code': language_code,
                    'is_bot': is_bot,
                    'is_premium': is_premium,
                    'account_created_at': account_created_at,
                    'last_activity_at': int(time.time())
                }
                await self.redis.set(
                    user_info_key,
                    json.dumps(user_info),
                    ex=None  # No expiry
                )
            
            logger.debug("user_registered", user_id=user_id, username=username)
        except Exception as e:
            logger.error("register_user_error", user_id=user_id, error=str(e))
    
    async def increment_message_count(self, user_id: int) -> None:
        """
        Increment user's message count.
        
        Args:
            user_id: Telegram user ID
        """
        try:
            key = f"stats:{user_id}:messages"
            await self.redis.incr(key)
        except Exception as e:
            logger.error("increment_message_count_error", user_id=user_id, error=str(e))
    
    async def increment_chat_count(self, user_id: int) -> None:
        """
        Increment user's completed chat count.
        
        Args:
            user_id: Telegram user ID
        """
        try:
            key = f"stats:{user_id}:chats"
            await self.redis.incr(key)
        except Exception as e:
            logger.error("increment_chat_count_error", user_id=user_id, error=str(e))
    
    async def get_user_stats(self, user_id: int) -> Dict[str, int]:
        """
        Get user statistics.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Dict with message_count and chat_count
        """
        try:
            message_count = await self.redis.get(f"stats:{user_id}:messages")
            chat_count = await self.redis.get(f"stats:{user_id}:chats")
            
            return {
                'message_count': int(message_count) if message_count else 0,
                'chat_count': int(chat_count) if chat_count else 0
            }
        except Exception as e:
            logger.error("get_user_stats_error", user_id=user_id, error=str(e))
            return {'message_count': 0, 'chat_count': 0}
    
    async def track_chat_start(self, user_id: int) -> None:
        """
        Track when a user starts a chat.
        
        Args:
            user_id: Telegram user ID
        """
        try:
            import time
            key = f"stats:{user_id}:chat_start"
            await self.redis.set(key, int(time.time()), ex=86400)  # 24 hour expiry
        except Exception as e:
            logger.error("track_chat_start_error", user_id=user_id, error=str(e))
    
    async def track_chat_end(self, user_id: int) -> None:
        """
        Track when a user ends a chat and calculate duration.
        
        Args:
            user_id: Telegram user ID
        """
        try:
            import time
            start_key = f"stats:{user_id}:chat_start"
            start_time = await self.redis.get(start_key)
            
            if start_time:
                duration = int(time.time()) - int(start_time)
                
                # Update total chat time
                total_key = f"stats:{user_id}:total_chat_time"
                await self.redis.incrby(total_key, duration)
                
                # Add to chat durations list (for average calculation)
                durations_key = f"stats:{user_id}:chat_durations"
                await self.redis.lpush(durations_key, duration)
                await self.redis.ltrim(durations_key, 0, 99)  # Keep last 100 chats
                
                # Clean up start time
                await self.redis.delete(start_key)
        except Exception as e:
            logger.error("track_chat_end_error", user_id=user_id, error=str(e))
    
    async def track_queue_join(self, user_id: int) -> None:
        """
        Track when a user joins the queue.
        
        Args:
            user_id: Telegram user ID
        """
        try:
            import time
            key = f"stats:{user_id}:queue_join"
            await self.redis.set(key, int(time.time()), ex=3600)  # 1 hour expiry
        except Exception as e:
            logger.error("track_queue_join_error", user_id=user_id, error=str(e))
    
    async def track_queue_leave(self, user_id: int) -> None:
        """
        Track when a user leaves the queue and calculate wait time.
        
        Args:
            user_id: Telegram user ID
        """
        try:
            import time
            join_key = f"stats:{user_id}:queue_join"
            join_time = await self.redis.get(join_key)
            
            if join_time:
                wait_time = int(time.time()) - int(join_time)
                
                # Update total queue time
                total_key = f"stats:{user_id}:total_queue_time"
                await self.redis.incrby(total_key, wait_time)
                
                # Increment queue sessions count
                sessions_key = f"stats:{user_id}:queue_sessions"
                await self.redis.incr(sessions_key)
                
                # Clean up join time
                await self.redis.delete(join_key)
        except Exception as e:
            logger.error("track_queue_leave_error", user_id=user_id, error=str(e))
    
    async def increment_skip_count(self, user_id: int) -> None:
        """
        Increment user's skip count (when they use /next).
        
        Args:
            user_id: Telegram user ID
        """
        try:
            key = f"stats:{user_id}:skips"
            await self.redis.incr(key)
        except Exception as e:
            logger.error("increment_skip_count_error", user_id=user_id, error=str(e))
    
    async def record_report(self, reported_user_id: int, reporter_id: int, reason: str = None) -> None:
        """
        Record when a user is reported.
        
        Args:
            reported_user_id: User who was reported
            reporter_id: User who made the report
            reason: Optional reason for report
        """
        try:
            import time
            import json
            
            report_data = {
                'reporter_id': reporter_id,
                'reported_at': int(time.time()),
                'reason': reason
            }
            
            # Add to user's report history
            key = f"stats:{reported_user_id}:reports"
            await self.redis.lpush(key, json.dumps(report_data))
            await self.redis.ltrim(key, 0, 49)  # Keep last 50 reports
            
            # Increment report count
            count_key = f"stats:{reported_user_id}:report_count"
            await self.redis.incr(count_key)
            
            # Check for auto-ban threshold
            await self.check_auto_ban_threshold(reported_user_id)
        except Exception as e:
            logger.error("record_report_error", reported_user_id=reported_user_id, error=str(e))
    
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
    
    # ============================================
    # BAN / UNBAN SYSTEM
    # ============================================
    
    async def ban_user(
        self,
        user_id: int,
        banned_by: int,
        reason: str,
        duration: Optional[int] = None,
        is_auto_ban: bool = False,
    ) -> bool:
        """
        Ban a user (temporary or permanent).
        
        Args:
            user_id: User to ban
            banned_by: Admin who banned the user
            reason: Ban reason (nudity, spam, abuse, fake_reports, harassment)
            duration: Ban duration in seconds (None for permanent)
            is_auto_ban: Whether this is an automatic ban from reports
            
        Returns:
            True if ban was successful
        """
        try:
            import time
            import json
            
            timestamp = int(time.time())
            expires_at = timestamp + duration if duration else None
            
            ban_data = {
                "user_id": user_id,
                "banned_by": banned_by,
                "reason": reason,
                "banned_at": timestamp,
                "expires_at": expires_at,
                "is_permanent": expires_at is None,
                "is_auto_ban": is_auto_ban,
            }
            
            # Store ban info
            ban_key = f"ban:{user_id}"
            await self.redis.set(
                ban_key,
                json.dumps(ban_data),
                ex=duration if duration else None,  # Auto-expire for temporary bans
            )
            
            # Add to banned users set
            await self.redis.sadd("bot:banned_users", str(user_id))
            
            # Store ban history
            history_key = f"ban_history:{user_id}"
            await self.redis.lpush(history_key, json.dumps(ban_data))
            await self.redis.ltrim(history_key, 0, 49)  # Keep last 50 bans
            
            # Remove from warning list if present
            await self.redis.srem("bot:warning_list", str(user_id))
            
            logger.info(
                "user_banned",
                user_id=user_id,
                banned_by=banned_by,
                reason=reason,
                duration=duration,
                is_auto_ban=is_auto_ban,
            )
            
            return True
            
        except Exception as e:
            logger.error("ban_user_error", user_id=user_id, error=str(e))
            return False
    
    async def unban_user(self, user_id: int, unbanned_by: int) -> bool:
        """
        Unban a user.
        
        Args:
            user_id: User to unban
            unbanned_by: Admin who unbanned the user
            
        Returns:
            True if unban was successful
        """
        try:
            import time
            import json
            
            # Remove ban info
            ban_key = f"ban:{user_id}"
            await self.redis.delete(ban_key)
            
            # Remove from banned users set
            await self.redis.srem("bot:banned_users", str(user_id))
            
            # Record unban in history
            unban_data = {
                "user_id": user_id,
                "unbanned_by": unbanned_by,
                "unbanned_at": int(time.time()),
            }
            
            history_key = f"unban_history:{user_id}"
            await self.redis.lpush(history_key, json.dumps(unban_data))
            await self.redis.ltrim(history_key, 0, 49)  # Keep last 50 unbans
            
            logger.info(
                "user_unbanned",
                user_id=user_id,
                unbanned_by=unbanned_by,
            )
            
            return True
            
        except Exception as e:
            logger.error("unban_user_error", user_id=user_id, error=str(e))
            return False
    
    async def is_user_banned(self, user_id: int) -> tuple[bool, Optional[Dict]]:
        """
        Check if user is banned.
        
        Args:
            user_id: User to check
            
        Returns:
            (is_banned, ban_data) - ban_data is None if not banned
        """
        try:
            import json
            
            ban_key = f"ban:{user_id}"
            ban_data_bytes = await self.redis.get(ban_key)
            
            if not ban_data_bytes:
                return False, None
            
            ban_data = json.loads(ban_data_bytes.decode('utf-8'))
            
            # Check if temporary ban has expired
            if ban_data.get("expires_at"):
                import time
                if time.time() > ban_data["expires_at"]:
                    # Ban expired, remove it
                    await self.unban_user(user_id, 0)  # System unban
                    return False, None
            
            return True, ban_data
            
        except Exception as e:
            logger.error("is_user_banned_error", user_id=user_id, error=str(e))
            return False, None
    
    async def add_warning(self, user_id: int, warned_by: int, reason: str) -> int:
        """
        Add a warning to a user.
        
        Args:
            user_id: User to warn
            warned_by: Admin who issued the warning
            reason: Warning reason
            
        Returns:
            Total number of warnings for this user
        """
        try:
            import time
            import json
            
            warning_data = {
                "user_id": user_id,
                "warned_by": warned_by,
                "reason": reason,
                "warned_at": int(time.time()),
            }
            
            # Store warning
            warning_key = f"warnings:{user_id}"
            await self.redis.lpush(warning_key, json.dumps(warning_data))
            await self.redis.ltrim(warning_key, 0, 99)  # Keep last 100 warnings
            
            # Increment warning count
            count_key = f"warning_count:{user_id}"
            warning_count = await self.redis.incr(count_key)
            
            # Add to warning list
            await self.redis.sadd("bot:warning_list", str(user_id))
            
            logger.info(
                "warning_added",
                user_id=user_id,
                warned_by=warned_by,
                reason=reason,
                total_warnings=warning_count,
            )
            
            return warning_count
            
        except Exception as e:
            logger.error("add_warning_error", user_id=user_id, error=str(e))
            return 0
    
    async def get_warning_count(self, user_id: int) -> int:
        """
        Get total warning count for a user.
        
        Args:
            user_id: User to check
            
        Returns:
            Warning count
        """
        try:
            count_key = f"warning_count:{user_id}"
            count = await self.redis.get(count_key)
            return int(count) if count else 0
        except Exception as e:
            logger.error("get_warning_count_error", user_id=user_id, error=str(e))
            return 0
    
    async def is_on_warning_list(self, user_id: int) -> bool:
        """
        Check if user is on the warning list.
        
        Args:
            user_id: User to check
            
        Returns:
            True if on warning list
        """
        try:
            is_member = await self.redis.smembers("bot:warning_list")
            return str(user_id).encode() in is_member or str(user_id) in is_member
        except Exception as e:
            logger.error("is_on_warning_list_error", user_id=user_id, error=str(e))
            return False
    
    async def remove_from_warning_list(self, user_id: int) -> bool:
        """
        Remove user from warning list.
        
        Args:
            user_id: User to remove
            
        Returns:
            True if successful
        """
        try:
            await self.redis.srem("bot:warning_list", str(user_id))
            logger.info("removed_from_warning_list", user_id=user_id)
            return True
        except Exception as e:
            logger.error("remove_from_warning_list_error", user_id=user_id, error=str(e))
            return False
    
    async def check_auto_ban_threshold(self, user_id: int) -> bool:
        """
        Check if user has reached auto-ban threshold based on reports.
        
        Args:
            user_id: User to check
            
        Returns:
            True if auto-ban threshold reached
        """
        try:
            # Get report count
            count_key = f"stats:{user_id}:report_count"
            report_count_bytes = await self.redis.get(count_key)
            report_count = int(report_count_bytes) if report_count_bytes else 0
            
            # Auto-ban threshold: 5 reports
            AUTO_BAN_THRESHOLD = 5
            
            if report_count >= AUTO_BAN_THRESHOLD:
                # Check if already banned
                is_banned, _ = await self.is_user_banned(user_id)
                if not is_banned:
                    # Auto-ban for 7 days (604800 seconds)
                    await self.ban_user(
                        user_id=user_id,
                        banned_by=0,  # System ban
                        reason="abuse",  # Auto-ban from reports
                        duration=604800,  # 7 days
                        is_auto_ban=True,
                    )
                    logger.warning(
                        "auto_ban_triggered",
                        user_id=user_id,
                        report_count=report_count,
                    )
                    return True
            
            return False
            
        except Exception as e:
            logger.error("check_auto_ban_threshold_error", user_id=user_id, error=str(e))
            return False
    
    async def get_ban_info(self, user_id: int) -> Optional[Dict]:
        """
        Get detailed ban information for a user.
        
        Args:
            user_id: User to check
            
        Returns:
            Ban data dictionary or None if not banned
        """
        try:
            import json
            
            ban_key = f"ban:{user_id}"
            ban_data_bytes = await self.redis.get(ban_key)
            
            if not ban_data_bytes:
                return None
            
            return json.loads(ban_data_bytes.decode('utf-8'))
            
        except Exception as e:
            logger.error("get_ban_info_error", user_id=user_id, error=str(e))
            return None
    
    async def get_banned_users_list(self) -> List[int]:
        """
        Get list of all banned users.
        
        Returns:
            List of banned user IDs
        """
        try:
            banned_set = await self.redis.smembers("bot:banned_users")
            user_ids = []
            for user_id_bytes in banned_set:
                try:
                    if isinstance(user_id_bytes, bytes):
                        user_id_bytes = user_id_bytes.decode('utf-8')
                    user_ids.append(int(user_id_bytes))
                except (ValueError, AttributeError):
                    continue
            return user_ids
        except Exception as e:
            logger.error("get_banned_users_list_error", error=str(e))
            return []
    
    async def get_warning_list(self) -> List[int]:
        """
        Get list of all users on warning list.
        
        Returns:
            List of user IDs on warning list
        """
        try:
            warning_set = await self.redis.smembers("bot:warning_list")
            user_ids = []
            for user_id_bytes in warning_set:
                try:
                    if isinstance(user_id_bytes, bytes):
                        user_id_bytes = user_id_bytes.decode('utf-8')
                    user_ids.append(int(user_id_bytes))
                except (ValueError, AttributeError):
                    continue
            return user_ids
        except Exception as e:
            logger.error("get_warning_list_error", error=str(e))
            return []
    
    async def get_users_by_filters(
        self, 
        gender: Optional[str] = None, 
        country: Optional[str] = None
    ) -> List[int]:
        """
        Get list of users matching specific profile filters.
        
        Args:
            gender: Filter by gender (Male/Female/Other) - None means any
            country: Filter by country name - None means any
            
        Returns:
            List of user IDs matching the filters
        """
        try:
            matching_users = []
            
            # Scan all profile keys
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
                        
                        # Get the profile data
                        profile_data = await self.redis.get(key)
                        if not profile_data:
                            continue
                        
                        if isinstance(profile_data, bytes):
                            profile_data = profile_data.decode('utf-8')
                        
                        profile_dict = json.loads(profile_data)
                        user_id = profile_dict.get("user_id")
                        
                        # Apply filters
                        gender_match = gender is None or profile_dict.get("gender") == gender
                        country_match = country is None or profile_dict.get("country", "").lower() == country.lower()
                        
                        if gender_match and country_match:
                            matching_users.append(user_id)
                            
                    except (IndexError, ValueError, json.JSONDecodeError) as e:
                        logger.debug("parse_profile_error", key=key, error=str(e))
                        continue
                
                if cursor == 0:
                    break
            
            logger.info(
                "filtered_users_retrieved",
                count=len(matching_users),
                gender_filter=gender,
                country_filter=country
            )
            
            return matching_users
            
        except Exception as e:
            logger.error(
                "get_users_by_filters_error",
                gender=gender,
                country=country,
                error=str(e)
            )
            return []
