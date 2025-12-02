"""Admin Dashboard - Web-based interface for bot administration."""
import asyncio
from datetime import datetime
from typing import Optional
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from telegram import Bot
from src.config import Config
from src.db.redis_client import RedisClient
from src.services.dashboard import DashboardService
from src.services.admin import AdminManager
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Ban reasons mapping
BAN_REASONS = {
    "nudity": "Nudity / Explicit Content",
    "spam": "Spam",
    "abuse": "Abuse",
    "fake_reports": "Fake Reports",
    "harassment": "Harassment",
}

app = Flask(__name__)
CORS(app)

# Global instances
redis_client = None
dashboard_service = None
admin_manager = None
event_loop = None
bot = None  # Telegram bot instance for sending notifications


async def init_services():
    """Initialize Redis and dashboard services."""
    global redis_client, dashboard_service, admin_manager, bot
    
    redis_client = RedisClient()
    await redis_client.connect()
    dashboard_service = DashboardService(redis_client)
    admin_manager = AdminManager(redis_client, Config.ADMIN_IDS)
    bot = Bot(token=Config.BOT_TOKEN)
    logger.info("Dashboard services initialized")


def run_async(coro):
    """Helper to run async functions in Flask routes."""
    global event_loop
    
    if event_loop is None or event_loop.is_closed():
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
    
    return event_loop.run_until_complete(coro)


def parse_duration(duration_str: str) -> Optional[int]:
    """
    Convert duration string to seconds.
    
    Args:
        duration_str: Duration like "1h", "24h", "7d", "30d", or "permanent"
        
    Returns:
        Duration in seconds, or None for permanent
    """
    if not duration_str or duration_str == "permanent":
        return None
    
    duration_map = {
        "1h": 3600,           # 1 hour
        "24h": 86400,         # 24 hours
        "7d": 604800,         # 7 days
        "30d": 2592000,       # 30 days
    }
    
    return duration_map.get(duration_str)


async def send_ban_notification(user_id: int, reason: str, duration_str: str):
    """Send ban notification to user via Telegram."""
    try:
        reason_text = BAN_REASONS.get(reason, reason)
        ban_message = (
            f"🚫 **You have been banned**\n\n"
            f"Reason: {reason_text}\n"
            f"Duration: {duration_str}\n\n"
            f"If you believe this is a mistake, please contact support."
        )
        await bot.send_message(user_id, ban_message, parse_mode="Markdown")
        logger.info("ban_notification_sent", user_id=user_id)
    except Exception as e:
        logger.warning("failed_to_notify_banned_user", user_id=user_id, error=str(e))


async def send_unban_notification(user_id: int):
    """Send unban notification to user via Telegram."""
    try:
        unban_message = (
            f"✅ **Your ban has been lifted**\n\n"
            f"You can now use the bot again.\n"
            f"Please follow the rules to avoid future bans."
        )
        await bot.send_message(user_id, unban_message, parse_mode="Markdown")
        logger.info("unban_notification_sent", user_id=user_id)
    except Exception as e:
        logger.warning("failed_to_notify_unbanned_user", user_id=user_id, error=str(e))


async def send_warning_notification(user_id: int, reason: str, warning_count: int):
    """Send warning notification to user via Telegram."""
    try:
        warn_message = (
            f"⚠️ **You have received a warning**\n\n"
            f"Reason: {reason}\n"
            f"Total Warnings: {warning_count}\n\n"
            f"⚠️ Multiple warnings may result in a ban.\n"
            f"Please follow the rules to avoid further action."
        )
        await bot.send_message(user_id, warn_message, parse_mode="Markdown")
        logger.info("warning_notification_sent", user_id=user_id)
    except Exception as e:
        logger.warning("failed_to_notify_warned_user", user_id=user_id, error=str(e))


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')


@app.route('/api/stats')
def get_stats():
    """Get dashboard statistics."""
    try:
        stats = run_async(dashboard_service.get_statistics())
        return jsonify(stats)
    except Exception as e:
        logger.error("get_stats_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/users')
def get_users():
    """Get all users with pagination."""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        users = run_async(dashboard_service.get_all_users_paginated(page, per_page))
        return jsonify(users)
    except Exception as e:
        logger.error("get_users_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/users/online')
def get_online_users():
    """Get currently online/active users."""
    try:
        users = run_async(dashboard_service.get_online_users())
        return jsonify(users)
    except Exception as e:
        logger.error("get_online_users_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/users/in-chat')
def get_users_in_chat():
    """Get users currently in chat."""
    try:
        users = run_async(dashboard_service.get_users_in_chat())
        return jsonify(users)
    except Exception as e:
        logger.error("get_users_in_chat_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/users/in-queue')
def get_users_in_queue():
    """Get users currently in queue."""
    try:
        users = run_async(dashboard_service.get_users_in_queue())
        return jsonify(users)
    except Exception as e:
        logger.error("get_users_in_queue_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/users/search')
def search_users():
    """Search users by various criteria."""
    try:
        user_id = request.args.get('user_id')
        username = request.args.get('username')
        gender = request.args.get('gender')
        country = request.args.get('country')
        
        users = run_async(dashboard_service.search_users(
            user_id=user_id,
            username=username,
            gender=gender,
            country=country
        ))
        return jsonify(users)
    except Exception as e:
        logger.error("search_users_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/users/<int:user_id>')
def get_user_detail(user_id):
    """Get detailed user profile."""
    try:
        user = run_async(dashboard_service.get_user_details(user_id))
        if user:
            return jsonify(user)
        else:
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        logger.error("get_user_detail_error", user_id=user_id, error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/users/<int:user_id>/history')
def get_user_history(user_id):
    """Get user chat history."""
    try:
        history = run_async(dashboard_service.get_user_chat_history(user_id))
        return jsonify(history)
    except Exception as e:
        logger.error("get_user_history_error", user_id=user_id, error=str(e))
        return jsonify({"error": str(e)}), 500


# ============================================
# BAN/UNBAN ENDPOINTS
# ============================================

@app.route('/api/moderation/ban', methods=['POST'])
def ban_user():
    """Ban a user."""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        reason = data.get('reason')
        duration_str = data.get('duration')  # String like "1h", "7d", or "permanent"
        admin_id = data.get('admin_id', 0)
        
        if not user_id or not reason:
            return jsonify({"error": "user_id and reason are required"}), 400
        
        # Convert duration string to seconds
        duration_seconds = parse_duration(duration_str)
        
        success = run_async(admin_manager.ban_user(
            user_id=int(user_id),
            banned_by=int(admin_id),
            reason=reason,
            duration=duration_seconds,  # Duration in seconds or None for permanent
            is_auto_ban=False
        ))
        
        if success:
            # Send notification to user
            run_async(send_ban_notification(int(user_id), reason, duration_str or "Permanent"))
            
            return jsonify({
                "success": True,
                "message": f"User {user_id} banned successfully"
            })
        else:
            return jsonify({"error": "Failed to ban user"}), 500
            
    except Exception as e:
        logger.error("ban_user_api_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/moderation/unban', methods=['POST'])
def unban_user():
    """Unban a user."""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        admin_id = data.get('admin_id', 0)
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        success = run_async(admin_manager.unban_user(
            user_id=int(user_id),
            unbanned_by=int(admin_id)
        ))
        
        if success:
            # Send notification to user
            run_async(send_unban_notification(int(user_id)))
            
            return jsonify({
                "success": True,
                "message": f"User {user_id} unbanned successfully"
            })
        else:
            return jsonify({"error": "Failed to unban user"}), 500
            
    except Exception as e:
        logger.error("unban_user_api_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/moderation/warn', methods=['POST'])
def warn_user():
    """Add warning to a user."""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        reason = data.get('reason')
        admin_id = data.get('admin_id', 0)
        
        if not user_id or not reason:
            return jsonify({"error": "user_id and reason are required"}), 400
        
        warning_count = run_async(admin_manager.add_warning(
            user_id=int(user_id),
            warned_by=int(admin_id),
            reason=reason
        ))
        
        if warning_count:
            # Send notification to user
            run_async(send_warning_notification(int(user_id), reason, warning_count))
        
        return jsonify({
            "success": True,
            "message": f"Warning added to user {user_id}",
            "warning_count": warning_count
        })
            
    except Exception as e:
        logger.error("warn_user_api_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/moderation/check-ban/<int:user_id>')
def check_ban(user_id):
    """Check if user is banned."""
    try:
        is_banned, ban_data = run_async(admin_manager.is_user_banned(user_id))
        
        if is_banned and ban_data:
            # Return ban data in the format expected by frontend
            return jsonify({
                "user_id": user_id,
                "is_banned": True,
                "reason": ban_data.get("reason", "unknown"),
                "duration": "permanent" if ban_data.get("is_permanent") else "temporary",
                "banned_at": ban_data.get("banned_at"),
                "expires_at": ban_data.get("expires_at", "permanent"),
                "banned_by": ban_data.get("banned_by", 0),
                "is_auto_ban": ban_data.get("is_auto_ban", False)
            })
        else:
            return jsonify({
                "user_id": user_id,
                "is_banned": False
            })
            
    except Exception as e:
        logger.error("check_ban_api_error", user_id=user_id, error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/moderation/banned-users')
def get_banned_users():
    """Get list of all banned users."""
    try:
        banned_user_ids = run_async(admin_manager.get_banned_users_list())
        
        # Get detailed info for each banned user
        banned_users = []
        for user_id in banned_user_ids[:50]:  # Limit to 50 for performance
            ban_data = run_async(admin_manager.get_ban_info(user_id))
            if ban_data:
                # Format the data for frontend
                formatted_ban = {
                    "user_id": ban_data.get("user_id"),
                    "reason": ban_data.get("reason", "unknown"),
                    "duration": "permanent" if ban_data.get("is_permanent") else "temporary",
                    "banned_at": ban_data.get("banned_at"),
                    "expires_at": ban_data.get("expires_at", "permanent"),
                    "banned_by": ban_data.get("banned_by", 0),
                    "is_auto_ban": ban_data.get("is_auto_ban", False)
                }
                banned_users.append(formatted_ban)
        
        return jsonify({
            "total": len(banned_user_ids),
            "banned_users": banned_users  # Changed from "users" to "banned_users"
        })
            
    except Exception as e:
        logger.error("get_banned_users_api_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/moderation/warned-users')
def get_warned_users():
    """Get list of all warned users."""
    try:
        warned_user_ids = run_async(admin_manager.get_warning_list())
        
        # Get warning counts
        warned_users = []
        for user_id in warned_user_ids[:50]:  # Limit to 50 for performance
            warning_count = run_async(admin_manager.get_warning_count(user_id))
            warned_users.append({
                "user_id": user_id,
                "warning_count": warning_count
            })
        
        return jsonify({
            "total": len(warned_user_ids),
            "warned_users": warned_users  # Changed from "users" to "warned_users"
        })
            
    except Exception as e:
        logger.error("get_warned_users_api_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})


if __name__ == '__main__':
    # Initialize event loop and services
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    event_loop.run_until_complete(init_services())
    
    # Run Flask app
    port = int(Config.DASHBOARD_PORT if hasattr(Config, 'DASHBOARD_PORT') else 5000)
    debug = Config.ENVIRONMENT == 'development'
    
    logger.info("Starting admin dashboard", port=port, debug=debug)
    
    try:
        app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
    finally:
        # Cleanup on shutdown
        if event_loop and not event_loop.is_closed():
            event_loop.run_until_complete(redis_client.close())
            event_loop.close()
        logger.info("Dashboard shutdown complete")
