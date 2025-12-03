# 🚀 Quick Deploy to Railway

**Use this checklist before deploying:**

## ✅ Pre-Deployment Checklist

1. **Run deployment checker:**
   ```powershell
   python check_deployment.py
   ```

2. **Test locally first:**
   ```powershell
   python -m src.bot
   ```

3. **Get your credentials:**
   - Bot Token: [@BotFather](https://t.me/BotFather)
   - Your User ID: [@userinfobot](https://t.me/userinfobot)

---

## 🚂 Deploy to Railway (5 minutes)

### 1. Push to GitHub
```powershell
git add .
git commit -m "Deploy to Railway"
git push origin main
```

### 2. Create Railway Project
1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Click "Deploy Now"

### 3. Add Redis
1. Click "+ New" → "Database" → "Add Redis"
2. Railway auto-configures `REDIS_URL`

### 4. Set Variables
Click your bot service → "Variables" → Add:

| Variable | Value |
|----------|-------|
| `BOT_TOKEN` | Your bot token from @BotFather |
| `ADMIN_IDS` | Your user ID from @userinfobot |
| `ENVIRONMENT` | `production` |

### 5. Deploy!
- Railway auto-deploys in 2-3 minutes
- Check "Logs" tab for: `"bot_initialized"`
- Test: Send `/start` to your bot

---

## 📊 Monitor

**View Logs:**
```
Railway Dashboard → Your Service → Logs
```

**Check Metrics:**
```
Railway Dashboard → Your Service → Metrics
```

**Redis Status:**
```
Railway Dashboard → Redis → Metrics
```

---

## 🆘 Troubleshooting

**Bot not responding?**
1. Check Railway logs for errors
2. Verify `BOT_TOKEN` is correct
3. Ensure Redis service is running

**Connection errors?**
1. Check `REDIS_URL` is auto-set by Railway
2. Verify Redis service is healthy
3. Restart bot service if needed

**Out of credit?**
- Check usage: Dashboard → Account → Usage
- Free tier: $5/month (~20-30 days runtime)
- Upgrade: $5/month for unlimited

---

## 📖 Full Documentation

See **RAILWAY_DEPLOYMENT.md** for:
- Detailed step-by-step guide
- Advanced configuration
- Scaling options
- Security best practices
- Admin dashboard setup

---

## 💡 Tips

✅ **Auto-deployment enabled** - Every git push auto-deploys  
✅ **No sleep issues** - Runs 24/7 continuously  
✅ **Monitor credit** - Check usage regularly  
✅ **Free tier first** - Test before upgrading  
✅ **Check logs often** - Catch issues early  

---

## 🎯 Success Criteria

After deployment, verify:
- [ ] `/start` works
- [ ] Two users can `/chat`
- [ ] Messages route correctly
- [ ] `/stop` ends chats
- [ ] `/next` finds new partner
- [ ] No errors in logs
- [ ] Bot online 24/7

---

**Happy deploying! 🎉**
