"""Message routing handlers."""
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError, Forbidden, BadRequest
from telegram.constants import ChatAction
from src.services.matching import MatchingEngine
from src.services.activity import ActivityManager
from src.services.media_preferences import MediaPreferenceManager
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
    
    try:
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
                )
            elif update.message.sticker:
                await context.bot.send_sticker(
                    partner_id,
                    update.message.sticker.file_id,
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
                )
            elif update.message.animation:
                await context.bot.send_animation(
                    partner_id,
                    update.message.animation.file_id,
                    caption=update.message.caption,
                    caption_entities=update.message.caption_entities,
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
                )
            elif update.message.contact:
                await context.bot.send_contact(
                    partner_id,
                    phone_number=update.message.contact.phone_number,
                    first_name=update.message.contact.first_name,
                    last_name=update.message.contact.last_name,
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
