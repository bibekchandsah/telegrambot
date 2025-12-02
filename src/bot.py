"""Main bot application."""
import signal
import sys
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)
from src.config import Config
from src.db.redis_client import redis_client
from src.services.matching import MatchingEngine
from src.services.profile import ProfileManager
from src.services.preferences import PreferenceManager
from src.services.feedback import FeedbackManager
from src.services.activity import ActivityManager
from src.services.media_preferences import MediaPreferenceManager
from src.services.admin import AdminManager
from src.services.reports import ReportManager
from src.handlers.commands import (
    start_command,
    help_command,
    chat_command,
    stop_command,
    next_command,
    report_command,
    report_callback,
    profile_command,
    editprofile_command,
    nickname_step,
    gender_callback,
    country_callback,
    country_text,
    cancel_profile,
    preferences_command,
    pref_gender_callback,
    pref_country_text,
    cancel_preferences,
    feedback_callback,
    rating_command,
    mediasettings_command,
    media_callback,
    admin_command,
    broadcast_command,
    broadcastactive_command,
    broadcast_message_step,
    broadcast_callback,
    stats_command,
    cancel_broadcast,
    ban_command,
    ban_user_id_step,
    ban_reason_callback,
    ban_duration_callback,
    unban_command,
    unban_user_id_step,
    warn_command,
    warn_user_id_step,
    warn_reason_step,
    checkban_command,
    bannedlist_command,
    warninglist_command,
    cancel_ban_operation,
    NICKNAME,
    GENDER,
    COUNTRY,
    PREF_GENDER,
    PREF_COUNTRY,
    MEDIA_SETTINGS,
    BROADCAST_MESSAGE,
    BAN_USER_ID,
    BAN_REASON,
    BAN_DURATION,
    UNBAN_USER_ID,
    WARNING_USER_ID,
    WARNING_REASON,
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
        
        # Initialize managers
        profile_manager = ProfileManager(redis_client)
        preference_manager = PreferenceManager(redis_client)
        feedback_manager = FeedbackManager(redis_client)
        activity_manager = ActivityManager(redis_client)
        media_manager = MediaPreferenceManager(redis_client)
        admin_manager = AdminManager(redis_client, Config.ADMIN_IDS)
        report_manager = ReportManager(redis_client)
        matching_engine = MatchingEngine(
            redis_client,
            profile_manager=profile_manager,
            preference_manager=preference_manager,
            feedback_manager=feedback_manager,
            admin_manager=admin_manager,
        )
        
        # Store instances in bot_data for access in handlers
        application.bot_data["redis"] = redis_client
        application.bot_data["matching"] = matching_engine
        application.bot_data["profile_manager"] = profile_manager
        application.bot_data["preference_manager"] = preference_manager
        application.bot_data["feedback_manager"] = feedback_manager
        application.bot_data["activity_manager"] = activity_manager
        application.bot_data["media_manager"] = media_manager
        application.bot_data["admin_manager"] = admin_manager
        application.bot_data["report_manager"] = report_manager
        
        logger.info("bot_initialized", bot_username=application.bot.username)
        
        # Log bot info
        bot_info = await application.bot.get_me()
        logger.info(
            "bot_info",
            id=bot_info.id,
            username=bot_info.username,
            name=bot_info.first_name,
        )
        
        # Start notification sender background job (if job_queue available)
        if application.job_queue:
            application.job_queue.run_repeating(
                send_pending_notifications,
                interval=5,  # Check every 5 seconds
                first=1,
                name="notification_sender"
            )
        else:
            logger.warning("job_queue_not_available", message="Install python-telegram-bot[job-queue] for background jobs")
        
    except Exception as e:
        logger.error("initialization_failed", error=str(e))
        raise


async def send_pending_notifications(context: ContextTypes.DEFAULT_TYPE):
    """Send pending notifications from Redis queue."""
    try:
        redis_client = context.bot_data.get("redis")
        if not redis_client:
            return
        
        # Get pending notifications
        import json
        notifications = await redis_client.lrange("bot:pending_notifications", 0, 9)  # Process 10 at a time
        
        for notification_bytes in notifications:
            try:
                if isinstance(notification_bytes, bytes):
                    notification_bytes = notification_bytes.decode('utf-8')
                notification = json.loads(notification_bytes)
                
                user_id = notification.get("user_id")
                message = notification.get("message")
                
                if user_id and message:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    logger.info("notification_sent", user_id=user_id)
                
                # Remove from queue
                await redis_client.lrem("bot:pending_notifications", 1, notification_bytes if isinstance(notification_bytes, bytes) else notification_bytes.encode())
                
            except Exception as e:
                logger.error("send_notification_error", error=str(e))
                # Remove failed notification to prevent infinite retries
                await redis_client.lrem("bot:pending_notifications", 1, notification_bytes if isinstance(notification_bytes, bytes) else notification_bytes.encode())
                
    except Exception as e:
        logger.error("pending_notifications_error", error=str(e))


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
        application.add_handler(CommandHandler("profile", profile_command))
        application.add_handler(CommandHandler("rating", rating_command))
        
        # Register admin commands
        application.add_handler(CommandHandler("admin", admin_command))
        application.add_handler(CommandHandler("stats", stats_command))
        application.add_handler(CommandHandler("checkban", checkban_command))
        application.add_handler(CommandHandler("bannedlist", bannedlist_command))
        application.add_handler(CommandHandler("warninglist", warninglist_command))
        
        # Register feedback callback handler
        application.add_handler(
            CallbackQueryHandler(
                feedback_callback,
                pattern="^feedback_(positive|negative|skip)$",
            )
        )
        
        # Register report callback handler
        application.add_handler(
            CallbackQueryHandler(
                report_callback,
                pattern="^report_(nudity|harassment|spam|scam|fake|other|cancel)$",
            )
        )
        
        # Register media settings conversation handler
        media_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("mediasettings", mediasettings_command)],
            states={
                MEDIA_SETTINGS: [
                    CallbackQueryHandler(
                        media_callback,
                        pattern="^media_(done|text_only_on|text_only_off|toggle_.+)$",
                    )
                ],
            },
            fallbacks=[],
        )
        application.add_handler(media_conv_handler)
        
        # Register admin broadcast conversation handler
        broadcast_conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("broadcast", broadcast_command),
                CommandHandler("broadcastactive", broadcastactive_command),
            ],
            states={
                BROADCAST_MESSAGE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message_step),
                    CallbackQueryHandler(
                        broadcast_callback,
                        pattern="^broadcast_(confirm|cancel)$",
                    ),
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel_broadcast)],
        )
        application.add_handler(broadcast_conv_handler)
        
        # Register ban conversation handler
        ban_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("ban", ban_command)],
            states={
                BAN_USER_ID: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, ban_user_id_step),
                ],
                BAN_REASON: [
                    CallbackQueryHandler(ban_reason_callback, pattern="^ban_(reason_|cancel)"),
                ],
                BAN_DURATION: [
                    CallbackQueryHandler(ban_duration_callback, pattern="^ban_(duration_|cancel)"),
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel_ban_operation)],
        )
        application.add_handler(ban_conv_handler)
        
        # Register unban conversation handler
        unban_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("unban", unban_command)],
            states={
                UNBAN_USER_ID: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, unban_user_id_step),
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel_ban_operation)],
        )
        application.add_handler(unban_conv_handler)
        
        # Register warning conversation handler
        warn_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("warn", warn_command)],
            states={
                WARNING_USER_ID: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, warn_user_id_step),
                ],
                WARNING_REASON: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, warn_reason_step),
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel_ban_operation)],
        )
        application.add_handler(warn_conv_handler)
        
        # Register profile editing conversation handler
        profile_conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("editprofile", editprofile_command),
                CallbackQueryHandler(editprofile_command, pattern="^edit_profile$"),
            ],
            states={
                NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, nickname_step)],
                GENDER: [CallbackQueryHandler(gender_callback, pattern="^gender_")],
                COUNTRY: [
                    CallbackQueryHandler(country_callback, pattern="^country_"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, country_text),
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel_profile)],
        )
        application.add_handler(profile_conv_handler)
        
        # Register preferences conversation handler
        preferences_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("preferences", preferences_command)],
            states={
                PREF_GENDER: [
                    CallbackQueryHandler(
                        pref_gender_callback,
                        pattern="^pref_(gender|country|reset|cancel|back|gender_male|gender_female|gender_any)$",
                    )
                ],
                PREF_COUNTRY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, pref_country_text),
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel_preferences)],
        )
        application.add_handler(preferences_conv_handler)
        
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
