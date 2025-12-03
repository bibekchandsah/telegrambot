# 🚀 Complete Deployment Guide

Deploy your Telegram Anonymous Chat Bot and Admin Dashboard to Railway with 24/7 uptime.

---

## 📋 **Prerequisites**

Before deploying, ensure you have:

- ✅ **GitHub Account** - Your code must be on GitHub
- ✅ **Railway Account** - Sign up at [railway.app](https://railway.app)
- ✅ **Telegram Bot Token** - Get from [@BotFather](https://t.me/BotFather)
- ✅ **Your Telegram User ID** - Get from [@userinfobot](https://t.me/userinfobot)
- ✅ **Code pushed to GitHub** - All changes committed and pushed

---

## 🎯 **Deployment Overview**

You'll deploy **3 services** on Railway:

1. **Redis Database** - Stores user data and sessions
2. **Telegram Bot** - Main bot service (24/7 polling)
3. **Admin Dashboard** - Web-based management interface

---

## 📦 **Part 1: Deploy Telegram Bot**

### **Step 1: Push Code to GitHub**

```powershell
git add .
git commit -m "Ready for Railway deployment"
git push origin main
```

### **Step 2: Create Railway Project**

1. Go to [railway.app](https://railway.app)
2. Click **"Sign in with GitHub"**
3. Authorize Railway
4. Click **"New Project"**
5. Select **"Deploy from GitHub repo"**
6. Choose your **telegrambot** repository
7. Click **"Deploy Now"**

Railway will create the first service (bot).

### **Step 3: Add Redis Database**

1. In your Railway project, click **"+ New"**
2. Select **"Database"**
3. Choose **"Add Redis"**
4. Railway automatically creates `REDIS_URL` variable

### **Step 4: Configure Bot Environment Variables**

1. Click on your **bot service** (telegram-chat-bot)
2. Go to **"Variables"** tab
3. Click **"+ New Variable"** and add:

#### **Reference Variable:**

**REDIS_URL:**
- Click "+ New Variable"
- Click "Add a Reference"
- Select: `REDIS_URL` from `telegram-bot-redis`
- Click "Add"

#### **Manual Variables:**

| Variable | Value | Description |
|----------|-------|-------------|
| `BOT_TOKEN` | Your bot token | From @BotFather |
| `ADMIN_IDS` | Your user ID | From @userinfobot |
| `ENVIRONMENT` | `production` | Production mode |
| `LOG_LEVEL` | `INFO` | Logging level |
| `MAX_QUEUE_SIZE` | `500` | Max users in queue |
| `MESSAGE_RATE_LIMIT` | `30` | Messages per minute |
| `CHAT_TIMEOUT` | `600` | Auto-disconnect (seconds) |
| `NEXT_COMMAND_LIMIT` | `10` | Max /next per minute |

### **Step 5: Verify Bot Deployment**

1. Go to **"Deployments"** tab
2. Wait 2-3 minutes for build
3. Check **"Deploy Logs"** for:
   ```
   ✅ "bot_initialized"
   ✅ "bot_info"
   ✅ Your bot username
   ```

### **Step 6: Test Your Bot**

1. Open Telegram
2. Search for your bot
3. Send `/start`
4. Bot should respond instantly ✅

---

## 🎛️ **Part 2: Deploy Admin Dashboard**

### **Step 1: Create Dashboard Service**

1. In your Railway project, click **"+ New"**
2. Select **"GitHub Repo"**
3. Choose your **telegrambot** repository
4. Railway creates a new service

### **Step 2: Configure Service Name**

1. Click on the **new service**
2. Go to **"Settings"** tab
3. Scroll to top and find **"Service Name"**
4. Change to: `telegram-dashboard`
5. Save

### **Step 3: Set Dockerfile Path**

Still in Settings, scroll to **"Build"** section:

1. Find **"Dockerfile Path"** field
2. Enter: `Dockerfile.dashboard`
3. Save

### **Step 4: Add Dashboard Environment Variables**

Go to **"Variables"** tab:

#### **Reference Variables:**

1. **REDIS_URL:**
   - Click "+ New Variable"
   - Click "Add a Reference"
   - Select: `REDIS_URL` from `telegram-bot-redis`
   - Click "Add"

2. **BOT_TOKEN:**
   - Click "+ New Variable"
   - Click "Add a Reference"
   - Select: `BOT_TOKEN` from `telegram-chat-bot`
   - Click "Add"

#### **Manual Variables:**

| Variable | Value |
|----------|-------|
| `ADMIN_IDS` | Your Telegram user ID |
| `ENVIRONMENT` | `production` |
| `DASHBOARD_PORT` | `5000` |
| `DASHBOARD_HOST` | `0.0.0.0` |

### **Step 5: Enable Public Networking**

1. Go to **"Settings"** tab
2. Scroll to **"Networking"** section
3. Click **"Generate Domain"**
4. Railway gives you a URL like: `telegram-dashboard-production-8801.up.railway.app`
5. **Save this URL!**

### **Step 6: Verify Dashboard Deployment**

1. Go to **"Deployments"** tab
2. Wait 2-3 minutes for build
3. Check **"Deploy Logs"** for:
   ```
   ✅ "Initializing dashboard services..."
   ✅ "Services initialized successfully!"
   ✅ "Starting admin dashboard"
   ✅ "Running on http://0.0.0.0:PORT"
   ```

### **Step 7: Access Your Dashboard**

1. Open the Railway-generated URL in your browser
2. You'll see the admin dashboard with:
   - 📊 Real-time statistics
   - 👥 User management
   - 💬 Active chat sessions
   - ⏳ Queue monitoring
   - 🚫 Ban/unban controls

---

## 🏗️ **Final Architecture**

```
Railway Project: telegram-bot
│
├── telegram-bot-redis (Redis Database)
│   ├── Port: 6379
│   └── Used by: Bot + Dashboard
│
├── telegram-chat-bot (Bot Service)
│   ├── Dockerfile: Dockerfile
│   ├── Connects to: Redis
│   └── Status: Running 24/7
│
└── telegram-dashboard (Dashboard Service)
    ├── Dockerfile: Dockerfile.dashboard
    ├── Connects to: Redis
    ├── Public URL: Generated by Railway
    └── Status: Running 24/7
```

---

## ✅ **Post-Deployment Checklist**

### **Bot Service:**
- [ ] Bot responds to `/start`
- [ ] Two users can `/chat` and match
- [ ] Messages route correctly
- [ ] `/stop` ends chats properly
- [ ] `/next` finds new partners
- [ ] Admin commands work (if admin)
- [ ] Photos/media send correctly
- [ ] No errors in logs

### **Dashboard Service:**
- [ ] Dashboard loads in browser
- [ ] Statistics show correct data
- [ ] User list displays properly
- [ ] Active chats show correctly
- [ ] Queue monitoring works
- [ ] Search functionality works
- [ ] Ban/unban controls work
- [ ] Responsive on mobile

### **Both Services:**
- [ ] Running 24/7 without sleep
- [ ] Redis connection stable
- [ ] No deployment errors
- [ ] Logs show normal activity

---

## 🐛 **Troubleshooting**

### **Bot Not Starting**

**Error:** `BOT_TOKEN environment variable is required`

**Fix:**
1. Go to bot service → Variables tab
2. Verify `BOT_TOKEN` is set
3. Check it's the correct token from @BotFather

**Error:** `REDIS_URL environment variable is required`

**Fix:**
1. Go to bot service → Variables tab
2. Add `REDIS_URL` as reference from `telegram-bot-redis`
3. Redeploy

### **Bot Conflict Error**

**Error:** `Conflict: terminated by other getUpdates request`

**Fix:**
- You have multiple bot instances running
- Delete the duplicate service
- Keep only one bot service running

### **Dashboard Not Loading**

**Error:** `Application failed to respond`

**Fix:**
1. Check Dockerfile path is `Dockerfile.dashboard`
2. Verify all variables are set (REDIS_URL, BOT_TOKEN, etc.)
3. Check logs for startup errors
4. Ensure public domain is generated

**Error:** `NameError: name 'os' is not defined`

**Fix:**
- Update code to latest version from GitHub
- The fix is already committed in the repository

### **Dashboard Shows No Data**

**Fix:**
1. Verify REDIS_URL points to same Redis as bot
2. Check bot is running and users are active
3. Test Redis connection in logs
4. Refresh dashboard page

---

## 💰 **Cost Management**

### **Railway Free Tier**

- **Credit:** $5/month
- **Estimated Usage:**
  - Bot: ~$2.50/month
  - Redis: ~$1.50/month
  - Dashboard: ~$1.00/month
  - **Total: ~$5/month** (within free tier!)

### **Runtime Estimates**

- **Free tier lasts:** ~20-25 days continuous
- **For 50-100 concurrent users**
- **~1000 messages/day**

### **Monitor Usage**

1. Go to Railway Dashboard
2. Click profile icon → **"Account Settings"**
3. View **"Usage"** tab
4. See remaining credit

### **When Credit Runs Out**

**Options:**
1. **Upgrade to Hobby Plan** - $5/month unlimited
2. **Wait for monthly reset** - Credit refreshes monthly
3. **Optimize resources** - Reduce if possible

---

## 🔄 **Updating Your Deployment**

### **Automatic Updates**

Every git push automatically redeploys:

```powershell
# Make changes to your code
git add .
git commit -m "Add new feature"
git push origin main

# Railway automatically:
# 1. Detects the push
# 2. Rebuilds Docker images
# 3. Deploys new versions
# 4. Restarts services gracefully
```

### **Manual Redeploy**

If needed:
1. Go to service → **"Deployments"** tab
2. Click **"Redeploy"** on latest deployment
3. Wait for completion

---

## 🔐 **Security Best Practices**

### **Protect Your Tokens**

- ✅ Never commit `.env` file (it's in `.gitignore`)
- ✅ Use Railway's Variables tab for secrets
- ✅ Regenerate tokens if exposed
- ✅ Limit admin access to trusted users only

### **Dashboard Security**

Your dashboard is publicly accessible. Options:

**Option 1: Keep URL Secret**
- URL is randomly generated and hard to guess
- Share only with trusted admins

**Option 2: Add HTTP Basic Auth** (Recommended)
- Add username/password protection
- See `DASHBOARD_RAILWAY_DEPLOY.md` for implementation

**Option 3: IP Whitelist** (Railway Pro)
- Restrict access to specific IP addresses
- Available on paid plans

### **Redis Security**

Railway Redis is private by default:
- ✅ Only accessible within your project
- ✅ Encrypted connections
- ✅ No public internet access

---

## 📊 **Monitoring**

### **View Bot Logs**

```
Railway Dashboard → telegram-chat-bot → Logs
```

Look for:
- ✅ `bot_initialized` - Bot started
- ✅ `match_found` - Users matched
- ⚠️ `rate_limit_exceeded` - Spam detected
- ❌ `error` - Issues to fix

### **View Dashboard Logs**

```
Railway Dashboard → telegram-dashboard → Logs
```

Look for:
- ✅ `Starting admin dashboard` - Dashboard started
- ✅ `redis_connected` - Database connected
- ❌ Any Python errors

### **Check Metrics**

```
Railway Dashboard → Service → Metrics
```

Monitor:
- **CPU Usage** - Should be <10%
- **Memory** - Bot: 100-200MB, Dashboard: 50-100MB
- **Network** - Shows activity levels

### **Redis Health**

```
Railway Dashboard → telegram-bot-redis → Metrics
```

Monitor:
- **Memory Usage** - Active data size
- **Operations/sec** - Command throughput
- **Connection Count** - Active connections

---

## 📈 **Scaling**

### **When to Scale**

Consider upgrading when:
- More than 100 concurrent users
- Bot responds slowly
- Credit runs out quickly
- Need more memory/CPU

### **Railway Plans**

| Plan | Price | Best For |
|------|-------|----------|
| **Free** | $5 credit/month | Testing, small bots (50-100 users) |
| **Hobby** | $5/month | Personal projects (100-500 users) |
| **Pro** | $20/month | Production (500+ users) |

### **How to Upgrade**

1. Go to **Account Settings**
2. Click **"Plans"** tab
3. Select **Hobby** or **Pro**
4. Add payment method
5. Confirm upgrade

---

## 🆘 **Getting Help**

### **Railway Resources**

- [Railway Documentation](https://docs.railway.app/)
- [Railway Discord](https://discord.gg/railway)
- [Railway Status](https://status.railway.app/)

### **Project Documentation**

- `RAILWAY_DEPLOYMENT.md` - Detailed bot deployment
- `DASHBOARD_RAILWAY_DEPLOY.md` - Dashboard-specific guide
- `QUICK_DEPLOY.md` - 5-minute quick start
- `README.md` - Project overview

### **Common Issues**

1. **Check logs first** - Most issues show in logs
2. **Verify environment variables** - Missing vars cause errors
3. **Test locally** - Ensure code works before deploying
4. **Review documentation** - Guides cover common scenarios

---

## 🎉 **Success!**

Once deployed, you have:

- ✅ **Telegram Bot** running 24/7 (no sleep!)
- ✅ **Admin Dashboard** accessible from anywhere
- ✅ **Redis Database** for data persistence
- ✅ **Auto-deployment** on every git push
- ✅ **Real-time monitoring** via Railway dashboard
- ✅ **Scalable architecture** ready to grow

---

## 📱 **Share Your Bot**

Your bot is now live! Share it:

1. **Get bot link:** `https://t.me/your_bot_username`
2. **Share with users** via social media, websites, etc.
3. **Monitor usage** via admin dashboard
4. **Gather feedback** and improve

---

## 🔗 **Quick Links**

- **Railway Dashboard:** [railway.app/dashboard](https://railway.app/dashboard)
- **Bot Service:** Check Railway project
- **Admin Dashboard:** Your generated Railway URL
- **GitHub Repo:** [github.com/bibekchandsah/telegrambot](https://github.com/bibekchandsah/telegrambot)

---

**Your anonymous chat bot is now serving users worldwide! 🌍**

**Made with ❤️ for 24/7 anonymous conversations**
