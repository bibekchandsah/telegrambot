"""Configuration management for the bot."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Bot configuration."""
    
    # Bot settings
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    # Redis settings
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Application settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "500"))
    MESSAGE_RATE_LIMIT = int(os.getenv("MESSAGE_RATE_LIMIT", "30"))
    CHAT_TIMEOUT = int(os.getenv("CHAT_TIMEOUT", "600"))
    NEXT_COMMAND_LIMIT = int(os.getenv("NEXT_COMMAND_LIMIT", "10"))
    
    # Admin settings
    ADMIN_IDS = [
        int(admin_id.strip()) 
        for admin_id in os.getenv("ADMIN_IDS", "").split(",") 
        if admin_id.strip()
    ]
    
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN environment variable is required")
        if not cls.REDIS_URL:
            raise ValueError("REDIS_URL environment variable is required")


# Validate on import
Config.validate()
