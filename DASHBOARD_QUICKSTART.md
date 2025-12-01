# Admin Dashboard - Quick Start Guide

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Python 3.8 or higher
- Redis server running
- Bot environment configured

### Step 1: Install Dependencies
```bash
pip install flask flask-cors
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### Step 2: Start the Dashboard

**Windows (Command Prompt):**
```bash
start_dashboard.bat
```

**Windows (PowerShell):**
```powershell
.\start_dashboard.ps1
```

**Manual Start:**
```bash
python admin_dashboard.py
```

### Step 3: Access Dashboard
Open your browser and go to:
```
http://localhost:5000
```

## 📊 What You'll See

### Dashboard Homepage
- **5 Statistics Cards**: Total users, profiles, active users, queue, and chat counts
- **Navigation Tabs**: Switch between different user views
- **Real-time Updates**: Statistics refresh every 30 seconds

### Available Views

1. **All Users** - Complete user list with pagination
2. **Online Users** - Currently active users
3. **In Chat** - Users in active conversations
4. **In Queue** - Users waiting for matches
5. **Search** - Find users by ID, username, gender, or country

## 🔍 Common Tasks

### View User Details
1. Navigate to any user list
2. Click "View Details" button
3. See complete profile, status, and preferences

### Search for a User
1. Click "Search Users" tab
2. Enter search criteria (User ID, username, etc.)
3. Click "Search" button

### Monitor Activity
1. Check statistics cards for real-time counts
2. Use "Online Users" tab for active users
3. Use "In Chat" tab to see chat pairs

## ⚙️ Configuration

### Optional Environment Variables
Add to your `.env` file:

```env
# Dashboard Configuration
DASHBOARD_PORT=5000        # Port number (default: 5000)
DASHBOARD_HOST=0.0.0.0     # Host address (default: 0.0.0.0)
ENVIRONMENT=development    # development or production
```

### Change Port
```bash
# In .env file
DASHBOARD_PORT=8080
```

Then access at: `http://localhost:8080`

## 🔒 Security Notes

### Development
- Default settings are for local development
- Accessible on localhost only (unless host=0.0.0.0)

### Production
⚠️ **Important**: Before deploying to production:
1. Add authentication (username/password)
2. Enable HTTPS/SSL
3. Use reverse proxy (nginx/apache)
4. Implement rate limiting
5. Restrict IP access

## 🐛 Troubleshooting

### Dashboard won't start
```bash
# Check if port is in use
netstat -ano | findstr :5000

# Check Redis connection
redis-cli ping

# View dashboard logs
python admin_dashboard.py
```

### No data showing
1. Make sure your bot is running
2. Check Redis is accessible
3. Verify users have used the bot
4. Check browser console (F12) for errors

### Can't access from other devices
1. Set `DASHBOARD_HOST=0.0.0.0` in `.env`
2. Check firewall allows port 5000
3. Use server IP: `http://YOUR_IP:5000`

## 📱 Mobile Access

The dashboard is responsive and works on mobile devices:
1. Find your server's IP address
2. Open on mobile: `http://SERVER_IP:5000`
3. Ensure devices are on same network

## 🎨 Customization

### Change Theme Colors
Edit `static/css/dashboard.css`:
```css
/* Primary gradient */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Change to your colors */
background: linear-gradient(135deg, #YOUR_COLOR1 0%, #YOUR_COLOR2 100%);
```

### Add New Statistics
1. Edit `src/services/dashboard.py` - Add data fetching
2. Edit `admin_dashboard.py` - Add API endpoint
3. Edit `templates/dashboard.html` - Add UI element
4. Edit `static/js/dashboard.js` - Add JavaScript logic

## 📋 API Usage

### Get Statistics (JSON)
```bash
curl http://localhost:5000/api/stats
```

### Get All Users
```bash
curl http://localhost:5000/api/users?page=1&per_page=20
```

### Search Users
```bash
curl "http://localhost:5000/api/users/search?username=john&gender=Male"
```

### Get User Details
```bash
curl http://localhost:5000/api/users/123456789
```

## 🔄 Auto-refresh

The dashboard auto-refreshes:
- **Statistics**: Every 30 seconds
- **Time Display**: Every 1 second
- **User Lists**: Manual refresh (click refresh button)

To change refresh interval, edit `static/js/dashboard.js`:
```javascript
// Change from 30 seconds to 60 seconds
setInterval(loadStats, 60000);
```

## 📊 Performance Tips

### Large User Base (1000+ users)
1. Default pagination: 20 users per page
2. Adjust in `static/js/dashboard.js`:
```javascript
const perPage = 50; // Change from 20 to 50
```

### Slow Loading
1. Increase Redis connection pool
2. Add caching layer
3. Optimize database queries
4. Use CDN for static files

## 🆘 Getting Help

If you encounter issues:
1. Check `ADMIN_DASHBOARD.md` for detailed documentation
2. Review error messages in terminal
3. Check browser console (F12 → Console tab)
4. Verify Redis connectivity
5. Ensure bot is running

## 📚 Next Steps

Once you're comfortable with the dashboard:
1. Add authentication for security
2. Implement chat history storage
3. Add export functionality (CSV/Excel)
4. Create analytics and reports
5. Add user management actions (ban, delete)

---

**Need more help?** See the full documentation in `ADMIN_DASHBOARD.md`
