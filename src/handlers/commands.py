"""Command handlers for the bot."""
from telegram import Update
from telegram.ext import ContextTypes
from src.services.matching import MatchingEngine
from src.services.queue import QueueFullError
from src.utils.decorators import rate_limit
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    
    welcome_message = (
        f"👋 Welcome to Anonymous Random Chat, {user.first_name}!\n\n"
        "🎭 Connect with random strangers anonymously.\n"
        "💬 Chat with anyone from around the world.\n\n"
        "📋 **Commands:**\n"
        "/chat - Start searching for a partner\n"
        "/stop - End current chat\n"
        "/next - Skip to next partner\n"
        "/help - Show help message\n\n"
        "🔒 Your identity remains completely anonymous.\n"
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
        "1️⃣ Use /chat to enter the waiting queue\n"
        "2️⃣ Once matched, start chatting with your partner\n"
        "3️⃣ Send text, photos, videos, stickers, voice notes\n"
        "4️⃣ Use /next to skip to a new partner\n"
        "5️⃣ Use /stop to end the chat\n\n"
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
            await update.message.reply_text(
                "✅ **Partner found!**\n\n"
                "👋 Say hi and start chatting!\n"
                "Use /next to skip or /stop to end.",
                parse_mode="Markdown",
            )
            
            # Notify partner
            await context.bot.send_message(
                partner_id,
                "✅ **Partner found!**\n\n"
                "👋 Say hi and start chatting!\n"
                "Use /next to skip or /stop to end.",
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
            await update.message.reply_text(
                "✅ **New partner found!**\n\n"
                "👋 Say hi and start chatting!",
                parse_mode="Markdown",
            )
            
            await context.bot.send_message(
                new_partner_id,
                "✅ **Partner found!**\n\n"
                "👋 Say hi and start chatting!",
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
