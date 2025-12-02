"""Message routing handlers."""
import asyncio
import json
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError, Forbidden, BadRequest
from telegram.constants import ChatAction
from src.services.matching import MatchingEngine
from src.services.activity import ActivityManager
from src.services.media_preferences import MediaPreferenceManager
from src.services.admin import AdminManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route messages between chat partners with typing indicators and media filtering."""
    if not update.message:
        return
    
    sender_id = update.effective_user.id
    matching: MatchingEngine = context.bot_data["matching"]
    activity_manager: ActivityManager = context.bot_data.get("activity_manager")
    media_manager: MediaPreferenceManager = context.bot_data.get("media_manager")
    admin_manager: AdminManager = context.bot_data.get("admin_manager")
    report_manager = context.bot_data.get("report_manager")
    
    # Check if user is banned
    if admin_manager:
        is_banned, ban_data = await admin_manager.is_user_banned(sender_id)
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
                    f"If you believe this is a mistake, please contact support."
                )
            else:
                ban_msg = (
                    f"🚫 **You are permanently banned**\n\n"
                    f"Reason: {ban_reasons_map.get(reason, reason)}\n\n"
                    f"If you believe this is a mistake, please contact support."
                )
            
            await update.message.reply_text(ban_msg, parse_mode="Markdown")
            return
    
    # Store user info for dashboard
    if admin_manager:
        try:
            user = update.effective_user
            await admin_manager.register_user(
                user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                language_code=user.language_code,
                is_bot=user.is_bot,
                is_premium=user.is_premium
            )
            # Increment message count
            await admin_manager.increment_message_count(user.id)
        except Exception as e:
            logger.debug("user_info_storage_failed", user_id=sender_id, error=str(e))
    
    try:
        # Update last activity timestamp for both users
        redis_client = context.bot_data.get("redis")
        if redis_client:
            import time
            current_time = int(time.time())
            await redis_client.set(f"chat:activity:{sender_id}", current_time, ex=7200)  # 2 hour expiry
        
        # Mark sender as typing (for the partner to see)
        if activity_manager:
            await activity_manager.set_typing(sender_id)
        
        # Get partner
        partner_id = await matching.get_partner(sender_id)
        
        if not partner_id:
            await update.message.reply_text(
                "❌ You're not in a chat.\n"
                "Use /chat to find a partner!"
            )
            return
        
        # Update partner's activity timestamp as well (they're receiving a message)
        if redis_client:
            current_time = int(time.time())
            await redis_client.set(f"chat:activity:{partner_id}", current_time, ex=7200)
        
        # Determine message type
        media_type = None
        if update.message.photo:
            media_type = "photo"
        elif update.message.video:
            media_type = "video"
        elif update.message.voice:
            media_type = "voice"
        elif update.message.audio:
            media_type = "audio"
        elif update.message.document:
            media_type = "document"
        elif update.message.sticker:
            media_type = "sticker"
        elif update.message.video_note:
            media_type = "video_note"
        elif update.message.location:
            media_type = "location"
        
        # Check if media type is globally blocked by admin
        if media_type and report_manager:
            is_blocked = await report_manager.is_media_blocked(media_type)
            if is_blocked:
                media_names = {
                    "photo": "Photos",
                    "video": "Videos",
                    "voice": "Voice messages",
                    "audio": "Audio files",
                    "document": "Documents",
                    "sticker": "Stickers",
                    "video_note": "Video notes",
                    "location": "Locations"
                }
                media_name = media_names.get(media_type, media_type.title())
                await update.message.reply_text(
                    f"🚫 **{media_name} are currently blocked**\n\n"
                    f"The admin has temporarily disabled {media_name.lower()} on this platform.\n\n"
                    "💡 Try sending a text message instead!",
                    parse_mode="Markdown",
                )
                return
        
        # Check if partner allows this media type
        if media_type and media_manager:
            is_allowed, reason = await media_manager.is_media_allowed(partner_id, media_type)
            
            if not is_allowed:
                await update.message.reply_text(
                    f"❌ **Message not sent**\n\n"
                    f"{reason}\n\n"
                    "💡 Try sending a text message instead!",
                    parse_mode="Markdown",
                )
                return
        
        # Check for bad words in text messages and captions
        if report_manager:
            text_to_check = None
            if update.message.text:
                text_to_check = update.message.text
            elif update.message.caption:
                text_to_check = update.message.caption
            
            if text_to_check:
                contains_bad_word = await report_manager.contains_bad_word(text_to_check)
                if contains_bad_word:
                    # Get bad words list to show which words are filtered
                    bad_words = await report_manager.get_bad_words()
                    filtered_words = [word for word in bad_words if word in text_to_check.lower()]
                    
                    await update.message.reply_text(
                        "⚠️ **Message Blocked - Inappropriate Content**\n\n"
                        "Your message contains words or phrases that violate our community guidelines.\n\n"
                        "🚫 **Detected:** " + ", ".join(f"`{word}`" for word in filtered_words[:3]) + "\n\n"
                        "⚡ **Warning:** Repeated violations may result in:\n"
                        "• Temporary restrictions\n"
                        "• Account warnings\n"
                        "• Permanent ban\n\n"
                        "💡 Please communicate respectfully and follow our rules.",
                        parse_mode="Markdown"
                    )
                    
                    # Increment warning count
                    if admin_manager:
                        await admin_manager.add_warning(
                            user_id=sender_id,
                            warned_by=0,  # System warning
                            reason="Bad word usage"
                        )
                    
                    # Log the violation
                    logger.warning(
                        "bad_word_detected",
                        user_id=sender_id,
                        words=filtered_words,
                        message_preview=text_to_check[:50]
                    )
                    return
        
        # Show typing indicator to partner
        try:
            await context.bot.send_chat_action(
                chat_id=partner_id,
                action=ChatAction.TYPING,
            )
            # Small delay to make typing indicator visible
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.debug("typing_indicator_failed", partner_id=partner_id, error=str(e))
        
        # Route message based on type
        try:
            if update.message.text:
                await context.bot.send_message(
                    partner_id,
                    update.message.text,
                    entities=update.message.entities,
                    protect_content=True,  # Disable forwarding and saving
                )
            elif update.message.photo:
                # Show upload photo action
                try:
                    await context.bot.send_chat_action(
                        chat_id=partner_id,
                        action=ChatAction.UPLOAD_PHOTO,
                    )
                    await asyncio.sleep(0.3)
                except Exception:
                    pass
                
                # Send the highest resolution photo
                photo = update.message.photo[-1]
                await context.bot.send_photo(
                    partner_id,
                    photo.file_id,
                    caption=update.message.caption,
                    caption_entities=update.message.caption_entities,
                    protect_content=True,  # Disable forwarding and saving
                )
            elif update.message.video:
                # Show upload video action
                try:
                    await context.bot.send_chat_action(
                        chat_id=partner_id,
                        action=ChatAction.UPLOAD_VIDEO,
                    )
                    await asyncio.sleep(0.3)
                except Exception:
                    pass
                
                await context.bot.send_video(
                    partner_id,
                    update.message.video.file_id,
                    caption=update.message.caption,
                    caption_entities=update.message.caption_entities,
                    protect_content=True,  # Disable forwarding and saving
                )
            elif update.message.voice:
                # Show upload voice action
                try:
                    await context.bot.send_chat_action(
                        chat_id=partner_id,
                        action=ChatAction.UPLOAD_VOICE,
                    )
                    await asyncio.sleep(0.3)
                except Exception:
                    pass
                
                await context.bot.send_voice(
                    partner_id,
                    update.message.voice.file_id,
                    caption=update.message.caption,
                    protect_content=True,  # Disable forwarding and saving
                )
            elif update.message.audio:
                # Show upload audio action
                try:
                    await context.bot.send_chat_action(
                        chat_id=partner_id,
                        action=ChatAction.UPLOAD_AUDIO,
                    )
                    await asyncio.sleep(0.3)
                except Exception:
                    pass
                
                await context.bot.send_audio(
                    partner_id,
                    update.message.audio.file_id,
                    caption=update.message.caption,
                    caption_entities=update.message.caption_entities,
                    protect_content=True,  # Disable forwarding and saving
                )
            elif update.message.document:
                # Show upload document action
                try:
                    await context.bot.send_chat_action(
                        chat_id=partner_id,
                        action=ChatAction.UPLOAD_DOCUMENT,
                    )
                    await asyncio.sleep(0.3)
                except Exception:
                    pass
                
                await context.bot.send_document(
                    partner_id,
                    update.message.document.file_id,
                    caption=update.message.caption,
                    caption_entities=update.message.caption_entities,
                    protect_content=True,  # Disable forwarding and saving
                )
            elif update.message.sticker:
                await context.bot.send_sticker(
                    partner_id,
                    update.message.sticker.file_id,
                    protect_content=True,  # Disable forwarding and saving
                )
            elif update.message.video_note:
                # Show upload video note action
                try:
                    await context.bot.send_chat_action(
                        chat_id=partner_id,
                        action=ChatAction.UPLOAD_VIDEO_NOTE,
                    )
                    await asyncio.sleep(0.3)
                except Exception:
                    pass
                
                await context.bot.send_video_note(
                    partner_id,
                    update.message.video_note.file_id,
                    protect_content=True,  # Disable forwarding and saving
                )
            elif update.message.animation:
                await context.bot.send_animation(
                    partner_id,
                    update.message.animation.file_id,
                    caption=update.message.caption,
                    caption_entities=update.message.caption_entities,
                    protect_content=True,  # Disable forwarding and saving
                )
            elif update.message.location:
                # Show find location action
                try:
                    await context.bot.send_chat_action(
                        chat_id=partner_id,
                        action=ChatAction.FIND_LOCATION,
                    )
                    await asyncio.sleep(0.3)
                except Exception:
                    pass
                
                await context.bot.send_location(
                    partner_id,
                    latitude=update.message.location.latitude,
                    longitude=update.message.location.longitude,
                    protect_content=True,  # Disable forwarding and saving
                )
            elif update.message.contact:
                await context.bot.send_contact(
                    partner_id,
                    phone_number=update.message.contact.phone_number,
                    first_name=update.message.contact.first_name,
                    last_name=update.message.contact.last_name,
                    protect_content=True,  # Disable forwarding and saving
                )
            else:
                # Fallback: try to copy the message
                await update.message.copy(chat_id=partner_id)
            
            logger.debug(
                "message_routed",
                sender_id=sender_id,
                partner_id=partner_id,
                message_type=update.message.effective_attachment.__class__.__name__ 
                    if update.message.effective_attachment else "text",
            )
        
        except Forbidden:
            # Partner blocked the bot
            logger.warning(
                "partner_blocked_bot",
                sender_id=sender_id,
                partner_id=partner_id,
            )
            
            # End the chat
            await matching.end_chat(sender_id)
            
            await update.message.reply_text(
                "⚠️ Your partner has blocked the bot.\n"
                "Chat ended. Use /chat to find a new partner."
            )
        
        except BadRequest as e:
            logger.error(
                "message_routing_bad_request",
                sender_id=sender_id,
                partner_id=partner_id,
                error=str(e),
            )
            
            await update.message.reply_text(
                "❌ Failed to send message. Please try again."
            )
        
        except TelegramError as e:
            logger.error(
                "message_routing_telegram_error",
                sender_id=sender_id,
                partner_id=partner_id,
                error=str(e),
            )
            
            await update.message.reply_text(
                "❌ Failed to send message. Please try again."
            )
    
    except Exception as e:
        logger.error(
            "message_handling_error",
            sender_id=sender_id,
            error=str(e),
        )
        
        await update.message.reply_text(
            "❌ An error occurred. Please try /stop and start again."
        )


async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in handlers."""
    logger.error(
        "unhandled_error",
        error=str(context.error),
        update=update,
    )
    
    # Notify user if possible
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ An unexpected error occurred.\n"
                "Please try again or use /help for assistance."
            )
        except Exception:
            pass
