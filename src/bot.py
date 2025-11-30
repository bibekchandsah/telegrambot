"""Main bot application."""
import signal
import sys
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)
from src.config import Config
from src.db.redis_client import redis_client
from src.services.matching import MatchingEngine
from src.handlers.commands import (
    start_command,
    help_command,
    chat_command,
    stop_command,
    next_command,
    report_command,
)
from src.handlers.messages import (
    handle_message,
    handle_error,
)
from src.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


async def post_init(application: Application):
    """Initialize resources after application startup."""
    try:
        # Connect to Redis
        await redis_client.connect()
        
        # Store instances in bot_data for access in handlers
        application.bot_data["redis"] = redis_client
        application.bot_data["matching"] = MatchingEngine(redis_client)
        
        logger.info("bot_initialized", bot_username=application.bot.username)
        
        # Log bot info
        bot_info = await application.bot.get_me()
        logger.info(
            "bot_info",
            id=bot_info.id,
            username=bot_info.username,
            name=bot_info.first_name,
        )
        
    except Exception as e:
        logger.error("initialization_failed", error=str(e))
        raise


async def post_shutdown(application: Application):
    """Cleanup resources on shutdown."""
    try:
        logger.info("shutting_down")
        
        # Notify active users
        matching: MatchingEngine = application.bot_data.get("matching")
        if matching:
            try:
                # Get all active pairs
                active_pairs = await redis_client.keys("pair:*")
                notified_users = set()
                
                for key in active_pairs:
                    user_id = int(key.decode().split(":")[1])
                    if user_id not in notified_users:
                        try:
                            await application.bot.send_message(
                                user_id,
                                "⚠️ Bot is restarting. Your chat has ended.\n"
                                "Please use /chat to reconnect shortly."
                            )
                            notified_users.add(user_id)
                        except Exception as e:
                            logger.warning(
                                "shutdown_notification_failed",
                                user_id=user_id,
                                error=str(e),
                            )
                
                logger.info(
                    "shutdown_notifications_sent",
                    count=len(notified_users),
                )
                
            except Exception as e:
                logger.error("shutdown_notification_error", error=str(e))
        
        # Close Redis connection
        await redis_client.close()
        
        logger.info("shutdown_complete")
        
    except Exception as e:
        logger.error("shutdown_error", error=str(e))


def main():
    """Run the bot."""
    try:
        # Create application
        application = (
            Application.builder()
            .token(Config.BOT_TOKEN)
            .post_init(post_init)
            .post_shutdown(post_shutdown)
            .build()
        )
        
        # Register command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("chat", chat_command))
        application.add_handler(CommandHandler("stop", stop_command))
        application.add_handler(CommandHandler("next", next_command))
        application.add_handler(CommandHandler("report", report_command))
        
        # Register message handler for routing
        # This handles all non-command messages
        application.add_handler(
            MessageHandler(
                filters.ALL & ~filters.COMMAND,
                handle_message,
            )
        )
        
        # Register error handler
        application.add_error_handler(handle_error)
        
        logger.info("starting_bot")
        
        # Handle graceful shutdown
        def signal_handler(sig, frame):
            logger.info("shutdown_signal_received", signal=sig)
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start the bot
        application.run_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )
        
    except KeyboardInterrupt:
        logger.info("keyboard_interrupt")
    except Exception as e:
        logger.error("bot_startup_failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
