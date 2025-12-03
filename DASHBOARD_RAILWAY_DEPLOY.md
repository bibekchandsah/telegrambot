# 🎛️ Admin Dashboard Deployment Guide

Deploy your admin dashboard to Railway for web-based bot management.

---

## 🚀 Quick Deploy to Railway

### Step 1: Commit Dashboard Files

```powershell
git add .
git commit -m "Add admin dashboard deployment files"
git push origin main
```

### Step 2: Create New Service in Railway

1. **Go to your Railway project** (same project as your bot)
2. Click **"+ New"** button
3. Select **"GitHub Repo"**
4. Choose your **telegrambot** repository
5. Railway will detect it's the same repo

### Step 3: Configure the Dashboard Service

1. **Service Settings:**
   - Click on the new service
   - Go to **"Settings"** tab
   - Change **"Service Name"** to `telegram-dashboard`

2. **Build Configuration:**
   - In Settings, find **"Build"** section
   - Set **"Dockerfile Path"** to: `Dockerfile.dashboard`
   - Or set **"Railway Config Path"** to: `railway.dashboard.json`

### Step 4: Add Environment Variables

Go to **"Variables"** tab and add:

#### Add Redis Reference:
1. Click **"+ New Variable"**
2. Click **"Add a Reference"**
3. Select:
   - Variable: `REDIS_URL`
   - From: `telegram-bot-redis`
4. Click **"Add"**

#### Add Bot Token Reference:
1. Click **"+ New Variable"**
2. Click **"Add a Reference"**
3. Select:
   - Variable: `BOT_TOKEN`
   - From: `telegram-chat-bot`
4. Click **"Add"**

#### Add Manual Variables:

| Variable | Value |
|----------|-------|
| `ADMIN_IDS` | Your Telegram user ID |
| `ENVIRONMENT` | `production` |
| `DASHBOARD_PORT` | `5000` |
| `DASHBOARD_HOST` | `0.0.0.0` |

### Step 5: Enable Public Networking

1. Go to **"Settings"** tab
2. Scroll to **"Networking"** section
3. Click **"Generate Domain"**
4. Railway will give you a URL like: `https://telegram-dashboard.railway.app`

### Step 6: Deploy

1. Click **"Deploy"** button
2. Wait 2-3 minutes for build
3. Check **"Logs"** for: `"Starting admin dashboard"`

---

## 🌐 Access Your Dashboard

Once deployed, access at:
```
https://your-service-name.railway.app
```

You'll see:
- 📊 Real-time statistics
- 👥 User management
- 💬 Active chat sessions
- ⏳ Queue monitoring
- 🚫 Ban/unban controls
- 📢 Broadcast management

---

## 🔒 Security Recommendations

### Option 1: Add Basic Authentication

Update `admin_dashboard.py` to add password protection:

```python
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()

DASHBOARD_USERNAME = os.getenv("DASHBOARD_USERNAME", "admin")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "changeme")

@auth.verify_password
def verify_password(username, password):
    if username == DASHBOARD_USERNAME and password == DASHBOARD_PASSWORD:
        return username
    return None

@app.route('/')
@auth.login_required
def dashboard():
    # ... existing code
```

Add to Railway Variables:
- `DASHBOARD_USERNAME` = your username
- `DASHBOARD_PASSWORD` = strong password

### Option 2: IP Whitelist (Railway Pro)

Railway Pro allows IP whitelisting in networking settings.

### Option 3: Don't Expose Publicly

Keep the dashboard service private:
- Don't generate a public domain
- Access via Railway CLI: `railway open`

---

## 📊 Dashboard Features

### Statistics Page
- Total users registered
- Currently active users
- Users in queue
- Active chat sessions
- Ban statistics

### User Management
- View all users with pagination
- Search by user ID, username, gender, country
- View user profiles and preferences
- Ban/unban users
- View user activity

### Chat Monitoring
- See active chat pairs
- Monitor message flow
- Force disconnect if needed
- View chat duration

### Queue Management
- View waiting users
- See queue length
- Monitor wait times
- Manual matching (if implemented)

### Reports & Moderation
- View user reports
- Ban users from reports
- Track warning history
- Monitor abuse patterns

---

## 🔄 Alternative: Local Tunnel (Development)

For testing without Railway:

### Using ngrok:
```powershell
# Install ngrok
choco install ngrok

# Start dashboard locally
python admin_dashboard.py

# In another terminal
ngrok http 5000
```

### Using localtunnel:
```powershell
# Install
npm install -g localtunnel

# Start dashboard
python admin_dashboard.py

# In another terminal
lt --port 5000
```

---

## 🐛 Troubleshooting

### Dashboard Won't Start

**Check logs for:**
```
"REDIS_URL environment variable is required"
```

**Fix:** Add REDIS_URL reference variable

### Can't Access Dashboard

**Check:**
1. Public domain is generated (Settings → Networking)
2. Service is deployed successfully (green checkmark)
3. Port 5000 is exposed in Dockerfile

### Dashboard Shows No Data

**Check:**
1. REDIS_URL points to same Redis as bot
2. Bot is running and users are active
3. Redis connection is working (check logs)

### CORS Errors

**Fix:** Dashboard already has CORS enabled via `flask-cors`

If issues persist, check browser console for specific errors.

---

## 💰 Cost Considerations

**Dashboard Service:**
- Lightweight Flask app
- ~$0.003/hour
- ~$2-3/month
- Fits within free tier with bot + Redis

**Total Monthly (Free Tier):**
- Bot: ~$2.50
- Redis: ~$1.50
- Dashboard: ~$1.00
- **Total: ~$5/month** (within free credit!)

---

## 🎯 Post-Deployment Checklist

- [ ] Dashboard accessible via Railway URL
- [ ] Statistics showing correct data
- [ ] User list loads properly
- [ ] Active chats display correctly
- [ ] Queue monitoring works
- [ ] Ban/unban functions work
- [ ] Search functionality works
- [ ] Responsive on mobile devices

---

## 🔗 Architecture

```
[Railway Project]
├── telegram-chat-bot (Bot Service)
│   ├── Dockerfile
│   └── Connects to Redis
│
├── telegram-bot-redis (Redis Database)
│   └── Shared by Bot & Dashboard
│
└── telegram-dashboard (Dashboard Service)
    ├── Dockerfile.dashboard
    ├── Public URL enabled
    └── Connects to Redis
```

---

## 📱 Mobile Access

The dashboard is responsive and works on:
- ✅ Desktop browsers
- ✅ Mobile phones (iOS/Android)
- ✅ Tablets
- ✅ Any device with a web browser

---

## 🆘 Need Help?

1. Check Railway logs
2. Review `ADMIN_DASHBOARD.md` for dashboard features
3. Verify all environment variables
4. Test Redis connection
5. Check bot is running properly

---

**Your dashboard will be accessible 24/7 from anywhere in the world!** 🌍
