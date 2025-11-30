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
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set value in Redis with optional expiry."""
        try:
            return await self.client.set(key, value, ex=ex)
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
    
    async def keys(self, pattern: str) -> list:
        """Get keys matching pattern."""
        try:
            return await self.client.keys(pattern)
        except RedisError as e:
            logger.error("redis_keys_error", pattern=pattern, error=str(e))
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
    
    async def expire(self, key: str, time: int) -> bool:
        """Set key expiration."""
        try:
            return await self.client.expire(key, time)
        except RedisError as e:
            logger.error("redis_expire_error", key=key, error=str(e))
            raise


# Singleton instance
redis_client = RedisClient()
