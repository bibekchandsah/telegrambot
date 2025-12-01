"""Admin Dashboard - Web-based interface for bot administration."""
import asyncio
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from src.config import Config
from src.db.redis_client import RedisClient
from src.services.dashboard import DashboardService
from src.utils.logger import get_logger

logger = get_logger(__name__)

app = Flask(__name__)
CORS(app)

# Global instances
redis_client = None
dashboard_service = None
event_loop = None


async def init_services():
    """Initialize Redis and dashboard services."""
    global redis_client, dashboard_service
    
    redis_client = RedisClient()
    await redis_client.connect()
    dashboard_service = DashboardService(redis_client)
    logger.info("Dashboard services initialized")


def run_async(coro):
    """Helper to run async functions in Flask routes."""
    global event_loop
    
    if event_loop is None or event_loop.is_closed():
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
    
    return event_loop.run_until_complete(coro)


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
