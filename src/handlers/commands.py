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
from src.utils.decorators import rate_limit
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Conversation states for profile editing
NICKNAME, GENDER, COUNTRY = range(3)


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
        "/chat - Start searching for a partner\n"
        "/stop - End current chat\n"
        "/next - Skip to next partner\n"
        "/help - Show help message\n\n"
        "🔒 Your identity remains completely anonymous.\n"
        "💡 Create your profile first with /editprofile!\n"
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
        "2️⃣ Use /chat to enter the waiting queue\n"
        "3️⃣ Once matched, start chatting with your partner\n"
        "4️⃣ Send text, photos, videos, stickers, voice notes\n"
        "5️⃣ Use /next to skip to a new partner\n"
        "6️⃣ Use /stop to end the chat\n\n"
        "📋 **All Commands:**\n"
        "/profile - View your profile\n"
        "/editprofile - Edit your profile\n"
        "/chat - Find a partner\n"
        "/stop - End chat\n"
        "/next - Skip to next\n"
        "/help - Show this message\n"
        "/report - Report abuse\n\n"
        "⚠️ **Rules:**\n"
        "• Be respectful and kind\n"
        "• No spam or abuse\n"
        "• Report issues with /report\n\n"
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
        
        # Try to find a partner
        await update.message.reply_text(
            "🔍 Looking for a partner..."
        )
        
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
                match_msg += f"🌍 {partner_profile.country}\n\n"
            match_msg += "👋 Say hi and start chatting!\n"
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
                partner_match_msg += f"🌍 {user_profile.country}\n\n"
            partner_match_msg += "👋 Say hi and start chatting!\n"
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
        logger.error(
            "chat_command_error",
            user_id=user_id,
            error=str(e),
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
            
            # Notify partner
            try:
                await context.bot.send_message(
                    partner_id,
                    "⚠️ **Partner has left the chat.**\n\n"
                    "Use /chat to find a new partner!",
                    parse_mode="Markdown",
                )
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
        
        # Notify previous partner
        try:
            await context.bot.send_message(
                partner_id,
                "⚠️ **Partner skipped to next chat.**\n\n"
                "Use /chat to find a new partner!",
                parse_mode="Markdown",
            )
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
            
            # Get partner's profile
            partner_profile = None
            user_profile = None
            if profile_manager:
                partner_profile = await profile_manager.get_profile(new_partner_id)
                user_profile = await profile_manager.get_profile(user_id)
            
            # Send match notification to user with partner's profile
            match_msg = "✅ **New partner found!**\n\n"
            if partner_profile:
                match_msg += f"👤 **Partner's Profile:**\n"
                match_msg += f"📝 {partner_profile.nickname}\n"
                match_msg += f"{'👨' if partner_profile.gender == 'Male' else '👩' if partner_profile.gender == 'Female' else '🧑'} {partner_profile.gender}\n"
                match_msg += f"🌍 {partner_profile.country}\n\n"
            match_msg += "👋 Say hi and start chatting!"
            
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
                partner_match_msg += f"🌍 {user_profile.country}\n\n"
            partner_match_msg += "👋 Say hi and start chatting!"
            
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
