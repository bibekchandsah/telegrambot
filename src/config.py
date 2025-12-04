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
    
    # Dashboard settings
    DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "5000"))
    DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "0.0.0.0")
    
    # TOTP Authentication settings
    TOTP_SECRET = os.getenv("TOTP_SECRET")  # If not set, will be generated and shown as QR
    TOTP_MAX_ATTEMPTS = int(os.getenv("TOTP_MAX_ATTEMPTS", "5"))
    SESSION_SECRET = os.getenv("SESSION_SECRET", os.urandom(24).hex())
    
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    # Production settings
    IS_PRODUCTION = ENVIRONMENT == "production"
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN environment variable is required")
        # REDIS_URL has a default, but warn if using localhost in production
        if cls.IS_PRODUCTION and "localhost" in cls.REDIS_URL:
            import sys
            print("WARNING: Using localhost Redis in production. Set REDIS_URL environment variable.", file=sys.stderr)
            print(f"Current REDIS_URL: {cls.REDIS_URL}", file=sys.stderr)
    
    @classmethod
    def is_production(cls):
        """Check if running in production mode."""
        return cls.IS_PRODUCTION
    
    @classmethod
    def get_log_config(cls):
        """Get logging configuration based on environment."""
        if cls.IS_PRODUCTION:
            return {
                "level": "INFO",
                "format": "json",  # Structured logging for production
                "output": "stdout"
            }
        else:
            return {
                "level": "DEBUG",
                "format": "text",  # Human-readable for development
                "output": "console"
            }


# Validate on import
Config.validate()
