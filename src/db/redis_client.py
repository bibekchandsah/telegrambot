"""Redis client with connection pooling."""
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError, ConnectionError
from typing import Optional
from src.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RedisClient:
    """Redis client wrapper with connection pooling."""
    
    def __init__(self):
        self.pool: Optional[ConnectionPool] = None
        self.client: Optional[redis.Redis] = None
        
    async def connect(self):
        """Initialize Redis connection pool."""
        try:
            self.pool = ConnectionPool.from_url(
                Config.REDIS_URL,
                max_connections=10,
                decode_responses=False,  # We'll decode manually when needed
            )
            self.client = redis.Redis(connection_pool=self.pool)
            
            # Test connection
            await self.client.ping()
            logger.info("redis_connected", url=Config.REDIS_URL)
            
        except ConnectionError as e:
            logger.error("redis_connection_failed", error=str(e))
            raise
    
    async def close(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()
        if self.pool:
            await self.pool.disconnect()
        logger.info("redis_disconnected")
    
    async def get(self, key: str) -> Optional[bytes]:
        """Get value from Redis."""
        try:
            return await self.client.get(key)
        except RedisError as e:
            logger.error("redis_get_error", key=key, error=str(e))
            raise
    
    async def set(self, key: str, value: str, ex: Optional[int] = None, nx: bool = False) -> bool:
        """Set value in Redis with optional expiry and nx flag."""
        try:
            return await self.client.set(key, value, ex=ex, nx=nx)
        except RedisError as e:
            logger.error("redis_set_error", key=key, error=str(e))
            raise
    
    async def delete(self, *keys: str) -> int:
        """Delete keys from Redis."""
        try:
            return await self.client.delete(*keys)
        except RedisError as e:
            logger.error("redis_delete_error", keys=keys, error=str(e))
            raise
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        try:
            return await self.client.exists(key) > 0
        except RedisError as e:
            logger.error("redis_exists_error", key=key, error=str(e))
            raise
    
    async def lpush(self, key: str, *values: str) -> int:
        """Push values to the left of a list."""
        try:
            return await self.client.lpush(key, *values)
        except RedisError as e:
            logger.error("redis_lpush_error", key=key, error=str(e))
            raise
    
    async def rpop(self, key: str) -> Optional[bytes]:
        """Pop value from the right of a list."""
        try:
            return await self.client.rpop(key)
        except RedisError as e:
            logger.error("redis_rpop_error", key=key, error=str(e))
            raise
    
    async def lrem(self, key: str, count: int, value: str) -> int:
        """Remove elements from list."""
        try:
            return await self.client.lrem(key, count, value)
        except RedisError as e:
            logger.error("redis_lrem_error", key=key, error=str(e))
            raise
    
    async def llen(self, key: str) -> int:
        """Get list length."""
        try:
            return await self.client.llen(key)
        except RedisError as e:
            logger.error("redis_llen_error", key=key, error=str(e))
            raise
    
    async def lrange(self, key: str, start: int, end: int) -> list:
        """Get range of elements from list."""
        try:
            return await self.client.lrange(key, start, end)
        except RedisError as e:
            logger.error("redis_lrange_error", key=key, error=str(e))
            raise
    
    async def ltrim(self, key: str, start: int, end: int) -> bool:
        """Trim list to specified range."""
        try:
            return await self.client.ltrim(key, start, end)
        except RedisError as e:
            logger.error("redis_ltrim_error", key=key, error=str(e))
            raise
    
    async def keys(self, pattern: str) -> list:
        """Get keys matching pattern."""
        try:
            return await self.client.keys(pattern)
        except RedisError as e:
            logger.error("redis_keys_error", pattern=pattern, error=str(e))
            raise
    
    async def scan(self, cursor: int = 0, match: str = None, count: int = 100):
        """
        Scan keys using cursor-based iteration.
        
        Args:
            cursor: Cursor position (0 to start)
            match: Pattern to match keys
            count: Number of keys to return per iteration
            
        Returns:
            Tuple of (next_cursor, list_of_keys)
        """
        try:
            return await self.client.scan(cursor=cursor, match=match, count=count)
        except RedisError as e:
            logger.error("redis_scan_error", error=str(e))
            raise
    
    async def eval(self, script: str, numkeys: int, *keys_and_args) -> any:
        """Evaluate Lua script."""
        try:
            return await self.client.eval(script, numkeys, *keys_and_args)
        except RedisError as e:
            logger.error("redis_eval_error", error=str(e))
            raise
    
    def pipeline(self, transaction: bool = True):
        """Create a pipeline for batch operations."""
        return self.client.pipeline(transaction=transaction)
    
    async def incr(self, key: str) -> int:
        """Increment value."""
        try:
            return await self.client.incr(key)
        except RedisError as e:
            logger.error("redis_incr_error", key=key, error=str(e))
            raise
    
    async def incrby(self, key: str, amount: int) -> int:
        """Increment value by amount."""
        try:
            return await self.client.incrby(key, amount)
        except RedisError as e:
            logger.error("redis_incrby_error", key=key, error=str(e))
            raise
    
    async def expire(self, key: str, time: int) -> bool:
        """Set key expiration."""
        try:
            return await self.client.expire(key, time)
        except RedisError as e:
            logger.error("redis_expire_error", key=key, error=str(e))
            raise
    
    async def sadd(self, key: str, *members: str) -> int:
        """Add members to a set."""
        try:
            return await self.client.sadd(key, *members)
        except RedisError as e:
            logger.error("redis_sadd_error", key=key, error=str(e))
            raise
    
    async def smembers(self, key: str) -> set:
        """Get all members of a set."""
        try:
            return await self.client.smembers(key)
        except RedisError as e:
            logger.error("redis_smembers_error", key=key, error=str(e))
            raise
    
    async def srem(self, key: str, *members: str) -> int:
        """Remove members from a set."""
        try:
            return await self.client.srem(key, *members)
        except RedisError as e:
            logger.error("redis_srem_error", key=key, error=str(e))
            raise
    
    async def zadd(self, key: str, mapping: dict, nx: bool = False, gt: bool = False) -> int:
        """Add members to a sorted set with scores."""
        try:
            return await self.client.zadd(key, mapping, nx=nx, gt=gt)
        except RedisError as e:
            logger.error("redis_zadd_error", key=key, error=str(e))
            raise
    
    async def zrevrange(self, key: str, start: int, end: int, withscores: bool = False) -> list:
        """Get members from sorted set in reverse order (highest to lowest score)."""
        try:
            return await self.client.zrevrange(key, start, end, withscores=withscores)
        except RedisError as e:
            logger.error("redis_zrevrange_error", key=key, error=str(e))
            raise
    
    async def zcard(self, key: str) -> int:
        """Get the number of members in a sorted set."""
        try:
            return await self.client.zcard(key)
        except RedisError as e:
            logger.error("redis_zcard_error", key=key, error=str(e))
            raise


# Singleton instance
redis_client = RedisClient()
