"""Utility decorators for handlers."""
import time
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from src.utils.logger import get_logger

logger = get_logger(__name__)


def rate_limit(max_calls: int, period: int = 60):
    """
    Rate limiting decorator.
    
    Args:
        max_calls: Maximum number of calls allowed
        period: Time period in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            key = f"ratelimit:{func.__name__}:{user_id}"
            
            # Get current count from Redis
            redis = context.bot_data.get("redis")
            if not redis:
                return await func(update, context)
            
            try:
                current = await redis.get(key)
                current = int(current) if current else 0
                
                if current >= max_calls:
                    await update.message.reply_text(
                        f"⚠️ You're doing that too often. Please wait a moment."
                    )
                    logger.warning(
                        "rate_limit_exceeded",
                        user_id=user_id,
                        function=func.__name__,
                        current=current,
                    )
                    return
                
                # Increment counter
                pipe = redis.pipeline()
                pipe.incr(key)
                pipe.expire(key, period)
                await pipe.execute()
                
            except Exception as e:
                logger.error("rate_limit_error", error=str(e))
                # Continue without rate limiting if Redis fails
            
            return await func(update, context)
        
        return wrapper
    return decorator


def require_state(*allowed_states):
    """
    Decorator to check user state before executing handler.
    
    Args:
        allowed_states: States that are allowed to execute this handler
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            redis = context.bot_data.get("redis")
            
            if not redis:
                return await func(update, context)
            
            try:
                current_state = await redis.get(f"state:{user_id}")
                current_state = current_state.decode() if current_state else "IDLE"
                
                if current_state not in allowed_states:
                    await update.message.reply_text(
                        f"⚠️ This command is not available in your current state."
                    )
                    return
                
            except Exception as e:
                logger.error("state_check_error", error=str(e))
            
            return await func(update, context)
        
        return wrapper
    return decorator
