# 🚂 Railway Deployment Guide

Complete guide to deploy your Telegram Anonymous Chat Bot to Railway.app with 24/7 uptime.

## 🎯 Why Railway?

✅ **No automatic sleep** - Runs 24/7 continuously  
✅ **$5 free credit/month** - ~500-600 hours runtime  
✅ **Built-in Redis** - One-click database  
✅ **Auto-deploy on git push** - Seamless CI/CD  
✅ **Easy scaling** - Upgrade when needed  
✅ **Great logs & monitoring** - Real-time insights  

---

## 📋 Prerequisites

Before deploying, make sure you have:

1. **GitHub Account** - Your code must be on GitHub
2. **Telegram Bot Token** - Get from [@BotFather](https://t.me/BotFather)
3. **Your Telegram User ID** - Get from [@userinfobot](https://t.me/userinfobot)
4. **Railway Account** - Sign up at [railway.app](https://railway.app)

---

## 🚀 Step-by-Step Deployment

### Step 1: Prepare Your Code

1. **Ensure all changes are committed:**
   ```powershell
   git status
   git add .
   git commit -m "Ready for Railway deployment"
   ```

2. **Push to GitHub:**
   ```powershell
   git push origin main
   ```

### Step 2: Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Click **"Sign in with GitHub"**
3. Authorize Railway to access your repositories
4. Click **"New Project"**
5. Select **"Deploy from GitHub repo"**
6. Choose your `telegrambot` repository
7. Click **"Deploy Now"**

### Step 3: Add Redis Database

1. In your Railway project dashboard, click **"+ New"**
2. Select **"Database"**
3. Choose **"Add Redis"**
4. Railway automatically creates `REDIS_URL` environment variable
5. Your bot service will auto-connect to Redis

### Step 4: Configure Environment Variables

1. Click on your bot service (not Redis)
2. Go to **"Variables"** tab
3. Click **"+ New Variable"** and add:

| Variable Name | Value | Description |
|---------------|-------|-------------|
| `BOT_TOKEN` | `your_bot_token_here` | From @BotFather |
| `ADMIN_IDS` | `your_user_id` | Your Telegram ID from @userinfobot |
| `ENVIRONMENT` | `production` | Sets production mode |
| `LOG_LEVEL` | `INFO` | Logging level |
| `MAX_QUEUE_SIZE` | `500` | Max users in queue |
| `MESSAGE_RATE_LIMIT` | `30` | Messages per minute |
| `CHAT_TIMEOUT` | `600` | Auto-disconnect timeout (seconds) |
| `NEXT_COMMAND_LIMIT` | `10` | Max /next per minute |

**Note:** `REDIS_URL` is automatically set by Railway when you add Redis.

### Step 5: Deploy!

1. Railway automatically builds and deploys
2. Watch the **"Deployments"** tab for progress
3. Wait 2-3 minutes for build to complete
4. Check **"Logs"** tab for startup messages

### Step 6: Verify Deployment

1. **Check Logs:**
   - Go to **"Logs"** tab
   - Look for: `"bot_initialized"` message
   - You should see your bot's username

2. **Test Your Bot:**
   - Open Telegram
   - Search for your bot
   - Send `/start`
   - Bot should respond immediately

3. **Test Matching:**
   - Use two different Telegram accounts
   - Both send `/chat`
   - They should be matched and able to chat

---

## 📊 Monitoring Your Bot

### View Logs

```
Railway Dashboard → Your Bot Service → Logs
```

Look for:
- ✅ `bot_initialized` - Bot started successfully
- ✅ `match_found` - Users being matched
- ❌ `error` - Any errors that occur

### Check Metrics

```
Railway Dashboard → Your Bot Service → Metrics
```

Monitor:
- **CPU Usage** - Should be low (< 10%)
- **Memory** - Should be ~100-200 MB
- **Network** - Shows bot activity

### Check Redis

```
Railway Dashboard → Redis Service → Metrics
```

Monitor:
- **Memory Usage** - Active users data
- **Operations** - Commands per second

---

## 💰 Managing Free Credit

Railway gives **$5 free credit per month**. Here's how to make it last:

### Estimate Usage

- **Bot + Redis:** ~$0.007/hour combined
- **Daily Cost:** ~$0.17/day
- **Monthly Cost:** ~$5/month (perfect for free tier!)

### Monitor Credit

1. Go to **Railway Dashboard**
2. Click your **profile icon** → **Account Settings**
3. View **Usage** tab
4. See remaining credit

### When Credit Runs Out

Options:
1. **Upgrade to Hobby Plan** - $5/month for unlimited
2. **Wait for next month** - Credit refreshes monthly
3. **Optimize usage** - Reduce resources if possible

---

## 🔄 Updating Your Bot

### Automatic Deployment

Railway auto-deploys on every git push:

```powershell
# Make changes to your code
git add .
git commit -m "Add new feature"
git push origin main

# Railway automatically:
# 1. Detects the push
# 2. Rebuilds Docker image
# 3. Deploys new version
# 4. Restarts bot gracefully
```

### Manual Redeploy

If needed:
1. Go to **Railway Dashboard**
2. Click your bot service
3. Click **"Deploy"** tab
4. Click **"Redeploy"**

---

## 🛠️ Troubleshooting

### Bot Not Starting

**Problem:** Deployment successful but bot doesn't respond

**Solution:**
1. Check logs for errors:
   ```
   Railway Dashboard → Logs
   ```
2. Verify `BOT_TOKEN` is correct
3. Ensure Redis is running (check Redis service)

**Common Errors:**
```
ValueError: BOT_TOKEN environment variable is required
→ Fix: Add BOT_TOKEN in Variables tab

redis.exceptions.ConnectionError
→ Fix: Ensure Redis service is added and running
```

### Bot Keeps Restarting

**Problem:** Bot restarts every few seconds

**Solution:**
1. Check logs for error messages
2. Verify all environment variables are set
3. Ensure `REDIS_URL` points to Railway Redis
4. Check Redis service is healthy

### Messages Not Being Delivered

**Problem:** Users matched but messages don't route

**Solution:**
1. Check Redis connection:
   ```
   Railway Dashboard → Redis → Metrics
   ```
2. Verify bot has proper permissions
3. Check rate limiting isn't too aggressive

### Out of Credit

**Problem:** Bot stops mid-month

**Solution:**
1. Check usage:
   ```
   Dashboard → Account Settings → Usage
   ```
2. Options:
   - Upgrade to Hobby plan ($5/month)
   - Wait for credit refresh
   - Optimize resource usage

---

## 🔐 Security Best Practices

### Protect Your Tokens

✅ **Never commit `.env` file** - It's in `.gitignore`  
✅ **Use Railway's Variables tab** - Secrets are encrypted  
✅ **Regenerate if exposed** - Get new token from @BotFather  
✅ **Limit admin access** - Only trusted user IDs in `ADMIN_IDS`  

### Redis Security

Railway Redis is private by default:
- ✅ Only accessible within your project
- ✅ Encrypted connection
- ✅ No public internet access

---

## 📈 Scaling Options

### When to Scale

Consider upgrading when:
- More than 100 concurrent users
- Bot responds slowly
- Credit runs out quickly
- Need more memory/CPU

### Railway Plans

| Plan | Price | Best For |
|------|-------|----------|
| **Free** | $5 credit/month | Testing, small bots |
| **Hobby** | $5/month | Personal projects, 100-500 users |
| **Pro** | $20/month | Production, 500+ users |

### Upgrade Steps

1. Go to **Account Settings**
2. Click **Plans**
3. Select **Hobby** or **Pro**
4. Add payment method
5. Confirm upgrade

---

## 🎛️ Advanced Configuration

### Enable Webhook Mode (Optional)

For better performance with high traffic:

1. Set in Railway variables:
   ```
   WEBHOOK_MODE=true
   WEBHOOK_URL=https://your-bot.railway.app
   ```

2. Update `src/bot.py` to use webhooks instead of polling

### Custom Domain (Hobby Plan+)

1. Go to **Settings** → **Domains**
2. Click **"Generate Domain"** or **"Custom Domain"**
3. Use domain for webhooks

### Database Backup

Railway Redis has persistence enabled:
- ✅ Auto-saves every 60 seconds
- ✅ Survives restarts
- ✅ No manual backup needed

---

## 📱 Admin Dashboard on Railway

### Deploy Dashboard (Optional)

To run the admin dashboard on Railway:

1. Create a new service in same project
2. Use same repository
3. Set start command:
   ```
   python admin_dashboard.py
   ```
4. Add PORT variable:
   ```
   DASHBOARD_PORT=5000
   ```
5. Enable public networking
6. Access via Railway-provided URL

---

## 🆘 Support & Resources

### Railway Documentation
- [Railway Docs](https://docs.railway.app/)
- [Railway Discord](https://discord.gg/railway)
- [Railway Status](https://status.railway.app/)

### Your Bot Issues
- Check logs first
- Review this guide
- Test locally before deploying
- Open GitHub issue if needed

### Useful Commands

```powershell
# View Railway CLI (optional)
npm i -g @railway/cli

# Login to Railway
railway login

# View logs
railway logs

# Check variables
railway variables

# Open dashboard
railway open
```

---

## ✅ Post-Deployment Checklist

After deployment, verify:

- [ ] Bot responds to `/start`
- [ ] Two users can match with `/chat`
- [ ] Messages route correctly
- [ ] `/stop` ends chat properly
- [ ] `/next` finds new partner
- [ ] Admin commands work (if admin)
- [ ] Photos/stickers send correctly
- [ ] Ban system functional
- [ ] Logs show no errors
- [ ] Redis connection stable
- [ ] Bot stays online 24/7

---

## 🎉 Success!

Your bot is now live on Railway with:
- ✅ 24/7 uptime (no sleep)
- ✅ Automatic scaling
- ✅ Redis persistence
- ✅ Auto-deployment
- ✅ Real-time logging

**Bot URL:** Check Railway dashboard for service URL  
**Status:** Monitor in Railway dashboard  
**Logs:** View in real-time from dashboard  

---

**Need help?** Check Railway docs or open an issue on GitHub!

**Made with ❤️ for 24/7 anonymous conversations**
