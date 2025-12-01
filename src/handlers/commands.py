"""Command handlers for the bot."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
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
from src.utils.decorators import rate_limit
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Conversation states for profile editing
NICKNAME, GENDER, COUNTRY = range(3)

# Conversation states for preferences
PREF_GENDER, PREF_COUNTRY = range(3, 5)

# Conversation states for media settings
MEDIA_SETTINGS = 5


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    
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
    
    try:
        # End current chat
        partner_id = await matching.end_chat(user_id)
        
        if not partner_id:
            await update.message.reply_text(
                "❌ You're not in a chat.\n"
                "Use /chat to find a partner!"
            )
            return
        
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
    await update.message.reply_text(
        "⚠️ **Report Abuse**\n\n"
        "To report your chat partner:\n"
        "1. Use /stop to end the chat\n"
        "2. Contact @YourSupportUsername with details\n\n"
        "We take reports seriously and will investigate."
    )
    
    logger.info(
        "report_command",
        user_id=update.effective_user.id,
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


