"""Command handlers for the bot."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from src.db.redis_client import RedisClient
from src.services.matching import MatchingEngine
from src.services.queue import QueueFullError
from src.services.profile import (
    ProfileManager,
    validate_nickname,
    validate_gender,
    validate_country,
    GENDERS,
    COUNTRIES,
)
from src.services.preferences import (
    PreferenceManager,
    validate_gender_filter,
    validate_country_filter,
    GENDER_FILTERS,
)
from src.services.feedback import (
    FeedbackManager,
    get_feedback_prompt,
)
from src.services.media_preferences import (
    MediaPreferenceManager,
    MediaPreferences,
)
from src.services.admin import AdminManager
from src.utils.decorators import rate_limit
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Conversation states for profile editing
NICKNAME, GENDER, COUNTRY = range(3)

# Conversation states for preferences
PREF_GENDER, PREF_COUNTRY = range(3, 5)

# Conversation states for media settings
MEDIA_SETTINGS = 5

# Conversation states for admin broadcast
BROADCAST_MESSAGE = 6

# Conversation states for ban system
BAN_USER_ID, BAN_REASON, BAN_DURATION = range(7, 10)
UNBAN_USER_ID = 10
WARNING_USER_ID, WARNING_REASON = range(11, 13)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    
    # Register user for broadcast
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    if admin_manager:
        await admin_manager.register_user(
            user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code,
            is_bot=user.is_bot,
            is_premium=user.is_premium
        )
    
    welcome_message = (
        f"👋 Welcome to Anonymous Random Chat, {user.first_name}!\n\n"
        "🎭 Connect with random strangers anonymously.\n"
        "💬 Chat with anyone from around the world.\n\n"
        "📋 **Commands:**\n"
        "/profile - View your profile\n"
        "/editprofile - Create/edit your profile\n"
        "/preferences - Set matching filters\n"
        "/mediasettings - Control media privacy\n"
        "/rating - View your rating\n"
        "/chat - Start searching for a partner\n"
        "/stop - End current chat\n"
        "/next - Skip to next partner\n"
        "/help - Show help message\n\n"
        "🔒 Your identity remains completely anonymous.\n"
        "💡 Create your profile first with /editprofile!\n"
        "⚙️ Customize matching with /preferences!\n"
        "⭐ Rate partners to improve matching!\n"
        "Ready to start? Use /chat to find a partner!"
    )
    
    await update.message.reply_text(
        welcome_message,
        parse_mode="Markdown",
    )
    
    logger.info("start_command", user_id=user.id, username=user.username)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_message = (
        "📚 **How to use this bot:**\n\n"
        "1️⃣ Create your profile with /editprofile\n"
        "   • Choose a nickname\n"
        "   • Select your gender\n"
        "   • Pick your country\n\n"
        "2️⃣ Set matching preferences with /preferences\n"
        "   • Filter by gender (Male/Female/Any)\n"
        "   • Filter by country (specific or Any)\n\n"
        "3️⃣ Configure media privacy with /mediasettings\n"
        "   • Control what media you receive\n"
        "   • Enable text-only mode for safety\n\n"
        "4️⃣ Use /chat to enter the waiting queue\n"
        "5️⃣ Once matched, start chatting with your partner\n"
        "6️⃣ Send text, photos, videos, stickers, voice notes\n"
        "7️⃣ Rate your partner after chatting (👍/👎)\n"
        "8️⃣ Use /next to skip to a new partner\n"
        "9️⃣ Use /stop to end the chat\n\n"
        "📋 **All Commands:**\n"
        "/profile - View your profile\n"
        "/editprofile - Edit your profile\n"
        "/preferences - Set matching filters\n"
        "/mediasettings - Media privacy settings\n"
        "/rating - View your rating\n"
        "/chat - Find a partner\n"
        "/stop - End chat\n"
        "/next - Skip to next\n"
        "/help - Show this message\n"
        "/report - Report abuse\n\n"
        "⚠️ **Rules:**\n"
        "• Be respectful and kind\n"
        "• No spam or abuse\n"
        "• Rate partners honestly\n"
        "• Report issues with /report\n\n"
        "💡 **Rating System:**\n"
        "• Good ratings help you match faster\n"
        "• Toxic users are auto-limited\n"
        "• View your rating with /rating\n\n"
        "🔒 All chats are anonymous and private.\n"
        "Your personal information is never shared."
    )
    
    await update.message.reply_text(
        help_message,
        parse_mode="Markdown",
    )
    
    logger.info("help_command", user_id=update.effective_user.id)


@rate_limit(max_calls=5, period=60)
async def chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /chat command - join queue and find partner."""
    user_id = update.effective_user.id
    matching: MatchingEngine = context.bot_data["matching"]
    preference_manager: PreferenceManager = context.bot_data.get("preference_manager")
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    
    # Check if user is banned
    if admin_manager:
        is_banned, ban_data = await admin_manager.is_user_banned(user_id)
        if is_banned and ban_data:
            reason = ban_data.get("reason", "Unknown")
            expires_at = ban_data.get("expires_at")
            
            ban_reasons_map = {
                "nudity": "Nudity / Explicit Content",
                "spam": "Spam",
                "abuse": "Abuse",
                "fake_reports": "Fake Reports",
                "harassment": "Harassment",
            }
            
            if expires_at:
                from datetime import datetime
                expiry_time = datetime.fromtimestamp(expires_at).strftime("%Y-%m-%d %H:%M:%S")
                ban_msg = (
                    f"🚫 **You are temporarily banned**\n\n"
                    f"Reason: {ban_reasons_map.get(reason, reason)}\n"
                    f"Ban expires: {expiry_time}\n\n"
                    f"You cannot use the bot until the ban expires."
                )
            else:
                ban_msg = (
                    f"🚫 **You are permanently banned**\n\n"
                    f"Reason: {ban_reasons_map.get(reason, reason)}\n\n"
                    f"You cannot use the bot."
                )
            
            await update.message.reply_text(ban_msg, parse_mode="Markdown")
            return
    
    try:
        # Check current state
        state = await matching.get_user_state(user_id)
        
        if state == "IN_CHAT":
            await update.message.reply_text(
                "❌ You're already in a chat!\n"
                "Use /stop to end current chat first."
            )
            return
        
        if state == "IN_QUEUE":
            await update.message.reply_text(
                "⏳ You're already in the queue!\n"
                "Please wait for a partner..."
            )
            return
        
        # Check if user has custom preferences set
        has_preferences = False
        if preference_manager:
            has_preferences = await preference_manager.has_preferences(user_id)
        
        # Try to find a partner
        search_msg = "🔍 Looking for a partner..."
        if not has_preferences:
            search_msg += "\n\n💡 Tip: Use /preferences to filter matches by gender or country!"
        
        await update.message.reply_text(search_msg)
        
        partner_id = await matching.find_partner(user_id)
        
        if partner_id:
            # Match found!
            profile_manager: ProfileManager = context.bot_data.get("profile_manager")
            
            # Get partner's profile
            partner_profile = None
            user_profile = None
            if profile_manager:
                partner_profile = await profile_manager.get_profile(partner_id)
                user_profile = await profile_manager.get_profile(user_id)
            
            # Send match notification to user with partner's profile
            match_msg = "✅ **Partner found!**\n\n"
            if partner_profile:
                match_msg += f"👤 **Partner's Profile:**\n"
                match_msg += f"📝 {partner_profile.nickname}\n"
                match_msg += f"{'👨' if partner_profile.gender == 'Male' else '👩' if partner_profile.gender == 'Female' else '🧑'} {partner_profile.gender}\n"
                match_msg += f"🌍 {partner_profile.country}\n"
            match_msg += "\n👋 Say hi and start chatting!\n"
            match_msg += "Use /next to skip or /stop to end."
            
            await update.message.reply_text(
                match_msg,
                parse_mode="Markdown",
            )
            
            # Send match notification to partner with user's profile
            partner_match_msg = "✅ **Partner found!**\n\n"
            if user_profile:
                partner_match_msg += f"👤 **Partner's Profile:**\n"
                partner_match_msg += f"📝 {user_profile.nickname}\n"
                partner_match_msg += f"{'👨' if user_profile.gender == 'Male' else '👩' if user_profile.gender == 'Female' else '🧑'} {user_profile.gender}\n"
                partner_match_msg += f"🌍 {user_profile.country}\n"
            partner_match_msg += "\n👋 Say hi and start chatting!\n"
            partner_match_msg += "Use /next to skip or /stop to end."
            
            await context.bot.send_message(
                partner_id,
                partner_match_msg,
                parse_mode="Markdown",
            )
            
            logger.info(
                "match_success",
                user_id=user_id,
                partner_id=partner_id,
            )
        else:
            # Added to queue
            queue_size = await matching.queue.get_queue_size()
            await update.message.reply_text(
                f"⏳ You're in the queue!\n\n"
                f"👥 People waiting: {queue_size}\n"
                f"You'll be notified when a partner is found."
            )
            
            logger.info(
                "queue_joined",
                user_id=user_id,
                queue_size=queue_size,
            )
    
    except QueueFullError:
        await update.message.reply_text(
            "⚠️ The queue is currently full.\n"
            "Please try again in a few moments."
        )
    except Exception as e:
        # Check if this is a user limitation error
        error_msg = str(e)
        if "limited" in error_msg.lower() or "rating" in error_msg.lower():
            await update.message.reply_text(
                f"⚠️ {error_msg}"
            )
        else:
            logger.error(
                "chat_command_error",
                user_id=user_id,
                error=error_msg,
            )
            await update.message.reply_text(
                "❌ An error occurred. Please try again."
            )


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command - end current chat."""
    user_id = update.effective_user.id
    matching: MatchingEngine = context.bot_data["matching"]
    
    try:
        # Check if user is in queue
        if await matching.queue.is_in_queue(user_id):
            await matching.queue.leave_queue(user_id)
            await matching.set_user_state(user_id, "IDLE")
            await update.message.reply_text(
                "✅ Removed from queue.\n"
                "Use /chat to search again."
            )
            logger.info("left_queue", user_id=user_id)
            return
        
        # End active chat
        partner_id = await matching.end_chat(user_id)
        
        if partner_id:
            await update.message.reply_text(
                "👋 **Chat ended.**\n\n"
                "Use /chat to find a new partner!",
                parse_mode="Markdown",
            )
            
            # Show feedback prompt
            await show_feedback_prompt(context, user_id, partner_id)
            
            # Notify partner
            try:
                await context.bot.send_message(
                    partner_id,
                    "⚠️ **Partner has left the chat.**\n\n"
                    "Use /chat to find a new partner!",
                    parse_mode="Markdown",
                )
                
                # Show feedback prompt to partner as well
                await show_feedback_prompt(context, partner_id, user_id)
                
            except Exception as e:
                logger.warning(
                    "partner_notification_failed",
                    partner_id=partner_id,
                    error=str(e),
                )
            
            logger.info(
                "chat_stopped",
                user_id=user_id,
                partner_id=partner_id,
            )
        else:
            await update.message.reply_text(
                "❌ You're not in a chat.\n"
                "Use /chat to find a partner!"
            )
    
    except Exception as e:
        logger.error(
            "stop_command_error",
            user_id=user_id,
            error=str(e),
        )
        await update.message.reply_text(
            "❌ An error occurred. Please try again."
        )


@rate_limit(max_calls=10, period=60)
async def next_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /next command - skip to next partner."""
    user_id = update.effective_user.id
    matching: MatchingEngine = context.bot_data["matching"]
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    
    try:
        # End current chat
        partner_id = await matching.end_chat(user_id)
        
        if not partner_id:
            await update.message.reply_text(
                "❌ You're not in a chat.\n"
                "Use /chat to find a partner!"
            )
            return
        
        # Track skip count
        if admin_manager:
            await admin_manager.increment_skip_count(user_id)
        
        # Show feedback prompt for previous partner
        await show_feedback_prompt(context, user_id, partner_id)
        
        # Notify previous partner
        try:
            await context.bot.send_message(
                partner_id,
                "⚠️ **Partner skipped to next chat.**\n\n"
                "Use /chat to find a new partner!",
                parse_mode="Markdown",
            )
            
            # Show feedback prompt to partner as well
            await show_feedback_prompt(context, partner_id, user_id)
            
        except Exception as e:
            logger.warning(
                "partner_notification_failed",
                partner_id=partner_id,
                error=str(e),
            )
        
        # Find new partner
        await update.message.reply_text(
            "🔍 Looking for a new partner..."
        )
        
        new_partner_id = await matching.find_partner(user_id)
        
        if new_partner_id:
            profile_manager: ProfileManager = context.bot_data.get("profile_manager")
            activity_manager = context.bot_data.get("activity_manager")
            
            # Get partner's profile
            partner_profile = None
            user_profile = None
            if profile_manager:
                partner_profile = await profile_manager.get_profile(new_partner_id)
                user_profile = await profile_manager.get_profile(user_id)
            
            # Get partner's online status
            partner_status = ""
            if activity_manager:
                partner_status = await activity_manager.get_status_text(new_partner_id)
            
            # Send match notification to user with partner's profile
            match_msg = "✅ **New partner found!**\n\n"
            if partner_profile:
                match_msg += f"👤 **Partner's Profile:**\n"
                match_msg += f"📝 {partner_profile.nickname}\n"
                match_msg += f"{'👨' if partner_profile.gender == 'Male' else '👩' if partner_profile.gender == 'Female' else '🧑'} {partner_profile.gender}\n"
                match_msg += f"🌍 {partner_profile.country}\n"
            if partner_status:
                match_msg += f"📶 {partner_status}\n"
            match_msg += "\n👋 Say hi and start chatting!"
            
            await update.message.reply_text(
                match_msg,
                parse_mode="Markdown",
            )
            
            # Get user's online status
            user_status = ""
            if activity_manager:
                user_status = await activity_manager.get_status_text(user_id)
            
            # Send match notification to partner with user's profile
            partner_match_msg = "✅ **Partner found!**\n\n"
            if user_profile:
                partner_match_msg += f"👤 **Partner's Profile:**\n"
                partner_match_msg += f"📝 {user_profile.nickname}\n"
                partner_match_msg += f"{'👨' if user_profile.gender == 'Male' else '👩' if user_profile.gender == 'Female' else '🧑'} {user_profile.gender}\n"
                partner_match_msg += f"🌍 {user_profile.country}\n"
            if user_status:
                partner_match_msg += f"📶 {user_status}\n"
            partner_match_msg += "\n👋 Say hi and start chatting!"
            
            await context.bot.send_message(
                new_partner_id,
                partner_match_msg,
                parse_mode="Markdown",
            )
            
            logger.info(
                "next_match_success",
                user_id=user_id,
                new_partner_id=new_partner_id,
            )
        else:
            queue_size = await matching.queue.get_queue_size()
            await update.message.reply_text(
                f"⏳ Searching for a partner...\n\n"
                f"👥 People waiting: {queue_size}\n"
                f"You'll be notified when someone is found."
            )
    
    except Exception as e:
        logger.error(
            "next_command_error",
            user_id=user_id,
            error=str(e),
        )
        await update.message.reply_text(
            "❌ An error occurred. Please try again."
        )


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /report command - report abuse."""
    user_id = update.effective_user.id
    redis_client: RedisClient = context.bot_data.get("redis")
    
    if not redis_client:
        await update.message.reply_text("❌ Service unavailable")
        return
    
    try:
        # Check if user is in chat
        partner_key = f"pair:{user_id}"
        partner_id_bytes = await redis_client.get(partner_key)
        
        if not partner_id_bytes:
            await update.message.reply_text(
                "⚠️ **No Active Chat**\n\n"
                "You can only report users while in an active chat.\n"
                "Start a chat with /start and match with someone first."
            )
            return
        
        partner_id = int(partner_id_bytes.decode('utf-8'))
        
        # Store partner ID in user context for callback
        context.user_data['report_target'] = partner_id
        
        # Show report reasons as inline keyboard
        keyboard = [
            [InlineKeyboardButton("🔞 Nudity / Explicit Content", callback_data="report_nudity")],
            [InlineKeyboardButton("😠 Harassment / Abuse", callback_data="report_harassment")],
            [InlineKeyboardButton("📧 Spam / Advertising", callback_data="report_spam")],
            [InlineKeyboardButton("💰 Scam / Fraud", callback_data="report_scam")],
            [InlineKeyboardButton("🎭 Fake Profile", callback_data="report_fake")],
            [InlineKeyboardButton("❓ Other Reason", callback_data="report_other")],
            [InlineKeyboardButton("❌ Cancel", callback_data="report_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚠️ **Report Your Chat Partner**\n\n"
            f"You are about to report User ID: `{partner_id}`\n\n"
            "Please select the reason for reporting:\n\n"
            "⚠️ **Important Notes:**\n"
            "• False reports may result in penalties\n"
            "• Your report will be reviewed by moderators\n"
            "• You can continue or end the chat after reporting",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        logger.info(
            "report_command",
            user_id=user_id,
            partner_id=partner_id
        )
        
    except Exception as e:
        logger.error("report_command_error", user_id=user_id, error=str(e))
        await update.message.reply_text(
            "❌ Error processing report. Please try again."
        )


async def report_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle report reason selection callbacks."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    redis_client: RedisClient = context.bot_data.get("redis")
    
    if not redis_client:
        await query.edit_message_text("❌ Service unavailable")
        return
    
    try:
        # Get the target user from context
        partner_id = context.user_data.get('report_target')
        if not partner_id:
            await query.edit_message_text(
                "❌ Report session expired. Please use /report again."
            )
            return
        
        # Handle cancel
        if query.data == "report_cancel":
            await query.edit_message_text(
                "❌ Report cancelled.\n\n"
                "You can report anytime using /report while in a chat."
            )
            context.user_data.pop('report_target', None)
            return
        
        # Extract report reason from callback data
        report_flags = {
            "report_nudity": "nudity",
            "report_harassment": "harassment",
            "report_spam": "spam",
            "report_scam": "scam",
            "report_fake": "fake",
            "report_other": "other"
        }
        
        flag = report_flags.get(query.data)
        if not flag:
            await query.edit_message_text("❌ Invalid report reason")
            return
        
        # Save the report to Redis
        import json
        import time
        
        # Create report data
        report_data = {
            "reporter_id": user_id,
            "reported_id": partner_id,
            "flag": flag,
            "timestamp": int(time.time())
        }
        
        # Store report in reported user's report list
        reports_key = f"stats:{partner_id}:reports"
        await redis_client.lpush(reports_key, json.dumps(report_data))
        
        # Increment report count
        count_key = f"stats:{partner_id}:report_count"
        new_count = await redis_client.incr(count_key)
        
        # Flag type counts
        flag_key = f"stats:{partner_id}:report_flags:{flag}"
        await redis_client.incr(flag_key)
        
        # Clean up context
        context.user_data.pop('report_target', None)
        
        flag_names = {
            "nudity": "Nudity / Explicit Content",
            "harassment": "Harassment / Abuse",
            "spam": "Spam / Advertising",
            "scam": "Scam / Fraud",
            "fake": "Fake Profile",
            "other": "Other Reason"
        }
        
        await query.edit_message_text(
            f"✅ **Report Submitted**\n\n"
            f"You have reported User ID: `{partner_id}`\n"
            f"Reason: **{flag_names[flag]}**\n\n"
            f"📋 Report #{new_count} for this user\n\n"
            f"Thank you for helping keep our community safe.\n"
            f"Our moderation team will review this report.\n\n"
            f"You can:\n"
            f"• Continue the chat\n"
            f"• Use /next to find a new partner\n"
            f"• Use /stop to end the chat",
            parse_mode="Markdown"
        )
        
        logger.info(
            "report_submitted",
            reporter_id=user_id,
            reported_id=partner_id,
            flag=flag,
            total_reports=new_count
        )
        
        # Check if user should be auto-banned (threshold: 5 reports)
        if new_count >= 5:
            admin_manager: AdminManager = context.bot_data.get("admin_manager")
            if admin_manager:
                # Auto-ban for 24 hours after 5 reports
                await admin_manager.ban_user(
                    user_id=partner_id,
                    banned_by=0,  # System ban
                    reason="Multiple user reports",
                    duration=86400,  # 24 hours
                    is_auto_ban=True
                )
                logger.warning(
                    "user_auto_banned",
                    user_id=partner_id,
                    report_count=new_count
                )
        
    except Exception as e:
        logger.error("report_callback_error", user_id=user_id, error=str(e))
        await query.edit_message_text(
            "❌ Error submitting report. Please try again."
        )


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /profile command - show user's profile."""
    user_id = update.effective_user.id
    profile_manager: ProfileManager = context.bot_data.get("profile_manager")
    
    if not profile_manager:
        await update.message.reply_text("❌ Profile service unavailable")
        return
    
    try:
        profile = await profile_manager.get_profile(user_id)
        
        if not profile:
            await update.message.reply_text(
                "❌ **You don't have a profile yet!**\n\n"
                "Create one using /editprofile\n\n"
                "Your profile helps other users know:\n"
                "• Your nickname\n"
                "• Your gender\n"
                "• Your country\n\n"
                "🔒 Your Telegram name remains private.",
                parse_mode="Markdown",
            )
            return
        
        # Show profile with edit button
        keyboard = [[InlineKeyboardButton("✏️ Edit Profile", callback_data="edit_profile")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            profile.to_display(),
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )
        
        logger.info("profile_viewed", user_id=user_id)
        
    except Exception as e:
        logger.error("profile_command_error", user_id=user_id, error=str(e))
        await update.message.reply_text(
            "❌ An error occurred. Please try again."
        )


async def editprofile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /editprofile command - start profile creation/editing."""
    user_id = update.effective_user.id
    profile_manager: ProfileManager = context.bot_data.get("profile_manager")
    
    # Handle both callback queries and regular messages
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message_method = query.edit_message_text
    else:
        message_method = update.message.reply_text
    
    if not profile_manager:
        await message_method("❌ Profile service unavailable")
        return ConversationHandler.END
    
    try:
        profile = await profile_manager.get_profile(user_id)
        
        if profile:
            text = (
                f"📝 **Edit Your Profile**\n\n"
                f"Current profile:\n"
                f"{profile.to_display()}\n\n"
                f"━━━━━━━━━━━━━━━\n"
                f"Let's update your nickname.\n"
                f"Send your new nickname (2-30 characters):"
            )
        else:
            text = (
                "👋 **Welcome! Let's create your profile**\n\n"
                "Your profile helps others know who they're chatting with.\n"
                "Don't worry - your Telegram name stays private! 🔒\n\n"
                "━━━━━━━━━━━━━━━\n"
                "Step 1: Choose a nickname\n"
                "Send your nickname (2-30 characters):"
            )
        
        await message_method(text, parse_mode="Markdown")
        
        logger.info("editprofile_started", user_id=user_id)
        return NICKNAME
        
    except Exception as e:
        logger.error("editprofile_command_error", user_id=user_id, error=str(e))
        try:
            await message_method("❌ An error occurred. Please try again.")
        except:
            pass
        return ConversationHandler.END


async def nickname_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle nickname input during profile creation."""
    nickname = update.message.text.strip()
    
    # Validate nickname
    is_valid, error_msg = validate_nickname(nickname)
    if not is_valid:
        await update.message.reply_text(
            f"❌ {error_msg}\n\n"
            "Please send a valid nickname:"
        )
        return NICKNAME
    
    # Store nickname in context
    context.user_data["nickname"] = nickname
    
    # Create gender selection keyboard
    keyboard = [
        [InlineKeyboardButton(f"👨 {GENDERS[0]}", callback_data=f"gender_{GENDERS[0]}")],
        [InlineKeyboardButton(f"👩 {GENDERS[1]}", callback_data=f"gender_{GENDERS[1]}")],
        [InlineKeyboardButton(f"🧑 {GENDERS[2]}", callback_data=f"gender_{GENDERS[2]}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ Nickname set to: **{nickname}**\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Step 2: Select your gender:",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )
    
    return GENDER


async def gender_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle gender selection via callback."""
    query = update.callback_query
    await query.answer()
    
    gender = query.data.replace("gender_", "")
    
    # Validate gender
    is_valid, error_msg = validate_gender(gender)
    if not is_valid:
        await query.message.reply_text(f"❌ {error_msg}")
        return GENDER
    
    # Store gender in context
    context.user_data["gender"] = gender
    
    # Show country selection with popular countries first
    popular_countries = ["India", "United States", "United Kingdom", "Pakistan", 
                        "Bangladesh", "Nepal", "Canada", "Australia", "Other"]
    
    keyboard = []
    for country in popular_countries:
        keyboard.append([InlineKeyboardButton(f"🌍 {country}", callback_data=f"country_{country}")])
    
    keyboard.append([InlineKeyboardButton("📋 See All Countries", callback_data="country_all")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"✅ Gender set to: **{gender}**\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Step 3: Select your country:",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )
    
    return COUNTRY


async def country_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle country selection via callback."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "country_all":
        # Show message to type country name
        await query.edit_message_text(
            "🌍 **Type your country name:**\n\n"
            "Send the name of your country.\n"
            "Examples: Germany, Japan, Brazil, etc.",
            parse_mode="Markdown",
        )
        return COUNTRY
    
    country = query.data.replace("country_", "")
    
    # Validate country
    is_valid, error_msg = validate_country(country)
    if not is_valid:
        await query.message.reply_text(f"❌ {error_msg}")
        return COUNTRY
    
    # Store country and save profile
    context.user_data["country"] = country
    
    # Save profile to Redis
    user_id = update.effective_user.id
    profile_manager: ProfileManager = context.bot_data.get("profile_manager")
    
    try:
        profile = await profile_manager.create_profile(
            user_id=user_id,
            nickname=context.user_data["nickname"],
            gender=context.user_data["gender"],
            country=country,
        )
        
        await query.edit_message_text(
            "✅ **Profile Created Successfully!**\n\n"
            f"{profile.to_display()}\n\n"
            "━━━━━━━━━━━━━━━\n"
            "You can:\n"
            "• View profile: /profile\n"
            "• Edit profile: /editprofile\n"
            "• Start chatting: /chat",
            parse_mode="Markdown",
        )
        
        logger.info(
            "profile_created_success",
            user_id=user_id,
            nickname=profile.nickname,
        )
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
        
    except Exception as e:
        logger.error("profile_save_error", user_id=user_id, error=str(e))
        await query.message.reply_text(
            "❌ Failed to save profile. Please try again with /editprofile"
        )
        context.user_data.clear()
        return ConversationHandler.END


async def country_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle country input as text."""
    country = update.message.text.strip()
    
    # Find closest match (case-insensitive)
    country_match = None
    for c in COUNTRIES:
        if c.lower() == country.lower():
            country_match = c
            break
    
    if not country_match:
        await update.message.reply_text(
            f"❌ Country '{country}' not found.\n\n"
            "Please send a valid country name or use /cancel to stop."
        )
        return COUNTRY
    
    # Store country and save profile
    context.user_data["country"] = country_match
    user_id = update.effective_user.id
    profile_manager: ProfileManager = context.bot_data.get("profile_manager")
    
    try:
        profile = await profile_manager.create_profile(
            user_id=user_id,
            nickname=context.user_data["nickname"],
            gender=context.user_data["gender"],
            country=country_match,
        )
        
        await update.message.reply_text(
            "✅ **Profile Created Successfully!**\n\n"
            f"{profile.to_display()}\n\n"
            "━━━━━━━━━━━━━━━\n"
            "You can:\n"
            "• View profile: /profile\n"
            "• Edit profile: /editprofile\n"
            "• Start chatting: /chat",
            parse_mode="Markdown",
        )
        
        logger.info(
            "profile_created_success",
            user_id=user_id,
            nickname=profile.nickname,
        )
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
        
    except Exception as e:
        logger.error("profile_save_error", user_id=user_id, error=str(e))
        await update.message.reply_text(
            "❌ Failed to save profile. Please try again with /editprofile"
        )
        context.user_data.clear()
        return ConversationHandler.END


async def cancel_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel profile creation/editing."""
    await update.message.reply_text(
        "❌ Profile editing cancelled.\n\n"
        "You can start again with /editprofile anytime."
    )
    
    context.user_data.clear()
    logger.info("profile_editing_cancelled", user_id=update.effective_user.id)
    return ConversationHandler.END


# ============ PREFERENCES COMMANDS ============


async def preferences_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /preferences command - show and edit matching preferences.
    Entry point for preferences conversation.
    """
    user_id = update.effective_user.id
    preference_manager: PreferenceManager = context.bot_data.get("preference_manager")
    
    if not preference_manager:
        await update.message.reply_text(
            "❌ Preference system is not available. Please try again later."
        )
        return ConversationHandler.END
    
    try:
        # Get current preferences
        preferences = await preference_manager.get_preferences(user_id)
        
        # Show current preferences with edit options
        keyboard = [
            [
                InlineKeyboardButton("🔄 Change Gender Filter", callback_data="pref_gender"),
                InlineKeyboardButton("🌍 Change Country Filter", callback_data="pref_country"),
            ],
            [
                InlineKeyboardButton("🔄 Reset to Defaults", callback_data="pref_reset"),
                InlineKeyboardButton("❌ Cancel", callback_data="pref_cancel"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = (
            f"{preferences.to_display()}\n\n"
            "━━━━━━━━━━━━━━━\n"
            "💡 Preferences help you find partners that match your criteria.\n"
            "Choose what to change:"
        )
        
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
        
        logger.info("preferences_shown", user_id=user_id)
        return PREF_GENDER  # Wait for user choice
        
    except Exception as e:
        logger.error("preferences_command_error", user_id=user_id, error=str(e))
        await update.message.reply_text(
            "❌ Failed to load preferences. Please try again."
        )
        return ConversationHandler.END


async def pref_gender_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle gender filter selection callback."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    callback_data = query.data
    
    if callback_data == "pref_gender":
        # Show gender filter options
        keyboard = [
            [
                InlineKeyboardButton("👨 Male", callback_data="pref_gender_male"),
                InlineKeyboardButton("👩 Female", callback_data="pref_gender_female"),
            ],
            [
                InlineKeyboardButton("🧑 Any", callback_data="pref_gender_any"),
            ],
            [InlineKeyboardButton("⬅️ Back", callback_data="pref_back")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "👤 **Select Gender Filter:**\n\n"
            "Choose the gender of partners you want to match with:",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
        
        return PREF_GENDER
    
    elif callback_data.startswith("pref_gender_"):
        # User selected a gender filter
        gender_map = {
            "pref_gender_male": "Male",
            "pref_gender_female": "Female",
            "pref_gender_any": "Any",
        }
        
        selected_gender = gender_map.get(callback_data)
        if not selected_gender:
            await query.edit_message_text("❌ Invalid selection. Use /preferences to try again.")
            return ConversationHandler.END
        
        # Validate
        is_valid, error_msg = validate_gender_filter(selected_gender)
        if not is_valid:
            await query.edit_message_text(f"❌ {error_msg}\nUse /preferences to try again.")
            return ConversationHandler.END
        
        # Save preference
        preference_manager: PreferenceManager = context.bot_data["preference_manager"]
        try:
            preferences = await preference_manager.set_preferences(
                user_id=user_id,
                gender_filter=selected_gender,
            )
            
            gender_emoji = {"Male": "👨", "Female": "👩", "Any": "🧑"}
            
            await query.edit_message_text(
                f"✅ Gender filter updated to: {gender_emoji.get(selected_gender, '🧑')} **{selected_gender}**\n\n"
                f"{preferences.to_display()}\n\n"
                "Use /preferences to change other settings or /chat to start matching!",
                parse_mode="Markdown",
            )
            
            logger.info("gender_filter_updated", user_id=user_id, gender=selected_gender)
            return ConversationHandler.END
            
        except Exception as e:
            logger.error("gender_filter_save_error", user_id=user_id, error=str(e))
            await query.edit_message_text(
                "❌ Failed to save gender filter. Use /preferences to try again."
            )
            return ConversationHandler.END
    
    elif callback_data == "pref_country":
        # Move to country selection
        await query.edit_message_text(
            "🌍 **Country Filter**\n\n"
            "Type the name of the country you want to match with (e.g., 'USA', 'India').\n"
            "Or type 'Any' to match with anyone.\n\n"
            "Use /cancel to cancel.",
        )
        return PREF_COUNTRY
    
    elif callback_data == "pref_reset":
        # Reset to defaults
        preference_manager: PreferenceManager = context.bot_data["preference_manager"]
        try:
            await preference_manager.delete_preferences(user_id)
            
            await query.edit_message_text(
                "✅ Preferences reset to defaults!\n\n"
                "🧑 Gender: Any\n"
                "🌍 Country: Any\n\n"
                "Use /preferences to set custom filters or /chat to start matching!"
            )
            
            logger.info("preferences_reset", user_id=user_id)
            return ConversationHandler.END
            
        except Exception as e:
            logger.error("preferences_reset_error", user_id=user_id, error=str(e))
            await query.edit_message_text(
                "❌ Failed to reset preferences. Use /preferences to try again."
            )
            return ConversationHandler.END
    
    elif callback_data == "pref_cancel":
        await query.edit_message_text(
            "❌ Preferences editing cancelled.\n\n"
            "Your current preferences remain unchanged.\n"
            "Use /preferences anytime to change them."
        )
        logger.info("preferences_cancelled", user_id=user_id)
        return ConversationHandler.END
    
    elif callback_data == "pref_back":
        # Go back to main preferences menu
        return await preferences_command(update, context)
    
    return ConversationHandler.END


async def pref_country_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle country filter text input."""
    user_id = update.effective_user.id
    country = update.message.text.strip()
    
    # Validate country
    is_valid, error_msg = validate_country_filter(country)
    if not is_valid:
        await update.message.reply_text(
            f"❌ {error_msg}\n\n"
            f"Please enter a valid country name or 'Any'.\n"
            f"Use /cancel to cancel."
        )
        return PREF_COUNTRY
    
    # Save preference
    preference_manager: PreferenceManager = context.bot_data["preference_manager"]
    try:
        preferences = await preference_manager.set_preferences(
            user_id=user_id,
            country_filter=country,
        )
        
        country_emoji = "🌍" if country == "Any" else "📍"
        
        await update.message.reply_text(
            f"✅ Country filter updated to: {country_emoji} **{country}**\n\n"
            f"{preferences.to_display()}\n\n"
            "Use /preferences to change other settings or /chat to start matching!",
            parse_mode="Markdown",
        )
        
        logger.info("country_filter_updated", user_id=user_id, country=country)
        return ConversationHandler.END
        
    except Exception as e:
        logger.error("country_filter_save_error", user_id=user_id, error=str(e))
        await update.message.reply_text(
            "❌ Failed to save country filter. Use /preferences to try again."
        )
        return ConversationHandler.END


async def cancel_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel preferences editing."""
    await update.message.reply_text(
        "❌ Preferences editing cancelled.\n\n"
        "You can start again with /preferences anytime."
    )
    
    context.user_data.clear()
    logger.info("preferences_editing_cancelled", user_id=update.effective_user.id)
    return ConversationHandler.END


# ============ FEEDBACK HANDLERS ============


async def show_feedback_prompt(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    partner_id: int,
):
    """
    Show feedback prompt to user after chat ends.
    
    Args:
        context: Bot context
        user_id: User to show prompt to
        partner_id: Partner who was just chatted with
    """
    try:
        # Store partner_id in user context for feedback callback
        # Note: We use bot-level storage since user_data is per-handler
        feedback_key = f"pending_feedback:{user_id}"
        redis = context.bot_data["redis"]
        
        # Store partner_id for 5 minutes
        await redis.set(feedback_key, str(partner_id), ex=300)
        
        # Get feedback prompt
        message_text, keyboard_data = get_feedback_prompt()
        
        # Convert to InlineKeyboardMarkup
        keyboard = [
            [InlineKeyboardButton(btn["text"], callback_data=btn["callback_data"]) for btn in row]
            for row in keyboard_data
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            user_id,
            message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
        
        logger.info("feedback_prompt_shown", user_id=user_id, partner_id=partner_id)
        
    except Exception as e:
        logger.error(
            "feedback_prompt_error",
            user_id=user_id,
            partner_id=partner_id,
            error=str(e),
        )


async def feedback_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle feedback button callbacks."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    callback_data = query.data
    
    try:
        # Get partner_id from storage
        feedback_key = f"pending_feedback:{user_id}"
        redis = context.bot_data["redis"]
        partner_data = await redis.get(feedback_key)
        
        if not partner_data:
            await query.edit_message_text(
                "⏰ Feedback session expired. You can rate your next partner!"
            )
            return
        
        partner_id = int(partner_data.decode())
        
        # Handle skip
        if callback_data == "feedback_skip":
            await redis.delete(feedback_key)
            await query.edit_message_text(
                "⏭️ Rating skipped.\n\n"
                "Use /chat to find a new partner!"
            )
            logger.info("feedback_skipped", user_id=user_id, partner_id=partner_id)
            return
        
        # Process rating
        feedback_manager: FeedbackManager = context.bot_data.get("feedback_manager")
        if not feedback_manager:
            await query.edit_message_text(
                "❌ Feedback system unavailable. Please try again later."
            )
            return
        
        is_positive = callback_data == "feedback_positive"
        
        # Record feedback
        recorded = await feedback_manager.record_feedback(
            rater_id=user_id,
            rated_user_id=partner_id,
            is_positive=is_positive,
        )
        
        if recorded:
            # Clean up pending feedback
            await redis.delete(feedback_key)
            
            # Get updated rating for display
            partner_rating = await feedback_manager.get_rating(partner_id)
            
            rating_emoji = "👍" if is_positive else "👎"
            
            await query.edit_message_text(
                f"✅ {rating_emoji} **Feedback recorded!**\n\n"
                f"Thank you for helping improve the community.\n"
                f"Partner's new score: {partner_rating.rating_score:.1f}%\n\n"
                f"Use /chat to find a new partner!",
                parse_mode="Markdown",
            )
            
            logger.info(
                "feedback_recorded",
                user_id=user_id,
                partner_id=partner_id,
                is_positive=is_positive,
            )
        else:
            await query.edit_message_text(
                "ℹ️ You've already rated this partner.\n\n"
                "Use /chat to find a new partner!"
            )
    
    except Exception as e:
        logger.error(
            "feedback_callback_error",
            user_id=user_id,
            error=str(e),
        )
        await query.edit_message_text(
            "❌ Failed to record feedback. Please try again."
        )


async def rating_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /rating command - show user's rating."""
    user_id = update.effective_user.id
    feedback_manager: FeedbackManager = context.bot_data.get("feedback_manager")
    
    if not feedback_manager:
        await update.message.reply_text(
            "❌ Rating system is not available."
        )
        return
    
    try:
        rating = await feedback_manager.get_rating(user_id)
        
        await update.message.reply_text(
            f"📊 **Your Rating**\n\n"
            f"{rating.to_display()}\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💡 Be respectful to improve your rating!\n"
            f"Good ratings help you match faster.",
            parse_mode="Markdown",
        )
        
        logger.info("rating_viewed", user_id=user_id, score=rating.rating_score)
        
    except Exception as e:
        logger.error("rating_command_error", user_id=user_id, error=str(e))
        await update.message.reply_text(
            "❌ Failed to load rating. Please try again."
        )


async def mediasettings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /mediasettings command - show media privacy settings."""
    user_id = update.effective_user.id
    media_manager: MediaPreferenceManager = context.bot_data.get("media_manager")
    
    if not media_manager:
        await update.message.reply_text(
            "❌ Media settings are not available."
        )
        return ConversationHandler.END
    
    try:
        # Get current preferences
        preferences = await media_manager.get_preferences(user_id)
        
        # Build settings message
        settings_msg = "🎛️ **Media Privacy Settings**\n\n"
        settings_msg += "Control what types of media you want to receive:\n\n"
        
        if preferences.text_only:
            settings_msg += "🔒 **Text-Only Mode: ENABLED**\n"
            settings_msg += "You only receive text messages.\n"
        else:
            settings_msg += "📷 Images: " + ("✅ Allowed" if preferences.allow_images else "❌ Blocked") + "\n"
            settings_msg += "🎥 Videos: " + ("✅ Allowed" if preferences.allow_videos else "❌ Blocked") + "\n"
            settings_msg += "🎤 Voice Notes: " + ("✅ Allowed" if preferences.allow_voice else "❌ Blocked") + "\n"
            settings_msg += "🎵 Audio: " + ("✅ Allowed" if preferences.allow_audio else "❌ Blocked") + "\n"
            settings_msg += "📎 Documents: " + ("✅ Allowed" if preferences.allow_documents else "❌ Blocked") + "\n"
            settings_msg += "😀 Stickers: " + ("✅ Allowed" if preferences.allow_stickers else "❌ Blocked") + "\n"
            settings_msg += "📹 Video Notes: " + ("✅ Allowed" if preferences.allow_video_notes else "❌ Blocked") + "\n"
            settings_msg += "📍 Locations: " + ("✅ Allowed" if preferences.allow_locations else "❌ Blocked") + "\n"
        
        settings_msg += "\n💡 Tap a button to toggle a setting:"
        
        # Build keyboard
        keyboard = []
        
        if preferences.text_only:
            # Show only text-only toggle if enabled
            keyboard.append([
                InlineKeyboardButton("🔓 Disable Text-Only Mode", callback_data="media_text_only_off")
            ])
        else:
            # Show all media type toggles
            keyboard.extend([
                [
                    InlineKeyboardButton(
                        f"{'❌ Block' if preferences.allow_images else '✅ Allow'} Images",
                        callback_data="media_toggle_images"
                    ),
                    InlineKeyboardButton(
                        f"{'❌ Block' if preferences.allow_videos else '✅ Allow'} Videos",
                        callback_data="media_toggle_videos"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        f"{'❌ Block' if preferences.allow_voice else '✅ Allow'} Voice",
                        callback_data="media_toggle_voice"
                    ),
                    InlineKeyboardButton(
                        f"{'❌ Block' if preferences.allow_audio else '✅ Allow'} Audio",
                        callback_data="media_toggle_audio"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        f"{'❌ Block' if preferences.allow_documents else '✅ Allow'} Documents",
                        callback_data="media_toggle_documents"
                    ),
                    InlineKeyboardButton(
                        f"{'❌ Block' if preferences.allow_stickers else '✅ Allow'} Stickers",
                        callback_data="media_toggle_stickers"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        f"{'❌ Block' if preferences.allow_video_notes else '✅ Allow'} Video Notes",
                        callback_data="media_toggle_video_notes"
                    ),
                    InlineKeyboardButton(
                        f"{'❌ Block' if preferences.allow_locations else '✅ Allow'} Locations",
                        callback_data="media_toggle_locations"
                    ),
                ],
                [
                    InlineKeyboardButton("🔒 Enable Text-Only Mode", callback_data="media_text_only_on")
                ],
            ])
        
        keyboard.append([
            InlineKeyboardButton("✅ Done", callback_data="media_done")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            settings_msg,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
        
        return MEDIA_SETTINGS
        
    except Exception as e:
        logger.error("mediasettings_command_error", user_id=user_id, error=str(e))
        await update.message.reply_text(
            "❌ Failed to load media settings. Please try again."
        )
        return ConversationHandler.END


async def media_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle media settings button callbacks."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    media_manager: MediaPreferenceManager = context.bot_data.get("media_manager")
    callback_data = query.data
    
    if not media_manager:
        await query.edit_message_text("❌ Media settings are not available.")
        return ConversationHandler.END
    
    try:
        if callback_data == "media_done":
            await query.edit_message_text(
                "✅ **Media settings saved!**\n\n"
                "Your privacy preferences have been updated.",
                parse_mode="Markdown",
            )
            return ConversationHandler.END
        
        # Get current preferences
        preferences = await media_manager.get_preferences(user_id)
        
        # Handle text-only mode toggles
        if callback_data == "media_text_only_on":
            preferences.text_only = True
            await media_manager.set_preferences(user_id, preferences)
            success_msg = "🔒 Text-only mode enabled! You'll only receive text messages."
        
        elif callback_data == "media_text_only_off":
            preferences.text_only = False
            await media_manager.set_preferences(user_id, preferences)
            success_msg = "🔓 Text-only mode disabled! You can now configure individual media types."
        
        # Handle individual media type toggles
        elif callback_data.startswith("media_toggle_"):
            media_type = callback_data.replace("media_toggle_", "")
            
            media_map = {
                "images": "allow_images",
                "videos": "allow_videos",
                "voice": "allow_voice",
                "audio": "allow_audio",
                "documents": "allow_documents",
                "stickers": "allow_stickers",
                "video_notes": "allow_video_notes",
                "locations": "allow_locations",
            }
            
            if media_type in media_map:
                pref_key = media_map[media_type]
                current_value = getattr(preferences, pref_key)
                new_value = not current_value
                
                setattr(preferences, pref_key, new_value)
                await media_manager.set_preferences(user_id, preferences)
                
                action = "blocked" if not new_value else "allowed"
                success_msg = f"✅ {media_type.replace('_', ' ').title()} {action}!"
            else:
                success_msg = "❌ Invalid option."
        
        else:
            success_msg = "❌ Unknown action."
        
        # Refresh the settings display
        preferences = await media_manager.get_preferences(user_id)
        
        settings_msg = "🎛️ **Media Privacy Settings**\n\n"
        settings_msg += "Control what types of media you want to receive:\n\n"
        
        if preferences.text_only:
            settings_msg += "🔒 **Text-Only Mode: ENABLED**\n"
            settings_msg += "You only receive text messages.\n"
        else:
            settings_msg += "📷 Images: " + ("✅ Allowed" if preferences.allow_images else "❌ Blocked") + "\n"
            settings_msg += "🎥 Videos: " + ("✅ Allowed" if preferences.allow_videos else "❌ Blocked") + "\n"
            settings_msg += "🎤 Voice Notes: " + ("✅ Allowed" if preferences.allow_voice else "❌ Blocked") + "\n"
            settings_msg += "🎵 Audio: " + ("✅ Allowed" if preferences.allow_audio else "❌ Blocked") + "\n"
            settings_msg += "📎 Documents: " + ("✅ Allowed" if preferences.allow_documents else "❌ Blocked") + "\n"
            settings_msg += "😀 Stickers: " + ("✅ Allowed" if preferences.allow_stickers else "❌ Blocked") + "\n"
            settings_msg += "📹 Video Notes: " + ("✅ Allowed" if preferences.allow_video_notes else "❌ Blocked") + "\n"
            settings_msg += "📍 Locations: " + ("✅ Allowed" if preferences.allow_locations else "❌ Blocked") + "\n"
        
        settings_msg += f"\n{success_msg}\n"
        settings_msg += "\n💡 Tap a button to toggle a setting:"
        
        # Rebuild keyboard
        keyboard = []
        
        if preferences.text_only:
            keyboard.append([
                InlineKeyboardButton("🔓 Disable Text-Only Mode", callback_data="media_text_only_off")
            ])
        else:
            keyboard.extend([
                [
                    InlineKeyboardButton(
                        f"{'❌ Block' if preferences.allow_images else '✅ Allow'} Images",
                        callback_data="media_toggle_images"
                    ),
                    InlineKeyboardButton(
                        f"{'❌ Block' if preferences.allow_videos else '✅ Allow'} Videos",
                        callback_data="media_toggle_videos"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        f"{'❌ Block' if preferences.allow_voice else '✅ Allow'} Voice",
                        callback_data="media_toggle_voice"
                    ),
                    InlineKeyboardButton(
                        f"{'❌ Block' if preferences.allow_audio else '✅ Allow'} Audio",
                        callback_data="media_toggle_audio"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        f"{'❌ Block' if preferences.allow_documents else '✅ Allow'} Documents",
                        callback_data="media_toggle_documents"
                    ),
                    InlineKeyboardButton(
                        f"{'❌ Block' if preferences.allow_stickers else '✅ Allow'} Stickers",
                        callback_data="media_toggle_stickers"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        f"{'❌ Block' if preferences.allow_video_notes else '✅ Allow'} Video Notes",
                        callback_data="media_toggle_video_notes"
                    ),
                    InlineKeyboardButton(
                        f"{'❌ Block' if preferences.allow_locations else '✅ Allow'} Locations",
                        callback_data="media_toggle_locations"
                    ),
                ],
                [
                    InlineKeyboardButton("🔒 Enable Text-Only Mode", callback_data="media_text_only_on")
                ],
            ])
        
        keyboard.append([
            InlineKeyboardButton("✅ Done", callback_data="media_done")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            settings_msg,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
        
        return MEDIA_SETTINGS
        
    except Exception as e:
        logger.error("media_callback_error", user_id=user_id, error=str(e))
        await query.edit_message_text(
            "❌ An error occurred. Please try again."
        )
        return ConversationHandler.END


# ============================================
# ADMIN COMMANDS
# ============================================

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command - show admin panel."""
    user_id = update.effective_user.id
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    
    if not admin_manager or not admin_manager.is_admin(user_id):
        await update.message.reply_text(
            "⛔ You don't have permission to use this command."
        )
        return
    
    admin_msg = (
        "🔐 **Admin Panel**\n\n"
        "**Broadcast Commands:**\n"
        "/broadcast - Send message to all users\n"
        "/broadcastactive - Send to active users only\n\n"
        "**Ban/Moderation Commands:**\n"
        "/ban - Ban a user (temporary/permanent)\n"
        "/unban - Unban a user\n"
        "/warn - Add warning to user\n"
        "/checkban - Check if user is banned\n"
        "/bannedlist - View all banned users\n"
        "/warninglist - View users on warning list\n\n"
        "**Media Blocking Commands:**\n"
        "/blockmedia - Block a media type\n"
        "/unblockmedia - Unblock a media type\n"
        "/blockedmedia - List blocked media types\n\n"
        "**Bad Word Filter Commands:**\n"
        "/addbadword - Add word/phrase to filter\n"
        "/removebadword - Remove word/phrase from filter\n"
        "/badwords - List all filtered words\n\n"
        "**Statistics:**\n"
        "/stats - View bot statistics\n\n"
        "Use these commands responsibly."
    )
    
    await update.message.reply_text(admin_msg, parse_mode="Markdown")


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /broadcast command - broadcast to all users."""
    user_id = update.effective_user.id
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    
    if not admin_manager or not admin_manager.is_admin(user_id):
        await update.message.reply_text(
            "⛔ You don't have permission to use this command."
        )
        return ConversationHandler.END
    
    # Store broadcast type in context
    context.user_data["broadcast_type"] = "all"
    
    await update.message.reply_text(
        "📢 **Broadcast to All Users**\n\n"
        "Send the message you want to broadcast.\n"
        "It will be sent to ALL users who have used the bot.\n\n"
        "Use /cancel to abort.",
        parse_mode="Markdown",
    )
    
    return BROADCAST_MESSAGE


async def broadcastactive_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /broadcastactive command - broadcast to active users only."""
    user_id = update.effective_user.id
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    
    if not admin_manager or not admin_manager.is_admin(user_id):
        await update.message.reply_text(
            "⛔ You don't have permission to use this command."
        )
        return ConversationHandler.END
    
    # Store broadcast type in context
    context.user_data["broadcast_type"] = "active"
    
    await update.message.reply_text(
        "📢 **Broadcast to Active Users**\n\n"
        "Send the message you want to broadcast.\n"
        "It will be sent to users currently in chat or queue.\n\n"
        "Use /cancel to abort.",
        parse_mode="Markdown",
    )
    
    return BROADCAST_MESSAGE


async def broadcast_message_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast message input."""
    user_id = update.effective_user.id
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    broadcast_type = context.user_data.get("broadcast_type", "all")
    
    if not admin_manager or not admin_manager.is_admin(user_id):
        await update.message.reply_text(
            "⛔ You don't have permission to use this command."
        )
        return ConversationHandler.END
    
    message_text = update.message.text
    
    # Show confirmation
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm Send", callback_data="broadcast_confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="broadcast_cancel"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Store message in context
    context.user_data["broadcast_message"] = message_text
    
    target = "ALL users" if broadcast_type == "all" else "ACTIVE users (in chat/queue)"
    
    await update.message.reply_text(
        f"📢 **Broadcast Preview**\n\n"
        f"Target: {target}\n\n"
        f"Message:\n{message_text}\n\n"
        f"Ready to send?",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    
    return BROADCAST_MESSAGE


async def broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast confirmation callback."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    callback_data = query.data
    
    if not admin_manager or not admin_manager.is_admin(user_id):
        await query.edit_message_text(
            "⛔ You don't have permission to use this command."
        )
        return ConversationHandler.END
    
    if callback_data == "broadcast_cancel":
        await query.edit_message_text(
            "❌ Broadcast cancelled."
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    elif callback_data == "broadcast_confirm":
        broadcast_type = context.user_data.get("broadcast_type", "all")
        message_text = context.user_data.get("broadcast_message", "")
        
        if not message_text:
            await query.edit_message_text(
                "❌ No message to broadcast."
            )
            return ConversationHandler.END
        
        await query.edit_message_text(
            "📤 Sending broadcast...\n"
            "This may take a few moments."
        )
        
        # Get target users
        if broadcast_type == "active":
            target_users = await admin_manager.get_active_users()
        else:
            target_users = await admin_manager.get_all_users()
        
        # Send broadcast
        success_count = 0
        failed_count = 0
        
        import asyncio
        
        for target_user_id in target_users:
            try:
                await context.bot.send_message(
                    target_user_id,
                    f"📢 **Admin Announcement**\n\n{message_text}",
                    parse_mode="Markdown",
                )
                success_count += 1
                
                # Small delay to avoid rate limits (30 messages per second limit)
                if success_count % 25 == 0:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                failed_count += 1
                logger.debug(
                    "broadcast_failed",
                    target_user_id=target_user_id,
                    error=str(e),
                )
        
        # Record broadcast
        await admin_manager.record_broadcast(
            admin_id=user_id,
            message=message_text,
            target_type=broadcast_type,
            success_count=success_count,
            failed_count=failed_count,
        )
        
        # Send summary
        await context.bot.send_message(
            user_id,
            f"✅ **Broadcast Complete**\n\n"
            f"Target: {broadcast_type.upper()}\n"
            f"✅ Sent: {success_count}\n"
            f"❌ Failed: {failed_count}\n"
            f"📊 Total: {len(target_users)}",
            parse_mode="Markdown",
        )
        
        context.user_data.clear()
        return ConversationHandler.END
    
    return BROADCAST_MESSAGE


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command - show bot statistics."""
    user_id = update.effective_user.id
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    
    if not admin_manager or not admin_manager.is_admin(user_id):
        await update.message.reply_text(
            "⛔ You don't have permission to use this command."
        )
        return
    
    try:
        # Get statistics
        all_users = await admin_manager.get_all_users()
        active_users = await admin_manager.get_active_users()
        
        stats_msg = (
            "📊 **Bot Statistics**\n\n"
            f"👥 Total Users: {len(all_users)}\n"
            f"🟢 Active Users: {len(active_users)}\n"
            f"⚪ Idle Users: {len(all_users) - len(active_users)}\n"
        )
        
        await update.message.reply_text(stats_msg, parse_mode="Markdown")
        
    except Exception as e:
        logger.error("stats_command_error", error=str(e))
        await update.message.reply_text(
            "❌ Failed to fetch statistics."
        )


async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel broadcast operation."""
    context.user_data.clear()
    await update.message.reply_text("❌ Broadcast cancelled.")
    return ConversationHandler.END


# ============================================
# BAN / UNBAN COMMANDS
# ============================================

BAN_REASONS = {
    "nudity": "Nudity / Explicit Content",
    "spam": "Spam",
    "abuse": "Abuse",
    "fake_reports": "Fake Reports",
    "harassment": "Harassment",
}


async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ban command - start ban process."""
    user_id = update.effective_user.id
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    
    if not admin_manager or not admin_manager.is_admin(user_id):
        await update.message.reply_text(
            "⛔ You don't have permission to use this command."
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "🚫 **Ban User**\n\n"
        "Send the user ID to ban.\n"
        "Use /cancel to abort.",
        parse_mode="Markdown",
    )
    
    return BAN_USER_ID


async def ban_user_id_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user ID input for ban."""
    try:
        user_id_to_ban = int(update.message.text.strip())
        context.user_data["ban_user_id"] = user_id_to_ban
        
        # Show ban reason selection
        keyboard = [
            [InlineKeyboardButton(f"📵 {BAN_REASONS['nudity']}", callback_data="ban_reason_nudity")],
            [InlineKeyboardButton(f"⚠️ {BAN_REASONS['spam']}", callback_data="ban_reason_spam")],
            [InlineKeyboardButton(f"🚨 {BAN_REASONS['abuse']}", callback_data="ban_reason_abuse")],
            [InlineKeyboardButton(f"❌ {BAN_REASONS['fake_reports']}", callback_data="ban_reason_fake_reports")],
            [InlineKeyboardButton(f"😡 {BAN_REASONS['harassment']}", callback_data="ban_reason_harassment")],
            [InlineKeyboardButton("❌ Cancel", callback_data="ban_cancel")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"User ID: `{user_id_to_ban}`\n\n"
            f"Select ban reason:",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
        
        return BAN_REASON
        
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid user ID. Please send a valid number.\n"
            "Use /cancel to abort."
        )
        return BAN_USER_ID


async def ban_reason_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ban reason selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "ban_cancel":
        await query.edit_message_text("❌ Ban operation cancelled.")
        context.user_data.clear()
        return ConversationHandler.END
    
    reason = query.data.replace("ban_reason_", "")
    context.user_data["ban_reason"] = reason
    
    user_id_to_ban = context.user_data.get("ban_user_id")
    
    # Show duration selection
    keyboard = [
        [InlineKeyboardButton("⏰ 1 Hour", callback_data="ban_duration_3600")],
        [InlineKeyboardButton("⏰ 24 Hours", callback_data="ban_duration_86400")],
        [InlineKeyboardButton("⏰ 7 Days", callback_data="ban_duration_604800")],
        [InlineKeyboardButton("⏰ 30 Days", callback_data="ban_duration_2592000")],
        [InlineKeyboardButton("🔒 Permanent", callback_data="ban_duration_permanent")],
        [InlineKeyboardButton("❌ Cancel", callback_data="ban_cancel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"User ID: `{user_id_to_ban}`\n"
        f"Reason: **{BAN_REASONS.get(reason, reason)}**\n\n"
        f"Select ban duration:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    
    return BAN_DURATION


async def ban_duration_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ban duration selection and execute ban."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    
    if query.data == "ban_cancel":
        await query.edit_message_text("❌ Ban operation cancelled.")
        context.user_data.clear()
        return ConversationHandler.END
    
    user_id_to_ban = context.user_data.get("ban_user_id")
    reason = context.user_data.get("ban_reason")
    
    # Parse duration
    if query.data == "ban_duration_permanent":
        duration = None
        duration_text = "Permanent"
    else:
        duration = int(query.data.replace("ban_duration_", ""))
        # Convert to human-readable
        if duration == 3600:
            duration_text = "1 Hour"
        elif duration == 86400:
            duration_text = "24 Hours"
        elif duration == 604800:
            duration_text = "7 Days"
        elif duration == 2592000:
            duration_text = "30 Days"
        else:
            duration_text = f"{duration} seconds"
    
    # Execute ban
    try:
        success = await admin_manager.ban_user(
            user_id=user_id_to_ban,
            banned_by=user_id,
            reason=reason,
            duration=duration,
            is_auto_ban=False,
        )
        
        if success:
            await query.edit_message_text(
                f"✅ **User Banned Successfully**\n\n"
                f"User ID: `{user_id_to_ban}`\n"
                f"Reason: **{BAN_REASONS.get(reason, reason)}**\n"
                f"Duration: **{duration_text}**\n"
                f"Banned by: Admin {user_id}",
                parse_mode="Markdown",
            )
            
            # Notify the banned user
            try:
                ban_message = (
                    f"🚫 **You have been banned**\n\n"
                    f"Reason: {BAN_REASONS.get(reason, reason)}\n"
                    f"Duration: {duration_text}\n\n"
                    f"If you believe this is a mistake, please contact support."
                )
                await context.bot.send_message(user_id_to_ban, ban_message, parse_mode="Markdown")
            except Exception as e:
                logger.warning("failed_to_notify_banned_user", user_id=user_id_to_ban, error=str(e))
        else:
            await query.edit_message_text(
                f"❌ Failed to ban user {user_id_to_ban}. Please try again."
            )
        
        context.user_data.clear()
        return ConversationHandler.END
        
    except Exception as e:
        logger.error("ban_execution_error", user_id=user_id_to_ban, error=str(e))
        await query.edit_message_text(
            f"❌ An error occurred while banning the user. Please try again."
        )
        context.user_data.clear()
        return ConversationHandler.END


async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unban command - start unban process."""
    user_id = update.effective_user.id
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    
    if not admin_manager or not admin_manager.is_admin(user_id):
        await update.message.reply_text(
            "⛔ You don't have permission to use this command."
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "✅ **Unban User**\n\n"
        "Send the user ID to unban.\n"
        "Use /cancel to abort.",
        parse_mode="Markdown",
    )
    
    return UNBAN_USER_ID


async def unban_user_id_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user ID input for unban."""
    user_id = update.effective_user.id
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    
    try:
        user_id_to_unban = int(update.message.text.strip())
        
        # Check if user is actually banned
        is_banned, ban_data = await admin_manager.is_user_banned(user_id_to_unban)
        
        if not is_banned:
            await update.message.reply_text(
                f"ℹ️ User `{user_id_to_unban}` is not currently banned.",
                parse_mode="Markdown",
            )
            return ConversationHandler.END
        
        # Execute unban
        success = await admin_manager.unban_user(user_id_to_unban, user_id)
        
        if success:
            await update.message.reply_text(
                f"✅ **User Unbanned Successfully**\n\n"
                f"User ID: `{user_id_to_unban}`\n"
                f"Unbanned by: Admin {user_id}",
                parse_mode="Markdown",
            )
            
            # Notify the unbanned user
            try:
                unban_message = (
                    f"✅ **Your ban has been lifted**\n\n"
                    f"You can now use the bot again.\n"
                    f"Please follow the rules to avoid future bans."
                )
                await context.bot.send_message(user_id_to_unban, unban_message, parse_mode="Markdown")
            except Exception as e:
                logger.warning("failed_to_notify_unbanned_user", user_id=user_id_to_unban, error=str(e))
        else:
            await update.message.reply_text(
                f"❌ Failed to unban user {user_id_to_unban}. Please try again."
            )
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid user ID. Please send a valid number.\n"
            "Use /cancel to abort."
        )
        return UNBAN_USER_ID
    except Exception as e:
        logger.error("unban_execution_error", error=str(e))
        await update.message.reply_text(
            f"❌ An error occurred. Please try again."
        )
        return ConversationHandler.END


async def warn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /warn command - add warning to user."""
    user_id = update.effective_user.id
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    
    if not admin_manager or not admin_manager.is_admin(user_id):
        await update.message.reply_text(
            "⛔ You don't have permission to use this command."
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "⚠️ **Add Warning**\n\n"
        "Send the user ID to warn.\n"
        "Use /cancel to abort.",
        parse_mode="Markdown",
    )
    
    return WARNING_USER_ID


async def warn_user_id_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user ID input for warning."""
    try:
        user_id_to_warn = int(update.message.text.strip())
        context.user_data["warn_user_id"] = user_id_to_warn
        
        await update.message.reply_text(
            f"User ID: `{user_id_to_warn}`\n\n"
            f"Send the warning reason:",
            parse_mode="Markdown",
        )
        
        return WARNING_REASON
        
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid user ID. Please send a valid number.\n"
            "Use /cancel to abort."
        )
        return WARNING_USER_ID


async def warn_reason_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle warning reason input."""
    user_id = update.effective_user.id
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    
    user_id_to_warn = context.user_data.get("warn_user_id")
    reason = update.message.text.strip()
    
    try:
        # Add warning
        warning_count = await admin_manager.add_warning(user_id_to_warn, user_id, reason)
        
        await update.message.reply_text(
            f"⚠️ **Warning Added Successfully**\n\n"
            f"User ID: `{user_id_to_warn}`\n"
            f"Reason: {reason}\n"
            f"Total Warnings: {warning_count}\n"
            f"Warned by: Admin {user_id}",
            parse_mode="Markdown",
        )
        
        # Notify the warned user
        try:
            warn_message = (
                f"⚠️ **You have received a warning**\n\n"
                f"Reason: {reason}\n"
                f"Total Warnings: {warning_count}\n\n"
                f"⚠️ Multiple warnings may result in a ban.\n"
                f"Please follow the rules to avoid further action."
            )
            await context.bot.send_message(user_id_to_warn, warn_message, parse_mode="Markdown")
        except Exception as e:
            logger.warning("failed_to_notify_warned_user", user_id=user_id_to_warn, error=str(e))
        
        context.user_data.clear()
        return ConversationHandler.END
        
    except Exception as e:
        logger.error("warn_execution_error", error=str(e))
        await update.message.reply_text(
            f"❌ An error occurred. Please try again."
        )
        context.user_data.clear()
        return ConversationHandler.END


async def checkban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /checkban command - check if user is banned."""
    user_id = update.effective_user.id
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    
    if not admin_manager or not admin_manager.is_admin(user_id):
        await update.message.reply_text(
            "⛔ You don't have permission to use this command."
        )
        return
    
    # Check if user ID was provided
    if not context.args or len(context.args) != 1:
        await update.message.reply_text(
            "❌ Usage: /checkban <user_id>\n"
            "Example: /checkban 123456789"
        )
        return
    
    try:
        user_id_to_check = int(context.args[0])
        
        is_banned, ban_data = await admin_manager.is_user_banned(user_id_to_check)
        
        if is_banned and ban_data:
            import time
            banned_at = ban_data.get("banned_at", 0)
            expires_at = ban_data.get("expires_at")
            reason = ban_data.get("reason", "Unknown")
            banned_by = ban_data.get("banned_by", 0)
            is_auto_ban = ban_data.get("is_auto_ban", False)
            
            # Format ban time
            from datetime import datetime
            ban_time = datetime.fromtimestamp(banned_at).strftime("%Y-%m-%d %H:%M:%S")
            
            if expires_at:
                expiry_time = datetime.fromtimestamp(expires_at).strftime("%Y-%m-%d %H:%M:%S")
                remaining = expires_at - int(time.time())
                if remaining > 86400:
                    remaining_text = f"{remaining // 86400} days"
                elif remaining > 3600:
                    remaining_text = f"{remaining // 3600} hours"
                else:
                    remaining_text = f"{remaining // 60} minutes"
                duration_text = f"Expires: {expiry_time}\nRemaining: {remaining_text}"
            else:
                duration_text = "Duration: Permanent"
            
            auto_ban_text = " (Auto-ban)" if is_auto_ban else ""
            
            message = (
                f"🚫 **User is BANNED{auto_ban_text}**\n\n"
                f"User ID: `{user_id_to_check}`\n"
                f"Reason: {BAN_REASONS.get(reason, reason)}\n"
                f"Banned at: {ban_time}\n"
                f"{duration_text}\n"
                f"Banned by: Admin {banned_by if banned_by > 0 else 'System'}"
            )
        else:
            # Check warnings
            warning_count = await admin_manager.get_warning_count(user_id_to_check)
            is_on_warning = await admin_manager.is_on_warning_list(user_id_to_check)
            
            message = f"✅ **User is NOT banned**\n\nUser ID: `{user_id_to_check}`"
            
            if is_on_warning or warning_count > 0:
                message += f"\n\n⚠️ Warnings: {warning_count}"
                if is_on_warning:
                    message += "\n🔶 On warning list"
        
        await update.message.reply_text(message, parse_mode="Markdown")
        
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid user ID. Please provide a valid number."
        )
    except Exception as e:
        logger.error("checkban_command_error", error=str(e))
        await update.message.reply_text(
            "❌ An error occurred while checking ban status."
        )


async def bannedlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /bannedlist command - show all banned users."""
    user_id = update.effective_user.id
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    
    if not admin_manager or not admin_manager.is_admin(user_id):
        await update.message.reply_text(
            "⛔ You don't have permission to use this command."
        )
        return
    
    try:
        banned_users = await admin_manager.get_banned_users_list()
        
        if not banned_users:
            await update.message.reply_text(
                "✅ No users are currently banned."
            )
            return
        
        message = f"🚫 **Banned Users** ({len(banned_users)} total)\n\n"
        
        # Show first 20 banned users with details
        for i, banned_user_id in enumerate(banned_users[:20]):
            ban_data = await admin_manager.get_ban_info(banned_user_id)
            if ban_data:
                reason = ban_data.get("reason", "Unknown")
                is_permanent = ban_data.get("is_permanent", False)
                is_auto_ban = ban_data.get("is_auto_ban", False)
                
                duration = "Permanent" if is_permanent else "Temporary"
                auto_text = " (Auto)" if is_auto_ban else ""
                
                message += f"{i+1}. `{banned_user_id}` - {BAN_REASONS.get(reason, reason)} ({duration}{auto_text})\n"
        
        if len(banned_users) > 20:
            message += f"\n... and {len(banned_users) - 20} more"
        
        await update.message.reply_text(message, parse_mode="Markdown")
        
    except Exception as e:
        logger.error("bannedlist_command_error", error=str(e))
        await update.message.reply_text(
            "❌ An error occurred while fetching banned users list."
        )


async def warninglist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /warninglist command - show users on warning list."""
    user_id = update.effective_user.id
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    
    if not admin_manager or not admin_manager.is_admin(user_id):
        await update.message.reply_text(
            "⛔ You don't have permission to use this command."
        )
        return
    
    try:
        warning_users = await admin_manager.get_warning_list()
        
        if not warning_users:
            await update.message.reply_text(
                "✅ No users are currently on the warning list."
            )
            return
        
        message = f"⚠️ **Warning List** ({len(warning_users)} total)\n\n"
        
        # Show first 20 users with warning counts
        for i, warned_user_id in enumerate(warning_users[:20]):
            warning_count = await admin_manager.get_warning_count(warned_user_id)
            message += f"{i+1}. `{warned_user_id}` - {warning_count} warning(s)\n"
        
        if len(warning_users) > 20:
            message += f"\n... and {len(warning_users) - 20} more"
        
        await update.message.reply_text(message, parse_mode="Markdown")
        
    except Exception as e:
        logger.error("warninglist_command_error", error=str(e))
        await update.message.reply_text(
            "❌ An error occurred while fetching warning list."
        )


async def cancel_ban_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel ban/unban/warn operation."""
    context.user_data.clear()
    await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END


async def blockmedia_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /blockmedia command - block a media type."""
    user_id = update.effective_user.id
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    
    if not admin_manager or not admin_manager.is_admin(user_id):
        await update.message.reply_text(
            "⛔ You don't have permission to use this command."
        )
        return
    
    # Check if arguments provided
    args = context.args
    if len(args) < 1:
        help_msg = (
            "🚫 **Block Media Type**\n\n"
            "**Usage:**\n"
            "`/blockmedia <type> [duration] [reason]`\n\n"
            "**Media Types:**\n"
            "• `photo` - Block photos/images\n"
            "• `video` - Block videos\n"
            "• `voice` - Block voice messages\n"
            "• `audio` - Block audio files\n"
            "• `document` - Block documents\n"
            "• `sticker` - Block stickers\n"
            "• `video_note` - Block video notes\n"
            "• `location` - Block location sharing\n\n"
            "**Duration (optional):**\n"
            "• `1h` - 1 hour\n"
            "• `6h` - 6 hours\n"
            "• `24h` - 24 hours\n"
            "• `7d` - 7 days\n"
            "• `permanent` - Permanent (default)\n\n"
            "**Examples:**\n"
            "`/blockmedia photo 1h Inappropriate content`\n"
            "`/blockmedia video permanent Adult content`\n"
            "`/blockmedia sticker 24h Spam`"
        )
        await update.message.reply_text(help_msg, parse_mode="Markdown")
        return
    
    media_type = args[0].lower()
    valid_types = ["photo", "video", "voice", "audio", "document", "sticker", "video_note", "location"]
    
    if media_type not in valid_types:
        await update.message.reply_text(
            f"❌ Invalid media type: `{media_type}`\n\n"
            f"Valid types: {', '.join(valid_types)}",
            parse_mode="Markdown"
        )
        return
    
    # Parse duration
    duration_str = "permanent"
    reason = "Content moderation"
    
    if len(args) >= 2:
        duration_str = args[1].lower()
        if duration_str not in ["1h", "6h", "24h", "7d", "30d", "permanent"]:
            # If not a valid duration, treat as reason
            reason = " ".join(args[1:])
            duration_str = "permanent"
        elif len(args) >= 3:
            reason = " ".join(args[2:])
    
    # Convert duration to seconds
    duration_map = {
        "1h": 3600,
        "6h": 21600,
        "24h": 86400,
        "7d": 604800,
        "30d": 2592000,
        "permanent": None
    }
    duration_seconds = duration_map.get(duration_str)
    
    # Block the media type
    report_manager = context.bot_data.get("report_manager")
    if not report_manager:
        await update.message.reply_text("❌ Report manager not available.")
        return
    
    try:
        success = await report_manager.block_media_type(
            media_type=media_type,
            duration=duration_seconds,
            reason=reason
        )
        
        if success:
            duration_text = "permanently" if duration_str == "permanent" else f"for {duration_str}"
            await update.message.reply_text(
                f"✅ **Media type blocked successfully**\n\n"
                f"📸 Type: `{media_type}`\n"
                f"⏱ Duration: {duration_text}\n"
                f"📝 Reason: {reason}\n\n"
                f"Users will now be blocked from sending {media_type}.",
                parse_mode="Markdown"
            )
            
            # Log the action
            await report_manager.log_moderation_action(
                admin_id=user_id,
                action="media_blocked",
                details=f"Blocked {media_type}: {reason} (Duration: {duration_str})"
            )
        else:
            await update.message.reply_text("❌ Failed to block media type.")
    except Exception as e:
        logger.error("blockmedia_command_error", error=str(e))
        await update.message.reply_text("❌ An error occurred while blocking media type.")


async def unblockmedia_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unblockmedia command - unblock a media type."""
    user_id = update.effective_user.id
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    
    if not admin_manager or not admin_manager.is_admin(user_id):
        await update.message.reply_text(
            "⛔ You don't have permission to use this command."
        )
        return
    
    # Check if arguments provided
    args = context.args
    if len(args) < 1:
        help_msg = (
            "✅ **Unblock Media Type**\n\n"
            "**Usage:**\n"
            "`/unblockmedia <type>`\n\n"
            "**Media Types:**\n"
            "• `photo` - Unblock photos/images\n"
            "• `video` - Unblock videos\n"
            "• `voice` - Unblock voice messages\n"
            "• `audio` - Unblock audio files\n"
            "• `document` - Unblock documents\n"
            "• `sticker` - Unblock stickers\n"
            "• `video_note` - Unblock video notes\n"
            "• `location` - Unblock location sharing\n\n"
            "**Examples:**\n"
            "`/unblockmedia photo`\n"
            "`/unblockmedia video`"
        )
        await update.message.reply_text(help_msg, parse_mode="Markdown")
        return
    
    media_type = args[0].lower()
    valid_types = ["photo", "video", "voice", "audio", "document", "sticker", "video_note", "location"]
    
    if media_type not in valid_types:
        await update.message.reply_text(
            f"❌ Invalid media type: `{media_type}`\n\n"
            f"Valid types: {', '.join(valid_types)}",
            parse_mode="Markdown"
        )
        return
    
    # Unblock the media type
    report_manager = context.bot_data.get("report_manager")
    if not report_manager:
        await update.message.reply_text("❌ Report manager not available.")
        return
    
    try:
        success = await report_manager.unblock_media_type(media_type)
        
        if success:
            await update.message.reply_text(
                f"✅ **Media type unblocked successfully**\n\n"
                f"📸 Type: `{media_type}`\n\n"
                f"Users can now send {media_type} again.",
                parse_mode="Markdown"
            )
            
            # Log the action
            await report_manager.log_moderation_action(
                admin_id=user_id,
                action="media_unblocked",
                details=f"Unblocked {media_type}"
            )
        else:
            await update.message.reply_text("❌ Failed to unblock media type.")
    except Exception as e:
        logger.error("unblockmedia_command_error", error=str(e))
        await update.message.reply_text("❌ An error occurred while unblocking media type.")


async def blockedmedia_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /blockedmedia command - list all blocked media types."""
    user_id = update.effective_user.id
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    
    if not admin_manager or not admin_manager.is_admin(user_id):
        await update.message.reply_text(
            "⛔ You don't have permission to use this command."
        )
        return
    
    report_manager = context.bot_data.get("report_manager")
    if not report_manager:
        await update.message.reply_text("❌ Report manager not available.")
        return
    
    try:
        blocked_media = await report_manager.get_blocked_media_types()
        
        if not blocked_media:
            await update.message.reply_text(
                "✅ No media types are currently blocked.\n\n"
                "All media types are allowed."
            )
            return
        
        from datetime import datetime
        
        message = f"🚫 **Blocked Media Types** ({len(blocked_media)} total)\n\n"
        
        for media in blocked_media:
            media_type = media.get("media_type", "unknown")
            reason = media.get("reason", "No reason")
            blocked_at = datetime.fromtimestamp(media.get("blocked_at", 0)).strftime("%Y-%m-%d %H:%M")
            
            if media.get("expires_at"):
                expires_at = datetime.fromtimestamp(media["expires_at"]).strftime("%Y-%m-%d %H:%M")
                duration_sec = media["expires_at"] - media.get("blocked_at", 0)
                
                if duration_sec == 3600:
                    duration = "1 hour"
                elif duration_sec == 21600:
                    duration = "6 hours"
                elif duration_sec == 86400:
                    duration = "24 hours"
                elif duration_sec == 604800:
                    duration = "7 days"
                elif duration_sec == 2592000:
                    duration = "30 days"
                else:
                    duration = f"{duration_sec // 3600} hours"
                
                message += f"📸 **{media_type}**\n"
                message += f"   Duration: {duration}\n"
                message += f"   Expires: {expires_at}\n"
                message += f"   Reason: {reason}\n\n"
            else:
                message += f"📸 **{media_type}**\n"
                message += f"   Duration: Permanent\n"
                message += f"   Blocked: {blocked_at}\n"
                message += f"   Reason: {reason}\n\n"
        
        message += "\nUse `/unblockmedia <type>` to unblock."
        
        await update.message.reply_text(message, parse_mode="Markdown")
        
    except Exception as e:
        logger.error("blockedmedia_command_error", error=str(e))
        await update.message.reply_text("❌ An error occurred while fetching blocked media types.")


async def addbadword_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addbadword command - add a word/phrase to bad word filter."""
    user_id = update.effective_user.id
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    
    if not admin_manager or not admin_manager.is_admin(user_id):
        await update.message.reply_text(
            "⛔ You don't have permission to use this command."
        )
        return
    
    # Check if arguments provided
    args = context.args
    if len(args) < 1:
        help_msg = (
            "🚫 **Add Bad Word/Phrase to Filter**\n\n"
            "**Usage:**\n"
            "`/addbadword <word or phrase>`\n\n"
            "**Examples:**\n"
            "`/addbadword spam`\n"
            "`/addbadword inappropriate phrase`\n"
            "`/addbadword badword123`\n\n"
            "**Note:**\n"
            "• Not case-sensitive (matches any case)\n"
            "• Can be a single word or multiple words\n"
            "• Messages containing this will be blocked"
        )
        await update.message.reply_text(help_msg, parse_mode="Markdown")
        return
    
    # Join all args to support multi-word phrases
    word = " ".join(args).lower().strip()
    
    if not word:
        await update.message.reply_text("❌ Please provide a valid word or phrase.")
        return
    
    # Add the bad word
    report_manager = context.bot_data.get("report_manager")
    if not report_manager:
        await update.message.reply_text("❌ Report manager not available.")
        return
    
    try:
        success = await report_manager.add_bad_word(word, user_id)
        
        if success:
            await update.message.reply_text(
                f"✅ **Bad word/phrase added successfully**\n\n"
                f"🚫 Filtered: `{word}`\n\n"
                f"Users sending messages with this word/phrase will be:\n"
                f"• Blocked from sending the message\n"
                f"• Given a warning\n"
                f"• Logged for moderation",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Failed to add bad word/phrase.")
    except Exception as e:
        logger.error("addbadword_command_error", error=str(e))
        await update.message.reply_text("❌ An error occurred while adding bad word/phrase.")


async def removebadword_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /removebadword command - remove a word/phrase from bad word filter."""
    user_id = update.effective_user.id
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    
    if not admin_manager or not admin_manager.is_admin(user_id):
        await update.message.reply_text(
            "⛔ You don't have permission to use this command."
        )
        return
    
    # Check if arguments provided
    args = context.args
    if len(args) < 1:
        help_msg = (
            "✅ **Remove Bad Word/Phrase from Filter**\n\n"
            "**Usage:**\n"
            "`/removebadword <word or phrase>`\n\n"
            "**Examples:**\n"
            "`/removebadword spam`\n"
            "`/removebadword inappropriate phrase`\n\n"
            "Use `/badwords` to see all filtered words."
        )
        await update.message.reply_text(help_msg, parse_mode="Markdown")
        return
    
    # Join all args to support multi-word phrases
    word = " ".join(args).lower().strip()
    
    if not word:
        await update.message.reply_text("❌ Please provide a valid word or phrase.")
        return
    
    # Remove the bad word
    report_manager = context.bot_data.get("report_manager")
    if not report_manager:
        await update.message.reply_text("❌ Report manager not available.")
        return
    
    try:
        success = await report_manager.remove_bad_word(word, user_id)
        
        if success:
            await update.message.reply_text(
                f"✅ **Bad word/phrase removed successfully**\n\n"
                f"🔓 Unfiltered: `{word}`\n\n"
                f"This word/phrase is no longer blocked.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"❌ Word/phrase not found in filter.\n\n"
                f"Use `/badwords` to see all filtered words."
            )
    except Exception as e:
        logger.error("removebadword_command_error", error=str(e))
        await update.message.reply_text("❌ An error occurred while removing bad word/phrase.")


async def badwords_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /badwords command - list all bad words in filter."""
    user_id = update.effective_user.id
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    
    if not admin_manager or not admin_manager.is_admin(user_id):
        await update.message.reply_text(
            "⛔ You don't have permission to use this command."
        )
        return
    
    report_manager = context.bot_data.get("report_manager")
    if not report_manager:
        await update.message.reply_text("❌ Report manager not available.")
        return
    
    try:
        bad_words = await report_manager.get_bad_words()
        
        if not bad_words:
            await update.message.reply_text(
                "✅ No bad words/phrases are currently filtered.\n\n"
                "Use `/addbadword <word>` to add one."
            )
            return
        
        # Sort words alphabetically
        bad_words = sorted(bad_words)
        
        message = f"🚫 **Bad Word Filter** ({len(bad_words)} total)\n\n"
        
        # Group by first letter for better organization
        current_letter = ""
        for word in bad_words:
            first_letter = word[0].upper() if word else "?"
            if first_letter != current_letter:
                current_letter = first_letter
                message += f"\n**{current_letter}**\n"
            message += f"• `{word}`\n"
        
        message += f"\n**Commands:**\n"
        message += f"• `/addbadword <word>` - Add new word\n"
        message += f"• `/removebadword <word>` - Remove word"
        
        await update.message.reply_text(message, parse_mode="Markdown")
        
    except Exception as e:
        logger.error("badwords_command_error", error=str(e))
        await update.message.reply_text("❌ An error occurred while fetching bad words list.")


