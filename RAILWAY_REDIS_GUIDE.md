# Railway Redis Connection Guide

## 🔄 Connecting Localhost to Railway Redis

### Understanding Railway Networking

Railway provides **two types of URLs** for Redis:

1. **🔒 Private Network** (`.railway.internal`)
   - Only works **within Railway's network**
   - Faster and free (no bandwidth charges)
   - Used for service-to-service communication
   
2. **🌐 Public Network** (`.proxy.rlwy.net`)
   - Works from **anywhere** (including localhost)
   - Goes through Railway's proxy
   - Uses Railway bandwidth quota

---

## ✅ Solution 1: Use Public URL (Recommended for Development)

### Step 1: Get Your Public Redis URL

From Railway Dashboard:

1. Go to your **Redis service** → **Settings** tab
2. Under **Networking** section, copy the public domain
3. Your screenshot shows: `caboose.proxy.rlwy.net:53870`

### Step 2: Get Redis Password

From Railway Dashboard:

1. Go to **Redis service** → **Variables** tab
2. Look for `REDIS_PASSWORD` or check the internal `REDIS_URL`
3. Your password appears to be: `ffszhttFptGyvkVAqChdBvOmdfsdfpgbFrwTc`

### Step 3: Build Public URL

```env
# Format
redis://default:PASSWORD@PUBLIC_HOST:PORT/0

# Your URL
REDIS_URL=redis://default:ffszhttFptGyvkVAqChdBvOmdfsdfpgbFrwTc@caboose.proxy.rlwy.net:53870/0
```

### Step 4: Update .env File

```env
# .env (for localhost development)
REDIS_URL=redis://default:ffszhttFptGyvkVAqChdBvOmdfsdfpgbFrwTc@caboose.proxy.rlwy.net:53870/0
```

### Step 5: Test Connection

```powershell
python test_redis_connection.py
```

**Expected output:**
```
✅ Connection successful! Redis responded with PONG
✅ SET successful
✅ GET successful
```

---

## ✅ Solution 2: Separate Redis for Local/Production (Recommended for Production)

### Why Use Separate Redis?

**Pros:**
- ✅ Local changes don't affect production
- ✅ Faster (no network latency)
- ✅ Free (no Railway bandwidth usage)
- ✅ Can work offline

**Cons:**
- ⚠️ Need to run local Redis
- ⚠️ Different data between local/production

### Setup Local Redis

#### Option A: Using Docker (Recommended)

```powershell
# Pull and run Redis
docker run -d --name redis-local -p 6379:6379 redis:latest

# Verify it's running
docker ps

# Test connection
docker exec -it redis-local redis-cli ping
# Should return: PONG
```

#### Option B: Install Redis on Windows

1. Download from: https://github.com/microsoftarchive/redis/releases
2. Install and run `redis-server.exe`
3. Redis will be available at `localhost:6379`

### Update .env for Local Development

```env
# .env (for localhost)
REDIS_URL=redis://localhost:6379/0
```

### Railway Configuration (No Change Needed)

Railway should already have the internal URL:
```env
# Railway environment variable (internal network)
REDIS_URL=redis://default:ffszhttFptGyvkVAqChdBvOmdfsdfpgbFrwTc@telegram-bot-redis.railway.internal:6379/0
```

---

## 🔧 Environment-Specific Configuration

Create different configurations for local vs production:

### Method 1: Multiple .env Files

```powershell
# .env.local (for development)
REDIS_URL=redis://localhost:6379/0

# .env.production (for Railway)
REDIS_URL=redis://default:PASSWORD@caboose.proxy.rlwy.net:53870/0
```

Use different files:
```python
from dotenv import load_dotenv
import os

env = os.getenv('ENVIRONMENT', 'development')
env_file = '.env.local' if env == 'development' else '.env.production'
load_dotenv(env_file)
```

### Method 2: Check Environment Variable

Your `config.py` already handles this well:

```python
# src/config.py
class Config:
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Warn if using localhost in production
    if IS_PRODUCTION and "localhost" in REDIS_URL:
        print("⚠️ WARNING: Using localhost Redis in production!")
```

---

## 📊 Comparison Table

| Feature | Public URL | Local Redis |
|---------|-----------|-------------|
| **Works from localhost** | ✅ Yes | ✅ Yes |
| **Same data as production** | ✅ Yes | ❌ No |
| **Network latency** | ⚠️ Higher | ✅ None |
| **Railway bandwidth** | ⚠️ Uses quota | ✅ Free |
| **Setup complexity** | ✅ Easy | ⚠️ Need to install |
| **Offline development** | ❌ No | ✅ Yes |
| **Recommended for** | Testing with prod data | Daily development |

---

## 🎯 Recommended Setup

### For Development/Testing:
```env
# Use Railway public URL to test with real data
REDIS_URL=redis://default:ffszhttFptGyvkVAqChdBvOmdfsdfpgbFrwTc@caboose.proxy.rlwy.net:53870/0
```

### For Production (Railway):
```env
# Use internal URL (faster, free)
REDIS_URL=redis://default:ffszhttFptGyvkVAqChdBvOmdfsdfpgbFrwTc@telegram-bot-redis.railway.internal:6379/0
```

### For Daily Local Development:
```env
# Use local Redis
REDIS_URL=redis://localhost:6379/0
```

---

## 🚨 Security Considerations

### ⚠️ Important: Protect Your Redis URL

**Never commit `.env` files to git!**

Check your `.gitignore`:
```gitignore
# .gitignore
.env
.env.local
.env.production
*.env
```

### Secure Password Handling

1. **Don't share** Redis passwords publicly
2. **Rotate passwords** periodically in Railway
3. **Use environment variables** (never hardcode)
4. **Limit access** to only necessary services

---

## 🧪 Testing Your Connection

### Quick Test

```powershell
# Run the test script
python test_redis_connection.py
```

### Manual Test with redis-cli

```powershell
# Connect to Railway Redis from localhost
redis-cli -h caboose.proxy.rlwy.net -p 53870 -a ffszhttFptGyvkVAqChdBvOmdfsdfpgbFrwTc

# Once connected, test commands
> PING
PONG

> SET test "hello"
OK

> GET test
"hello"

> KEYS *
(list of all keys)

> EXIT
```

---

## 📝 Complete .env Examples

### For Localhost Development (Public URL)

```env
# Bot Configuration
BOT_TOKEN=your_telegram_bot_token

# Redis - Railway Public URL (works from localhost)
REDIS_URL=redis://default:ffszhttFptGyvkVAqChdBvOmdfsdfpgbFrwTc@caboose.proxy.rlwy.net:53870/0

# Admin Settings
ADMIN_IDS=123456789

# Dashboard
DASHBOARD_PORT=5000
DASHBOARD_HOST=0.0.0.0
ENVIRONMENT=development

# TOTP Authentication
TOTP_SECRET=
TOTP_MAX_ATTEMPTS=5
```

### For Localhost Development (Local Redis)

```env
# Bot Configuration
BOT_TOKEN=your_telegram_bot_token

# Redis - Local Instance
REDIS_URL=redis://localhost:6379/0

# Admin Settings
ADMIN_IDS=123456789

# Dashboard
DASHBOARD_PORT=5000
DASHBOARD_HOST=0.0.0.0
ENVIRONMENT=development

# TOTP Authentication
TOTP_SECRET=
TOTP_MAX_ATTEMPTS=5
```

---

## 🆘 Troubleshooting

### Error: "Connection refused"

**Cause:** Redis not running or wrong host/port

**Fix:**
```powershell
# For local Redis
docker ps  # Check if Redis container is running
docker start redis-local  # Start if stopped

# For Railway Redis
# Verify the public domain hasn't changed in Railway dashboard
```

### Error: "Authentication failed"

**Cause:** Wrong password

**Fix:**
1. Go to Railway → Redis service → Variables
2. Copy the correct password from `REDIS_PASSWORD`
3. Update your `.env` file

### Error: "Timeout"

**Cause:** Network issue or firewall

**Fix:**
1. Check your internet connection
2. Verify Railway service is running
3. Check if firewall is blocking Railway domains

### Connection Works but No Data

**Cause:** Using different Redis databases

**Fix:**
- Ensure database number matches (usually `/0` at end of URL)
- Check if you're using correct Redis instance (local vs Railway)

---

## 📋 Quick Reference

| Task | Command |
|------|---------|
| Test connection | `python test_redis_connection.py` |
| Start local Redis | `docker run -d -p 6379:6379 redis:latest` |
| Connect with CLI | `redis-cli -h HOST -p PORT -a PASSWORD` |
| Check Railway URL | Railway Dashboard → Redis → Settings → Networking |
| Get password | Railway Dashboard → Redis → Variables |

---

## ✨ Next Steps

1. **Choose your approach:**
   - Public URL for testing with prod data
   - Local Redis for daily development

2. **Update your .env file** with appropriate Redis URL

3. **Test the connection:**
   ```powershell
   python test_redis_connection.py
   ```

4. **Start your bot:**
   ```powershell
   python src/bot.py
   ```

5. **Start your dashboard:**
   ```powershell
   python admin_dashboard.py
   ```

Everything should work! 🎉
