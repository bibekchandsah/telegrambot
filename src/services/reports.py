"""Report and Safety Management Service."""
import json
import time
from typing import Dict, List, Optional, Any
from src.db.redis_client import RedisClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ReportManager:
    """Manages user reports and safety moderation."""
    
    # Report flag types
    REPORT_FLAGS = {
        "nudity": "Nudity / Sexual Content",
        "harassment": "Harassment / Bullying",
        "spam": "Spam / Advertising",
        "scam": "Scam / Fraud",
        "fake": "Fake Profile",
        "other": "Other Violation"
    }
    
    # Media types that can be blocked
    MEDIA_TYPES = ["photo", "video", "voice", "sticker", "gif", "document"]
    
    def __init__(self, redis_client: RedisClient):
        """Initialize report manager."""
        self.redis = redis_client
    
    # ============================================
    # REPORT MANAGEMENT
    # ============================================
    
    async def get_all_reports(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all user reports across the platform.
        
        Args:
            limit: Maximum number of reports to retrieve
            
        Returns:
            List of report dictionaries with user info
        """
        try:
            # Get all users who have been reported
            all_users = await self.redis.keys("stats:*:reports")
            
            all_reports = []
            for key_bytes in all_users:
                try:
                    key = key_bytes.decode('utf-8') if isinstance(key_bytes, bytes) else key_bytes
                    user_id = int(key.split(':')[1])
                    
                    # Get report count
                    count_key = f"stats:{user_id}:report_count"
                    count_bytes = await self.redis.get(count_key)
                    report_count = int(count_bytes) if count_bytes else 0
                    
                    # Get recent reports
                    reports_bytes = await self.redis.lrange(key, 0, 9)  # Last 10
                    reports = []
                    flag_counts = {
                        "nudity": 0,
                        "harassment": 0,
                        "spam": 0,
                        "scam": 0,
                        "fake": 0,
                        "other": 0
                    }
                    
                    for report_bytes in reports_bytes:
                        try:
                            if isinstance(report_bytes, bytes):
                                report_bytes = report_bytes.decode('utf-8')
                            report_data = json.loads(report_bytes)
                            reports.append(report_data)
                            
                            # Count flags
                            flag = report_data.get('flag', 'other')
                            if flag in flag_counts:
                                flag_counts[flag] += 1
                        except:
                            continue
                    
                    # Check report status (approved/rejected/pending)
                    status = "pending"
                    approved_key = f"report:approvals:{user_id}"
                    rejected_key = f"report:rejections:{user_id}"
                    
                    # Get the most recent report timestamp
                    latest_report_timestamp = 0
                    if reports:
                        latest_report_timestamp = max([r.get('timestamp', 0) for r in reports])
                    
                    # Check if report was approved
                    approved_data = await self.redis.lrange(approved_key, 0, 0)
                    if approved_data:
                        try:
                            approval_bytes = approved_data[0]
                            if isinstance(approval_bytes, bytes):
                                approval_bytes = approval_bytes.decode('utf-8')
                            approval_info = json.loads(approval_bytes)
                            approval_time = approval_info.get('approved_at', 0)
                            # Only mark as approved if approval is more recent than latest report
                            if approval_time > latest_report_timestamp:
                                status = "approved"
                        except Exception as e:
                            logger.debug("parse_approval_error", error=str(e))
                            pass
                    
                    # Check if report was rejected (takes precedence if more recent)
                    rejected_data = await self.redis.lrange(rejected_key, 0, 0)
                    if rejected_data:
                        try:
                            rejection_bytes = rejected_data[0]
                            if isinstance(rejection_bytes, bytes):
                                rejection_bytes = rejection_bytes.decode('utf-8')
                            rejection_info = json.loads(rejection_bytes)
                            rejection_time = rejection_info.get('rejected_at', 0)
                            # Only mark as rejected if rejection is more recent than latest report
                            if rejection_time > latest_report_timestamp:
                                status = "rejected"
                        except Exception as e:
                            logger.debug("parse_rejection_error", error=str(e))
                            pass
                    
                    if reports:
                        all_reports.append({
                            "user_id": user_id,
                            "report_count": report_count,
                            "reports": reports,  # Changed from recent_reports
                            "flags": flag_counts,  # Added flag counts
                            "status": status  # Can be: pending, approved, rejected
                        })
                except Exception as e:
                    logger.debug("parse_report_error", error=str(e))
                    continue
            
            # Sort by report count (descending)
            all_reports.sort(key=lambda x: x['report_count'], reverse=True)
            
            return all_reports[:limit]
            
        except Exception as e:
            logger.error("get_all_reports_error", error=str(e))
            return []
    
    async def get_report_by_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get all reports for a specific user.
        
        Args:
            user_id: User to get reports for
            
        Returns:
            Report data dictionary or None
        """
        try:
            # Get report count
            count_key = f"stats:{user_id}:report_count"
            count_bytes = await self.redis.get(count_key)
            report_count = int(count_bytes) if count_bytes else 0
            
            if report_count == 0:
                return None
            
            # Get all reports
            reports_key = f"stats:{user_id}:reports"
            reports_bytes = await self.redis.lrange(reports_key, 0, -1)
            
            reports = []
            for report_bytes in reports_bytes:
                try:
                    if isinstance(report_bytes, bytes):
                        report_bytes = report_bytes.decode('utf-8')
                    report_data = json.loads(report_bytes)
                    reports.append(report_data)
                except:
                    continue
            
            return {
                "user_id": user_id,
                "report_count": report_count,
                "reports": reports
            }
            
        except Exception as e:
            logger.error("get_report_by_user_error", user_id=user_id, error=str(e))
            return None
    
    async def approve_report(self, user_id: int, admin_id: int) -> bool:
        """
        Approve a report (marks report as valid, may trigger action).
        
        Args:
            user_id: User whose report is approved
            admin_id: Admin approving the report
            
        Returns:
            True if successful
        """
        try:
            approval_data = {
                "user_id": user_id,
                "admin_id": admin_id,
                "approved_at": int(time.time()),
                "action": "approved"
            }
            
            # Store approval
            key = f"report:approvals:{user_id}"
            await self.redis.lpush(key, json.dumps(approval_data))
            await self.redis.ltrim(key, 0, 49)  # Keep last 50
            
            logger.info("report_approved", user_id=user_id, admin_id=admin_id)
            return True
            
        except Exception as e:
            logger.error("approve_report_error", user_id=user_id, error=str(e))
            return False
    
    async def reject_report(self, user_id: int, admin_id: int, reason: str = None) -> bool:
        """
        Reject a report (marks report as false/invalid).
        
        Args:
            user_id: User whose report is rejected
            admin_id: Admin rejecting the report
            reason: Optional reason for rejection
            
        Returns:
            True if successful
        """
        try:
            rejection_data = {
                "user_id": user_id,
                "admin_id": admin_id,
                "rejected_at": int(time.time()),
                "reason": reason,
                "action": "rejected"
            }
            
            # Store rejection
            key = f"report:rejections:{user_id}"
            await self.redis.lpush(key, json.dumps(rejection_data))
            await self.redis.ltrim(key, 0, 49)  # Keep last 50
            
            # Optionally reduce report count if rejecting false reports
            count_key = f"stats:{user_id}:report_count"
            current_count = await self.redis.get(count_key)
            if current_count:
                new_count = max(0, int(current_count) - 1)
                await self.redis.set(count_key, new_count)
            
            logger.info("report_rejected", user_id=user_id, admin_id=admin_id)
            return True
            
        except Exception as e:
            logger.error("reject_report_error", user_id=user_id, error=str(e))
            return False
    
    # ============================================
    # USER FREEZING (TOXIC USER MANAGEMENT)
    # ============================================
    
    async def freeze_user(self, user_id: int, admin_id: int, duration: Optional[int] = None, reason: str = None, duration_str: str = None) -> bool:
        """
        Freeze a toxic user (prevents matching but allows limited access).
        
        Args:
            user_id: User to freeze
            admin_id: Admin freezing the user
            duration: Freeze duration in seconds (None for permanent)
            reason: Reason for freeze
            duration_str: Duration string for display (e.g., "1h", "24h", "permanent")
            
        Returns:
            True if successful
        """
        try:
            freeze_data = {
                "user_id": user_id,
                "frozen_by": admin_id,
                "frozen_at": int(time.time()),
                "expires_at": int(time.time()) + duration if duration else None,
                "duration": duration_str or ("Permanent" if duration is None else f"{duration}s"),
                "reason": reason or "Toxic behavior",
                "is_permanent": duration is None
            }
            
            # Store freeze data
            freeze_key = f"user:frozen:{user_id}"
            await self.redis.set(
                freeze_key,
                json.dumps(freeze_data),
                ex=duration if duration else None
            )
            
            # Add to frozen users set
            await self.redis.sadd("bot:frozen_users", str(user_id))
            
            logger.info("user_frozen", user_id=user_id, admin_id=admin_id, duration=duration)
            return True
            
        except Exception as e:
            logger.error("freeze_user_error", user_id=user_id, error=str(e))
            return False
    
    async def unfreeze_user(self, user_id: int, admin_id: int) -> bool:
        """
        Unfreeze a user.
        
        Args:
            user_id: User to unfreeze
            admin_id: Admin unfreezing the user
            
        Returns:
            True if successful
        """
        try:
            # Remove freeze data
            freeze_key = f"user:frozen:{user_id}"
            await self.redis.delete(freeze_key)
            
            # Remove from frozen set
            await self.redis.srem("bot:frozen_users", str(user_id))
            
            logger.info("user_unfrozen", user_id=user_id, admin_id=admin_id)
            return True
            
        except Exception as e:
            logger.error("unfreeze_user_error", user_id=user_id, error=str(e))
            return False
    
    async def is_user_frozen(self, user_id: int) -> tuple[bool, Optional[Dict]]:
        """
        Check if user is frozen.
        
        Args:
            user_id: User to check
            
        Returns:
            (is_frozen, freeze_data)
        """
        try:
            freeze_key = f"user:frozen:{user_id}"
            freeze_bytes = await self.redis.get(freeze_key)
            
            if not freeze_bytes:
                return False, None
            
            freeze_data = json.loads(freeze_bytes.decode('utf-8'))
            
            # Check if temporary freeze expired
            if freeze_data.get("expires_at"):
                if time.time() > freeze_data["expires_at"]:
                    await self.unfreeze_user(user_id, 0)  # System unfreeze
                    return False, None
            
            return True, freeze_data
            
        except Exception as e:
            logger.error("is_user_frozen_error", user_id=user_id, error=str(e))
            return False, None
    
    async def get_frozen_users(self) -> List[int]:
        """Get list of all frozen users."""
        try:
            frozen_set = await self.redis.smembers("bot:frozen_users")
            return [int(uid.decode('utf-8') if isinstance(uid, bytes) else uid) for uid in frozen_set]
        except Exception as e:
            logger.error("get_frozen_users_error", error=str(e))
            return []
    
    # ============================================
    # MEDIA BLOCKING
    # ============================================
    
    async def block_media_type(self, media_type: str, duration: Optional[int] = None, reason: str = None) -> bool:
        """
        Block a specific media type globally or temporarily.
        
        Args:
            media_type: Type of media to block (photo, video, voice, etc.)
            duration: Block duration in seconds (None for permanent)
            reason: Reason for blocking
            
        Returns:
            True if successful
        """
        try:
            if media_type not in self.MEDIA_TYPES:
                logger.warning("invalid_media_type", media_type=media_type)
                return False
            
            block_data = {
                "media_type": media_type,
                "blocked_at": int(time.time()),
                "expires_at": int(time.time()) + duration if duration else None,
                "reason": reason or "Content moderation",
                "is_permanent": duration is None
            }
            
            # Store block data
            block_key = f"media:blocked:{media_type}"
            await self.redis.set(
                block_key,
                json.dumps(block_data),
                ex=duration if duration else None
            )
            
            # Add to blocked media set
            await self.redis.sadd("bot:blocked_media", media_type)
            
            logger.info("media_type_blocked", media_type=media_type, duration=duration)
            return True
            
        except Exception as e:
            logger.error("block_media_type_error", media_type=media_type, error=str(e))
            return False
    
    async def unblock_media_type(self, media_type: str) -> bool:
        """
        Unblock a media type.
        
        Args:
            media_type: Type of media to unblock
            
        Returns:
            True if successful
        """
        try:
            block_key = f"media:blocked:{media_type}"
            await self.redis.delete(block_key)
            await self.redis.srem("bot:blocked_media", media_type)
            
            logger.info("media_type_unblocked", media_type=media_type)
            return True
            
        except Exception as e:
            logger.error("unblock_media_type_error", media_type=media_type, error=str(e))
            return False
    
    async def is_media_blocked(self, media_type: str) -> bool:
        """Check if a media type is currently blocked."""
        try:
            block_key = f"media:blocked:{media_type}"
            return await self.redis.exists(block_key)
        except Exception as e:
            logger.error("is_media_blocked_error", media_type=media_type, error=str(e))
            return False
    
    async def get_blocked_media_types(self) -> List[Dict[str, Any]]:
        """Get all currently blocked media types with details."""
        try:
            blocked_set = await self.redis.smembers("bot:blocked_media")
            blocked_media = []
            
            for media_bytes in blocked_set:
                try:
                    media_type = media_bytes.decode('utf-8') if isinstance(media_bytes, bytes) else media_bytes
                    block_key = f"media:blocked:{media_type}"
                    block_bytes = await self.redis.get(block_key)
                    
                    if block_bytes:
                        block_data = json.loads(block_bytes.decode('utf-8'))
                        blocked_media.append(block_data)
                except:
                    continue
            
            return blocked_media
            
        except Exception as e:
            logger.error("get_blocked_media_types_error", error=str(e))
            return []
    
    # ============================================
    # BAD WORD FILTER
    # ============================================
    
    async def add_bad_word(self, word: str, admin_id: int) -> bool:
        """
        Add word to bad word filter.
        
        Args:
            word: Word to filter (case-insensitive)
            admin_id: Admin adding the word
            
        Returns:
            True if successful
        """
        try:
            word = word.lower().strip()
            
            # Add to bad words set
            await self.redis.sadd("bot:bad_words", word)
            
            # Log the addition
            log_data = {
                "word": word,
                "added_by": admin_id,
                "added_at": int(time.time())
            }
            await self.redis.lpush("bot:bad_words_log", json.dumps(log_data))
            await self.redis.ltrim("bot:bad_words_log", 0, 499)  # Keep last 500
            
            logger.info("bad_word_added", word=word, admin_id=admin_id)
            return True
            
        except Exception as e:
            logger.error("add_bad_word_error", word=word, error=str(e))
            return False
    
    async def remove_bad_word(self, word: str, admin_id: int) -> bool:
        """
        Remove word from bad word filter.
        
        Args:
            word: Word to remove
            admin_id: Admin removing the word
            
        Returns:
            True if successful
        """
        try:
            word = word.lower().strip()
            result = await self.redis.srem("bot:bad_words", word)
            
            if result:
                logger.info("bad_word_removed", word=word, admin_id=admin_id)
                return True
            return False
            
        except Exception as e:
            logger.error("remove_bad_word_error", word=word, error=str(e))
            return False
    
    async def get_bad_words(self) -> List[str]:
        """Get all bad words in filter."""
        try:
            words_set = await self.redis.smembers("bot:bad_words")
            return sorted([w.decode('utf-8') if isinstance(w, bytes) else w for w in words_set])
        except Exception as e:
            logger.error("get_bad_words_error", error=str(e))
            return []
    
    async def contains_bad_word(self, text: str) -> bool:
        """Check if text contains any bad words."""
        try:
            text_lower = text.lower()
            bad_words = await self.get_bad_words()
            
            for word in bad_words:
                if word in text_lower:
                    return True
            return False
            
        except Exception as e:
            logger.error("contains_bad_word_error", error=str(e))
            return False
    
    # ============================================
    # MODERATION LOGS
    # ============================================
    
    async def log_moderation_action(
        self,
        admin_id: int,
        action: str,
        target_user_id: Optional[int] = None,
        details: str = None
    ) -> None:
        """
        Log a moderation action for audit trail.
        
        Args:
            admin_id: Admin performing action
            action: Type of action (ban, report_approve, media_block, etc.)
            target_user_id: User affected (if applicable)
            details: Additional details
        """
        try:
            log_entry = {
                "admin_id": admin_id,
                "action": action,
                "target_user_id": target_user_id,
                "details": details,
                "timestamp": int(time.time())
            }
            
            # Add to moderation log
            await self.redis.lpush("bot:moderation_log", json.dumps(log_entry))
            await self.redis.ltrim("bot:moderation_log", 0, 999)  # Keep last 1000
            
        except Exception as e:
            logger.error("log_moderation_action_error", error=str(e))
    
    async def get_moderation_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent moderation logs (newest first).
        
        Args:
            limit: Maximum number of logs to retrieve
            
        Returns:
            List of log entries (newest first, thanks to lpush storing newest at index 0)
        """
        try:
            # lrange(0, limit-1) gets newest logs first because lpush adds to the left
            logs_bytes = await self.redis.lrange("bot:moderation_log", 0, limit - 1)
            logs = []
            
            for log_bytes in logs_bytes:
                try:
                    if isinstance(log_bytes, bytes):
                        log_bytes = log_bytes.decode('utf-8')
                    log_data = json.loads(log_bytes)
                    logs.append(log_data)
                except:
                    continue
            
            # No reverse needed - lpush keeps newest at index 0
            return logs
            
        except Exception as e:
            logger.error("get_moderation_logs_error", error=str(e))
            return []
    
    # ============================================
    # REPORT STATISTICS
    # ============================================
    
    async def get_report_stats(self) -> Dict[str, Any]:
        """Get overall report statistics."""
        try:
            # Get all users who have been reported
            report_keys = await self.redis.keys("stats:*:reports")
            total_reported_users = len(report_keys)
            
            # Calculate total reports by summing individual report counts
            total_reports = 0
            for key_bytes in report_keys:
                try:
                    key = key_bytes.decode('utf-8') if isinstance(key_bytes, bytes) else key_bytes
                    user_id = key.split(':')[1]
                    
                    # Get report count for this user
                    count_key = f"stats:{user_id}:report_count"
                    count_bytes = await self.redis.get(count_key)
                    if count_bytes:
                        total_reports += int(count_bytes)
                except Exception as e:
                    logger.debug("count_reports_error", key=key, error=str(e))
                    continue
            
            # Calculate pending reports (not approved or rejected individually)
            approval_keys = await self.redis.keys("report:individual_approval:*")
            rejection_keys = await self.redis.keys("report:individual_rejection:*")
            processed_reports = len(approval_keys) + len(rejection_keys)
            pending_reports = max(0, total_reports - processed_reports)
            
            # Get frozen users count
            frozen_users = await self.get_frozen_users()
            
            # Get blocked media count
            blocked_media = await self.get_blocked_media_types()
            
            # Get bad words count
            bad_words = await self.get_bad_words()
            
            return {
                "total_reports": total_reports,
                "reported_users": total_reported_users,
                "pending_reports": pending_reports,
                "frozen_users_count": len(frozen_users),
                "blocked_media_count": len(blocked_media),
                "bad_words_count": len(bad_words)
            }
            
        except Exception as e:
            logger.error("get_report_stats_error", error=str(e))
            return {
                "total_reports": 0,
                "reported_users": 0,
                "pending_reports": 0,
                "frozen_users_count": 0,
                "blocked_media_count": 0,
                "bad_words_count": 0
            }
