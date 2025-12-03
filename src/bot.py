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
    ContextTypes,
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
    broadcastusers_command,
    broadcastusers_ids_step,
    broadcastfilter_command,
    filter_gender_callback,
    filter_country_step,
    filter_message_type_callback,
    filter_message_step,
    filtered_broadcast_callback,
    button_config_callback,
    broadcast_button_callback,
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
    blockmedia_command,
    unblockmedia_command,
    blockedmedia_command,
    addbadword_command,
    removebadword_command,
    badwords_command,
    maintenance_command,
    registrations_command,
    forcelogout_command,
    resetqueue_command,
    enablegender_command,
    disablegender_command,
    enableregional_command,
    disableregional_command,
    forcematch_command,
    matchstatus_command,
    menu_button_callback,
    NICKNAME,
    GENDER,
    COUNTRY,
    PREF_GENDER,
    PREF_COUNTRY,
    MEDIA_SETTINGS,
    BROADCAST_MESSAGE,
    BROADCAST_FILTER_GENDER,
    BROADCAST_FILTER_COUNTRY,
    BROADCAST_FILTER_MESSAGE,
    BROADCAST_FILTER_MEDIA,
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
        
        # Set bot commands menu
        from telegram import BotCommand
        commands = [
            BotCommand("start", "Start a new chat session"),
            BotCommand("chat", "Find a random partner"),
            BotCommand("stop", "End current chat"),
            BotCommand("next", "Skip to next partner"),
            BotCommand("profile", "View/edit your profile"),
            BotCommand("preferences", "Set matching preferences"),
            BotCommand("mediasettings", "Configure media types"),
            BotCommand("rating", "Rate your last chat"),
            BotCommand("report", "Report abuse"),
            BotCommand("cancel", "Cancel current operation"),
            BotCommand("help", "Show help information"),
        ]
        await application.bot.set_my_commands(commands)
        logger.info("bot_commands_set", count=len(commands))
        
        # Start notification sender background job (if job_queue available)
        if application.job_queue:
            application.job_queue.run_repeating(
                send_pending_notifications,
                interval=5,  # Check every 5 seconds
                first=1,
                name="notification_sender"
            )
            # Start inactivity monitor
            application.job_queue.run_repeating(
                check_inactivity,
                interval=30,  # Check every 30 seconds
                first=10,
                name="inactivity_monitor"
            )
        else:
            logger.warning("job_queue_not_available", message="Install python-telegram-bot[job-queue] for background jobs")
        
    except Exception as e:
        logger.error("initialization_failed", error=str(e))
        raise


async def check_inactivity(context: ContextTypes.DEFAULT_TYPE):
    """Check for inactive chats and auto-disconnect."""
    try:
        import time
        redis_client = context.bot_data.get("redis")
        matching = context.bot_data.get("matching")
        
        if not redis_client or not matching:
            return
        
        # Get inactivity duration from settings (default 300 seconds = 5 minutes)
        inactivity_duration_bytes = await redis_client.get("bot:settings:inactivity_duration")
        inactivity_duration = 300  # default
        if inactivity_duration_bytes:
            try:
                inactivity_duration = int(inactivity_duration_bytes.decode('utf-8') if isinstance(inactivity_duration_bytes, bytes) else inactivity_duration_bytes)
            except:
                pass
        
        current_time = int(time.time())
        
        # Get all active pairs
        pair_keys = await redis_client.keys("pair:*")
        
        for pair_key in pair_keys:
            try:
                if isinstance(pair_key, bytes):
                    pair_key = pair_key.decode('utf-8')
                
                user_id = int(pair_key.split(':')[1])
                partner_id_bytes = await redis_client.get(pair_key)
                
                if not partner_id_bytes:
                    continue
                
                partner_id = int(partner_id_bytes.decode('utf-8') if isinstance(partner_id_bytes, bytes) else partner_id_bytes)
                
                # Get last activity times
                user_activity_bytes = await redis_client.get(f"chat:activity:{user_id}")
                partner_activity_bytes = await redis_client.get(f"chat:activity:{partner_id}")
                
                user_last_activity = None
                partner_last_activity = None
                
                if user_activity_bytes:
                    user_last_activity = int(user_activity_bytes.decode('utf-8') if isinstance(user_activity_bytes, bytes) else user_activity_bytes)
                
                if partner_activity_bytes:
                    partner_last_activity = int(partner_activity_bytes.decode('utf-8') if isinstance(partner_activity_bytes, bytes) else partner_activity_bytes)
                
                # If no activity timestamp, this is a new chat - set it now
                if user_last_activity is None:
                    await redis_client.set(f"chat:activity:{user_id}", current_time, ex=7200)
                    user_last_activity = current_time
                
                if partner_last_activity is None:
                    await redis_client.set(f"chat:activity:{partner_id}", current_time, ex=7200)
                    partner_last_activity = current_time
                
                # Check if either user has been inactive too long
                user_inactive_time = current_time - user_last_activity
                partner_inactive_time = current_time - partner_last_activity
                
                # Get the longest inactivity time (both users need to be inactive)
                max_inactive_time = min(user_inactive_time, partner_inactive_time)
                
                if max_inactive_time >= inactivity_duration:
                    # Auto-disconnect due to inactivity
                    logger.info(
                        "auto_disconnect_inactivity",
                        user_id=user_id,
                        partner_id=partner_id,
                        inactive_seconds=max_inactive_time
                    )
                    
                    # End the chat
                    await matching.end_chat(user_id)
                    
                    # Clean up activity timestamps
                    await redis_client.delete(f"chat:activity:{user_id}")
                    await redis_client.delete(f"chat:activity:{partner_id}")
                    
                    # Notify both users
                    inactivity_msg = (
                        "⏱️ **Chat ended due to inactivity.**\n\n"
                        f"No messages were exchanged for {inactivity_duration // 60} minutes.\n\n"
                        "Use /chat to find a new partner!"
                    )
                    
                    try:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=inactivity_msg,
                            parse_mode='Markdown'
                        )
                    except Exception as e:
                        logger.debug("notify_user_failed", user_id=user_id, error=str(e))
                    
                    try:
                        await context.bot.send_message(
                            chat_id=partner_id,
                            text=inactivity_msg,
                            parse_mode='Markdown'
                        )
                    except Exception as e:
                        logger.debug("notify_partner_failed", partner_id=partner_id, error=str(e))
                
            except Exception as e:
                logger.debug("check_pair_inactivity_error", pair_key=pair_key, error=str(e))
        
    except Exception as e:
        logger.error("inactivity_check_error", error=str(e))


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
        application.add_handler(CommandHandler("blockmedia", blockmedia_command))
        application.add_handler(CommandHandler("unblockmedia", unblockmedia_command))
        application.add_handler(CommandHandler("blockedmedia", blockedmedia_command))
        application.add_handler(CommandHandler("addbadword", addbadword_command))
        application.add_handler(CommandHandler("removebadword", removebadword_command))
        application.add_handler(CommandHandler("badwords", badwords_command))
        
        # Register bot control commands
        application.add_handler(CommandHandler("maintenance", maintenance_command))
        application.add_handler(CommandHandler("registrations", registrations_command))
        application.add_handler(CommandHandler("forcelogout", forcelogout_command))
        application.add_handler(CommandHandler("resetqueue", resetqueue_command))
        application.add_handler(CommandHandler("enablegender", enablegender_command))
        application.add_handler(CommandHandler("disablegender", disablegender_command))
        application.add_handler(CommandHandler("enableregional", enableregional_command))
        application.add_handler(CommandHandler("disableregional", disableregional_command))
        application.add_handler(CommandHandler("forcematch", forcematch_command))
        application.add_handler(CommandHandler("matchstatus", matchstatus_command))
        
        # Register menu button callback handler
        application.add_handler(
            CallbackQueryHandler(
                menu_button_callback,
                pattern="^action_",
            )
        )
        
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
        
        # Register broadcast button callback handler
        application.add_handler(
            CallbackQueryHandler(
                broadcast_button_callback,
                pattern="^broadcast_btn_",
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
        
        # Register targeted users broadcast conversation handler
        broadcastusers_conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("broadcastusers", broadcastusers_command),
            ],
            states={
                BROADCAST_MESSAGE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, broadcastusers_ids_step),
                ],
                BROADCAST_FILTER_MEDIA: [
                    CallbackQueryHandler(
                        filter_message_type_callback,
                        pattern="^msgtype_",
                    ),
                ],
                BROADCAST_FILTER_MESSAGE: [
                    MessageHandler(
                        (filters.TEXT | filters.PHOTO) & ~filters.COMMAND,
                        filter_message_step,
                    ),
                    CallbackQueryHandler(
                        button_config_callback,
                        pattern="^(add_button|buttons_done)$",
                    ),
                    CallbackQueryHandler(
                        filtered_broadcast_callback,
                        pattern="^broadcast_(filtered_confirm|cancel)$",
                    ),
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel_broadcast)],
        )
        application.add_handler(broadcastusers_conv_handler)
        
        # Register filtered broadcast conversation handler
        filtered_broadcast_conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("broadcastfilter", broadcastfilter_command),
            ],
            states={
                BROADCAST_FILTER_GENDER: [
                    CallbackQueryHandler(
                        filter_gender_callback,
                        pattern="^filter_gender_",
                    ),
                ],
                BROADCAST_FILTER_COUNTRY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, filter_country_step),
                ],
                BROADCAST_FILTER_MEDIA: [
                    CallbackQueryHandler(
                        filter_message_type_callback,
                        pattern="^msgtype_",
                    ),
                ],
                BROADCAST_FILTER_MESSAGE: [
                    MessageHandler(
                        (filters.TEXT | filters.PHOTO) & ~filters.COMMAND,
                        filter_message_step,
                    ),
                    CallbackQueryHandler(
                        button_config_callback,
                        pattern="^(add_button|buttons_done)$",
                    ),
                    CallbackQueryHandler(
                        filtered_broadcast_callback,
                        pattern="^broadcast_(filtered_confirm|cancel)$",
                    ),
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel_broadcast)],
        )
        application.add_handler(filtered_broadcast_conv_handler)
        
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
