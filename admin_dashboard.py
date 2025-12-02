"""Admin Dashboard - Web-based interface for bot administration."""
import asyncio
import json
import time
from datetime import datetime
from typing import Optional
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from telegram import Bot
from src.config import Config
from src.db.redis_client import RedisClient
from src.services.dashboard import DashboardService
from src.services.admin import AdminManager
from src.services.reports import ReportManager
from src.utils.logger import get_logger
from threading import local

logger = get_logger(__name__)

# Thread-local storage for per-request services
thread_local = local()

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

# Thread-local storage for per-request services
thread_local = local()

# Global configuration
redis_url = None
bot_token = None
admin_ids = None


async def init_services():
    """Store configuration."""
    global redis_url, bot_token, admin_ids
    
    redis_url = Config.REDIS_URL
    bot_token = Config.BOT_TOKEN
    admin_ids = Config.ADMIN_IDS
    
    # Test connection
    test_client = RedisClient()
    await test_client.connect()
    await test_client.close()
    
    logger.info("Dashboard configuration initialized")


def get_thread_services():
    """Get or create services for current thread."""
    if not hasattr(thread_local, 'services'):
        # Create new services for this thread
        async def create_services():
            client = RedisClient()
            await client.connect()
            dashboard = DashboardService(client)
            admin = AdminManager(client, admin_ids)
            reports = ReportManager(client)
            telegram_bot = Bot(token=bot_token)
            return client, dashboard, admin, reports, telegram_bot
        
        # Run in new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        thread_local.services = loop.run_until_complete(create_services())
        thread_local.loop = loop
    
    return thread_local.services


def run_async(coro):
    """Helper to run async functions using thread-local services."""
    # Get or create services for this thread
    get_thread_services()  # Ensure services exist
    
    # Run coroutine in thread's event loop
    loop = thread_local.loop
    try:
        return loop.run_until_complete(coro)
    except Exception as e:
        logger.error("run_async_error", error=str(e))
        raise


def parse_duration(duration_str: str) -> Optional[int]:
    """
    Convert duration string to seconds.
    
    Args:
        duration_str: Duration like "1h", "6h", "24h", "7d", "30d", or "permanent"
        
    Returns:
        Duration in seconds, or None for permanent
    """
    if not duration_str or duration_str == "permanent":
        return None
    
    duration_map = {
        "1h": 3600,           # 1 hour
        "6h": 21600,          # 6 hours
        "24h": 86400,         # 24 hours
        "7d": 604800,         # 7 days
        "30d": 2592000,       # 30 days
    }
    
    return duration_map.get(duration_str)


def parse_admin_id(admin_id_value) -> int:
    """
    Convert admin_id to integer, handling string 'admin' or numeric values.
    
    Args:
        admin_id_value: Admin ID from request (can be string 'admin', int, or None)
        
    Returns:
        Integer admin ID (0 if invalid)
    """
    if not admin_id_value:
        return 0
    
    # If it's already an int, return it
    if isinstance(admin_id_value, int):
        return admin_id_value
    
    # If it's a string, try to convert it
    if isinstance(admin_id_value, str):
        # Handle 'admin' string literal
        if admin_id_value.lower() == 'admin':
            return 0
        # Try to parse as integer
        try:
            return int(admin_id_value)
        except ValueError:
            return 0
    
    return 0


async def send_ban_notification_with_bot(bot_instance, user_id: int, reason: str, duration_str: str):
    """Send ban notification to user via Telegram."""
    try:
        reason_text = BAN_REASONS.get(reason, reason)
        ban_message = (
            f"🚫 **You have been banned**\n\n"
            f"Reason: {reason_text}\n"
            f"Duration: {duration_str}\n\n"
            f"If you believe this is a mistake, please contact support."
        )
        await bot_instance.send_message(user_id, ban_message, parse_mode="Markdown")
        logger.info("ban_notification_sent", user_id=user_id)
    except Exception as e:
        logger.warning("failed_to_notify_banned_user", user_id=user_id, error=str(e))


async def send_unban_notification_with_bot(bot_instance, user_id: int):
    """Send unban notification to user via Telegram."""
    try:
        unban_message = (
            f"✅ **Your ban has been lifted**\n\n"
            f"You can now use the bot again.\n"
            f"Please follow the rules to avoid future bans."
        )
        await bot_instance.send_message(user_id, unban_message, parse_mode="Markdown")
        logger.info("unban_notification_sent", user_id=user_id)
    except Exception as e:
        logger.warning("failed_to_notify_unbanned_user", user_id=user_id, error=str(e))


async def send_warning_notification_with_bot(bot_instance, user_id: int, reason: str, warning_count: int):
    """Send warning notification to user via Telegram."""
    try:
        warn_message = (
            f"⚠️ **You have received a warning**\n\n"
            f"Reason: {reason}\n"
            f"Total Warnings: {warning_count}\n\n"
            f"⚠️ Multiple warnings may result in a ban.\n"
            f"Please follow the rules to avoid further action."
        )
        await bot_instance.send_message(user_id, warn_message, parse_mode="Markdown")
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
        _, dashboard_service, _, _, _ = get_thread_services()
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
        
        _, dashboard_service, _, _, _ = get_thread_services()
        users = run_async(dashboard_service.get_all_users_paginated(page, per_page))
        return jsonify(users)
    except Exception as e:
        logger.error("get_users_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/users/online')
def get_online_users():
    """Get currently online/active users."""
    try:
        _, dashboard_service, _, _, _ = get_thread_services()
        users = run_async(dashboard_service.get_online_users())
        return jsonify(users)
    except Exception as e:
        logger.error("get_online_users_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/users/in-chat')
def get_users_in_chat():
    """Get users currently in chat."""
    try:
        _, dashboard_service, _, _, _ = get_thread_services()
        users = run_async(dashboard_service.get_users_in_chat())
        return jsonify(users)
    except Exception as e:
        logger.error("get_users_in_chat_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/users/in-queue')
def get_users_in_queue():
    """Get users currently in queue."""
    try:
        _, dashboard_service, _, _, _ = get_thread_services()
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
        
        _, dashboard_service, _, _, _ = get_thread_services()
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
        _, dashboard_service, _, _, _ = get_thread_services()
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
        _, dashboard_service, _, _, _ = get_thread_services()
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
        
        _, _, admin_manager, _, bot = get_thread_services()
        success = run_async(admin_manager.ban_user(
            user_id=int(user_id),
            banned_by=int(admin_id),
            reason=reason,
            duration=duration_seconds,  # Duration in seconds or None for permanent
            is_auto_ban=False
        ))
        
        if success:
            # Send notification to user
            run_async(send_ban_notification_with_bot(bot, int(user_id), reason, duration_str or "Permanent"))
            
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
        
        _, _, admin_manager, _, bot = get_thread_services()
        success = run_async(admin_manager.unban_user(
            user_id=int(user_id),
            unbanned_by=int(admin_id)
        ))
        
        if success:
            # Send notification to user
            run_async(send_unban_notification_with_bot(bot, int(user_id)))
            
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
        
        _, _, admin_manager, _, bot = get_thread_services()
        warning_count = run_async(admin_manager.add_warning(
            user_id=int(user_id),
            warned_by=int(admin_id),
            reason=reason
        ))
        
        if warning_count:
            # Send notification to user
            run_async(send_warning_notification_with_bot(bot, int(user_id), reason, warning_count))
        
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
        _, _, admin_manager, _, _ = get_thread_services()
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
        _, _, admin_manager, _, _ = get_thread_services()
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
        _, _, admin_manager, _, _ = get_thread_services()
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


# ============================================
# REPORT & SAFETY MANAGEMENT ENDPOINTS
# ============================================

@app.route('/api/reports/all')
def get_all_reports():
    """Get all user reports."""
    try:
        limit = request.args.get('limit', 100, type=int)
        _, _, _, report_manager, _ = get_thread_services()
        reports = run_async(report_manager.get_all_reports(limit=limit))
        
        return jsonify({
            "success": True,
            "total": len(reports),
            "reports": reports
        })
    except Exception as e:
        logger.error("get_all_reports_api_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/reports/user/<int:user_id>')
def get_user_reports(user_id):
    """Get reports for a specific user."""
    try:
        _, _, _, report_manager, _ = get_thread_services()
        report_data = run_async(report_manager.get_report_by_user(user_id))
        
        if report_data:
            return jsonify({
                "success": True,
                "report": report_data
            })
        else:
            return jsonify({
                "success": False,
                "message": "No reports found for this user"
            }), 404
    except Exception as e:
        logger.error("get_user_reports_api_error", user_id=user_id, error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/reports/approve', methods=['POST'])
def approve_report():
    """Approve a report."""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        admin_id = parse_admin_id(data.get('admin_id'))
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        _, _, _, report_manager, _ = get_thread_services()
        success = run_async(report_manager.approve_report(int(user_id), admin_id))
        
        if success:
            # Log moderation action
            run_async(report_manager.log_moderation_action(
                admin_id=admin_id,
                action="report_approved",
                target_user_id=int(user_id),
                details=f"Report approved for user {user_id}"
            ))
            
            return jsonify({
                "success": True,
                "message": f"Report for user {user_id} approved"
            })
        else:
            return jsonify({"error": "Failed to approve report"}), 500
    except Exception as e:
        logger.error("approve_report_api_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/reports/reject', methods=['POST'])
def reject_report():
    """Reject a report."""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        admin_id = parse_admin_id(data.get('admin_id'))
        reason = data.get('reason', '')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        _, _, _, report_manager, _ = get_thread_services()
        success = run_async(report_manager.reject_report(int(user_id), admin_id, reason))
        
        if success:
            # Log moderation action
            run_async(report_manager.log_moderation_action(
                admin_id=admin_id,
                action="report_rejected",
                target_user_id=int(user_id),
                details=f"Report rejected for user {user_id}: {reason}"
            ))
            
            return jsonify({
                "success": True,
                "message": f"Report for user {user_id} rejected"
            })
        else:
            return jsonify({"error": "Failed to reject report"}), 500
    except Exception as e:
        logger.error("reject_report_api_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/reports/stats')
def get_report_stats():
    """Get report statistics."""
    try:
        _, _, _, report_manager, _ = get_thread_services()
        stats = run_async(report_manager.get_report_stats())
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        logger.error("get_report_stats_api_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/reports/approve-individual', methods=['POST'])
def approve_individual_report():
    """Approve a single individual report."""
    try:
        data = request.get_json()
        reported_user_id = data.get('reported_user_id')
        reporter_id = data.get('reporter_id')
        timestamp = data.get('timestamp')
        admin_id = parse_admin_id(data.get('admin_id'))
        
        if not all([reported_user_id, reporter_id, timestamp]):
            return jsonify({"error": "reported_user_id, reporter_id, and timestamp are required"}), 400
        
        redis_client, _, _, report_manager, _ = get_thread_services()
        
        # Remove rejection if exists (allow status change)
        rejection_key = f"report:individual_rejection:{reported_user_id}:{reporter_id}:{timestamp}"
        run_async(redis_client.delete(rejection_key))
        
        # Store individual approval
        approval_key = f"report:individual_approval:{reported_user_id}:{reporter_id}:{timestamp}"
        approval_data = {
            "reported_user_id": int(reported_user_id),
            "reporter_id": int(reporter_id),
            "timestamp": int(timestamp),
            "admin_id": admin_id,
            "approved_at": int(time.time()),
            "action": "approved"
        }
        await_result = run_async(redis_client.set(approval_key, json.dumps(approval_data)))
        
        # Log moderation action
        run_async(report_manager.log_moderation_action(
            admin_id=admin_id,
            action="individual_report_approved",
            target_user_id=int(reported_user_id),
            details=f"Individual report approved: Reporter {reporter_id} -> User {reported_user_id}"
        ))
        
        return jsonify({
            "success": True,
            "message": "Report approved successfully"
        })
    except Exception as e:
        logger.error("approve_individual_report_api_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/reports/reject-individual', methods=['POST'])
def reject_individual_report():
    """Reject a single individual report."""
    try:
        data = request.get_json()
        reported_user_id = data.get('reported_user_id')
        reporter_id = data.get('reporter_id')
        timestamp = data.get('timestamp')
        admin_id = parse_admin_id(data.get('admin_id'))
        reason = data.get('reason', 'Invalid report')
        
        if not all([reported_user_id, reporter_id, timestamp]):
            return jsonify({"error": "reported_user_id, reporter_id, and timestamp are required"}), 400
        
        redis_client, _, _, report_manager, _ = get_thread_services()
        
        # Remove approval if exists (allow status change)
        approval_key = f"report:individual_approval:{reported_user_id}:{reporter_id}:{timestamp}"
        run_async(redis_client.delete(approval_key))
        
        # Store individual rejection
        rejection_key = f"report:individual_rejection:{reported_user_id}:{reporter_id}:{timestamp}"
        rejection_data = {
            "reported_user_id": int(reported_user_id),
            "reporter_id": int(reporter_id),
            "timestamp": int(timestamp),
            "admin_id": admin_id,
            "rejected_at": int(time.time()),
            "reason": reason,
            "action": "rejected"
        }
        await_result = run_async(redis_client.set(rejection_key, json.dumps(rejection_data)))
        
        # Log moderation action
        run_async(report_manager.log_moderation_action(
            admin_id=admin_id,
            action="individual_report_rejected",
            target_user_id=int(reported_user_id),
            details=f"Individual report rejected: Reporter {reporter_id} -> User {reported_user_id}. Reason: {reason}"
        ))
        
        return jsonify({
            "success": True,
            "message": "Report rejected successfully"
        })
    except Exception as e:
        logger.error("reject_individual_report_api_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/reports/individual-status')
def get_individual_report_status():
    """Get status of an individual report."""
    try:
        reported_user_id = request.args.get('reported_user')
        reporter_id = request.args.get('reporter')
        timestamp = request.args.get('timestamp')
        
        if not all([reported_user_id, reporter_id, timestamp]):
            return jsonify({"error": "Missing parameters"}), 400
        
        redis_client, _, _, _, _ = get_thread_services()
        
        # Check approval
        approval_key = f"report:individual_approval:{reported_user_id}:{reporter_id}:{timestamp}"
        approval_data = run_async(redis_client.get(approval_key))
        if approval_data:
            return jsonify({"status": "approved"})
        
        # Check rejection
        rejection_key = f"report:individual_rejection:{reported_user_id}:{reporter_id}:{timestamp}"
        rejection_data = run_async(redis_client.get(rejection_key))
        if rejection_data:
            return jsonify({"status": "rejected"})
        
        return jsonify({"status": "pending"})
    except Exception as e:
        logger.error("get_individual_report_status_api_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/reports/all-individual-statuses', methods=['POST'])
def get_all_individual_statuses():
    """Get statuses for multiple individual reports in batch."""
    try:
        data = request.get_json()
        reports = data.get('reports', [])
        
        if not reports:
            return jsonify({"success": True, "statuses": []})
        
        redis_client, _, _, _, _ = get_thread_services()
        statuses = []
        
        for report in reports:
            reported_user_id = report.get('reported_user_id')
            reporter_id = report.get('reporter_id')
            timestamp = report.get('timestamp')
            
            if not all([reported_user_id, reporter_id, timestamp]):
                continue
            
            # Check approval
            approval_key = f"report:individual_approval:{reported_user_id}:{reporter_id}:{timestamp}"
            approval_data = run_async(redis_client.get(approval_key))
            if approval_data:
                statuses.append({
                    "reported_user_id": reported_user_id,
                    "reporter_id": reporter_id,
                    "timestamp": timestamp,
                    "status": "approved"
                })
                continue
            
            # Check rejection
            rejection_key = f"report:individual_rejection:{reported_user_id}:{reporter_id}:{timestamp}"
            rejection_data = run_async(redis_client.get(rejection_key))
            if rejection_data:
                statuses.append({
                    "reported_user_id": reported_user_id,
                    "reporter_id": reporter_id,
                    "timestamp": timestamp,
                    "status": "rejected"
                })
                continue
            
            # Default to pending
            statuses.append({
                "reported_user_id": reported_user_id,
                "reporter_id": reporter_id,
                "timestamp": timestamp,
                "status": "pending"
            })
        
        return jsonify({
            "success": True,
            "statuses": statuses
        })
    except Exception as e:
        logger.error("get_all_individual_statuses_api_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/safety/block-media', methods=['POST'])
def block_media():
    """Block a media type."""
    try:
        data = request.get_json()
        media_type = data.get('media_type')
        admin_id = parse_admin_id(data.get('admin_id'))
        duration_str = data.get('duration')  # "1h", "24h", "7d", "permanent"
        reason = data.get('reason', 'Content moderation')
        
        if not media_type:
            return jsonify({"error": "media_type is required"}), 400
        
        # Convert duration
        duration_seconds = parse_duration(duration_str)
        
        _, _, _, report_manager, _ = get_thread_services()
        success = run_async(report_manager.block_media_type(
            media_type=media_type,
            duration=duration_seconds,
            reason=reason
        ))
        
        if success:
            # Log moderation action
            run_async(report_manager.log_moderation_action(
                admin_id=admin_id,
                action="media_blocked",
                details=f"Blocked {media_type}: {reason} (Duration: {duration_str})"
            ))
            
            return jsonify({
                "success": True,
                "message": f"Media type {media_type} blocked successfully"
            })
        else:
            return jsonify({"error": "Failed to block media type"}), 500
    except Exception as e:
        logger.error("block_media_api_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/safety/unblock-media', methods=['POST'])
def unblock_media():
    """Unblock a media type."""
    try:
        data = request.get_json()
        media_type = data.get('media_type')
        admin_id = parse_admin_id(data.get('admin_id'))
        
        if not media_type:
            return jsonify({"error": "media_type is required"}), 400
        
        _, _, _, report_manager, _ = get_thread_services()
        success = run_async(report_manager.unblock_media_type(media_type))
        
        if success:
            # Log moderation action
            run_async(report_manager.log_moderation_action(
                admin_id=admin_id,
                action="media_unblocked",
                details=f"Unblocked {media_type}"
            ))
            
            return jsonify({
                "success": True,
                "message": f"Media type {media_type} unblocked successfully"
            })
        else:
            return jsonify({"error": "Failed to unblock media type"}), 500
    except Exception as e:
        logger.error("unblock_media_api_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/safety/blocked-media')
def get_blocked_media():
    """Get list of blocked media types."""
    try:
        _, _, _, report_manager, _ = get_thread_services()
        blocked_media = run_async(report_manager.get_blocked_media_types())
        return jsonify({
            "total": len(blocked_media),
            "blocked_media": blocked_media
        })
    except Exception as e:
        logger.error("get_blocked_media_api_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/safety/bad-words')
def get_bad_words():
    """Get all bad words."""
    try:
        _, _, _, report_manager, _ = get_thread_services()
        bad_words = run_async(report_manager.get_bad_words())
        return jsonify({
            "total": len(bad_words),
            "bad_words": bad_words
        })
    except Exception as e:
        logger.error("get_bad_words_api_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/safety/bad-words/add', methods=['POST'])
def add_bad_word():
    """Add a bad word."""
    try:
        data = request.get_json()
        word = data.get('word')
        admin_id = parse_admin_id(data.get('admin_id'))
        
        if not word:
            return jsonify({"error": "word is required"}), 400
        
        _, _, _, report_manager, _ = get_thread_services()
        success = run_async(report_manager.add_bad_word(word, admin_id))
        
        if success:
            # Log moderation action
            run_async(report_manager.log_moderation_action(
                admin_id=admin_id,
                action="bad_word_added",
                details=f"Added bad word: {word}"
            ))
            
            return jsonify({
                "success": True,
                "message": f"Bad word '{word}' added successfully"
            })
        else:
            return jsonify({"error": "Failed to add bad word"}), 500
    except Exception as e:
        logger.error("add_bad_word_api_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/safety/bad-words/remove', methods=['POST'])
def remove_bad_word():
    """Remove a bad word."""
    try:
        data = request.get_json()
        word = data.get('word')
        admin_id = parse_admin_id(data.get('admin_id'))
        
        if not word:
            return jsonify({"error": "word is required"}), 400
        
        _, _, _, report_manager, _ = get_thread_services()
        success = run_async(report_manager.remove_bad_word(word, admin_id))
        
        if success:
            # Log moderation action
            run_async(report_manager.log_moderation_action(
                admin_id=admin_id,
                action="bad_word_removed",
                details=f"Removed bad word: {word}"
            ))
            
            return jsonify({
                "success": True,
                "message": f"Bad word '{word}' removed successfully"
            })
        else:
            return jsonify({"error": "Word not found or failed to remove"}), 500
    except Exception as e:
        logger.error("remove_bad_word_api_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/safety/moderation-logs')
def get_moderation_logs():
    """Get moderation logs."""
    try:
        limit = request.args.get('limit', 100, type=int)
        _, _, _, report_manager, _ = get_thread_services()
        logs = run_async(report_manager.get_moderation_logs(limit=limit))
        
        return jsonify({
            "total": len(logs),
            "logs": logs
        })
    except Exception as e:
        logger.error("get_moderation_logs_api_error", error=str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})


if __name__ == '__main__':
    # Initialize services with proper asyncio context
    print("Initializing dashboard services...")
    asyncio.run(init_services())
    print("Services initialized successfully!")
    
    # Run Flask app
    port = int(Config.DASHBOARD_PORT if hasattr(Config, 'DASHBOARD_PORT') else 5000)
    debug = Config.ENVIRONMENT == 'development'
    
    logger.info("Starting admin dashboard", port=port, debug=debug)
    
    try:
        app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
    finally:
        logger.info("Dashboard shutdown complete")
