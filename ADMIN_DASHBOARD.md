# Admin Dashboard Documentation

## Overview
The Admin Dashboard is a web-based interface for managing and monitoring your Telegram bot. It provides comprehensive user management features and real-time statistics.

## Features

### 1. Dashboard Statistics
- **Total Users**: All users who have interacted with the bot
- **Users with Profiles**: Users who have completed their profiles
- **Active Users**: Users currently online (in queue or chat)
- **Users in Queue**: Users waiting to be matched
- **Users in Chat**: Users currently chatting with a partner

### 2. User Management

#### All Users
- View all registered users with pagination (20 users per page)
- Navigate through pages of users
- View user details including ID, username, age, gender, country

#### Online Users
- See users who are currently active
- Real-time view of online activity

#### Users in Chat
- View all active chat sessions
- See chat partners (who is chatting with whom)
- Monitor ongoing conversations

#### Users in Queue
- See users waiting for a match
- Monitor queue status in real-time

### 3. Search Functionality
Search users by multiple criteria:
- **User ID**: Find specific user by their Telegram ID
- **Username**: Search by username (partial match supported)
- **Gender**: Filter by Male/Female/Other
- **Country**: Search by country name

### 4. User Details
Click "View Details" on any user to see:
- Complete profile information
- Current state (idle, in_chat, etc.)
- Queue and chat status
- Preferences settings
- Chat partner information (if in chat)

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

The dashboard requires:
- Flask 3.0.0
- Flask-CORS 4.0.0

### 2. Environment Configuration
Add these optional settings to your `.env` file:

```env
# Dashboard settings (optional)
DASHBOARD_PORT=5000
DASHBOARD_HOST=0.0.0.0
ENVIRONMENT=development  # or production
```

## Running the Dashboard

### Method 1: Using Python directly
```bash
python admin_dashboard.py
```

### Method 2: Using the startup script (Windows)
```bash
.\start_dashboard.bat
```

### Method 3: Using PowerShell script
```powershell
.\start_dashboard.ps1
```

The dashboard will start on:
- **URL**: http://localhost:5000
- **Host**: 0.0.0.0 (accessible from other devices on your network)
- **Port**: 5000 (configurable via DASHBOARD_PORT environment variable)

## Accessing the Dashboard

1. Open your web browser
2. Navigate to: `http://localhost:5000`
3. Or use your server IP: `http://YOUR_SERVER_IP:5000`

## API Endpoints

The dashboard provides these REST API endpoints:

### Statistics
- `GET /api/stats` - Get dashboard statistics

### User Management
- `GET /api/users?page=1&per_page=20` - Get all users (paginated)
- `GET /api/users/online` - Get online users
- `GET /api/users/in-chat` - Get users in chat
- `GET /api/users/in-queue` - Get users in queue
- `GET /api/users/<user_id>` - Get specific user details
- `GET /api/users/<user_id>/history` - Get user chat history
- `GET /api/users/search?user_id=&username=&gender=&country=` - Search users

### Health Check
- `GET /health` - Health check endpoint

## Security Considerations

### Production Deployment
For production, you should:

1. **Add Authentication**: Implement login system
2. **Use HTTPS**: Enable SSL/TLS
3. **Restrict Access**: Use firewall or VPN
4. **Rate Limiting**: Add rate limiting to API endpoints
5. **Environment Variables**: Keep sensitive data in `.env`

### Example: Adding Basic Auth (Optional)
You can add Flask-HTTPAuth for basic authentication:

```bash
pip install flask-httpauth
```

Then modify `admin_dashboard.py` to add authentication.

## Troubleshooting

### Dashboard won't start
1. Check if Redis is running
2. Verify `REDIS_URL` in `.env`
3. Ensure port 5000 is not in use
4. Check Python version (requires Python 3.8+)

### No data showing
1. Ensure the bot is running
2. Check Redis connection
3. Verify users have interacted with the bot
4. Check browser console for errors

### Cannot access from other devices
1. Use `0.0.0.0` as host (already configured)
2. Check firewall settings
3. Ensure port 5000 is open
4. Use correct server IP address

## Development

### File Structure
```
admin_dashboard.py          # Main Flask application
src/services/dashboard.py   # Dashboard service layer
templates/dashboard.html    # Frontend HTML
static/css/dashboard.css    # Styling
static/js/dashboard.js      # JavaScript functionality
```

### Customization
- **Styling**: Edit `static/css/dashboard.css`
- **Layout**: Modify `templates/dashboard.html`
- **Functionality**: Update `static/js/dashboard.js`
- **Backend Logic**: Edit `src/services/dashboard.py`

## Auto-refresh
The dashboard automatically refreshes:
- **Statistics**: Every 30 seconds
- **User lists**: Manual refresh via button
- **Time display**: Every second

## Browser Compatibility
Tested on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Support
For issues or questions:
1. Check the logs for errors
2. Verify Redis connection
3. Review environment variables
4. Check bot is running correctly
