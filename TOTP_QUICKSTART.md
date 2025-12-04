# TOTP Authentication - Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

This installs the new TOTP packages:
- `pyotp` - For TOTP generation
- `qrcode` - For QR code generation  
- `pillow` - For image processing

### Step 2: First Time Run
```bash
python admin_dashboard.py
```

### Step 3: Visit Login Page
Open your browser and go to:
```
http://localhost:5000/login
```

### Step 4: Scan QR Code
You'll see a **QR code** on the screen:

1. Open your authenticator app:
   - **Google Authenticator** (iOS/Android)
   - **Microsoft Authenticator**
   - **Authy**
   - Or any TOTP app

2. **Scan the QR code** shown on screen

3. Your app will show a 6-digit code that changes every 30 seconds

### Step 5: Save the Secret Key
Below the QR code, you'll see a secret key like:
```
JBSWY3DPEHPK3PXP
```

**IMPORTANT:** Save this somewhere safe! You'll need it if you lose your phone.

### Step 6: Update .env File
Add the secret to your `.env` file:
```env
TOTP_SECRET=JBSWY3DPEHPK3PXP
```

### Step 7: Restart Dashboard
```bash
# Stop the running dashboard (Ctrl+C)
python admin_dashboard.py
```

### Step 8: Login
1. Go to `http://localhost:5000/login`
2. Enter the 6-digit code from your authenticator app
3. Click "Verify & Login"
4. ✅ You're in!

---

## 🔐 Daily Usage

### Logging In
1. Visit `http://localhost:5000/login`
2. Get code from authenticator app
3. Enter 6-digit code
4. Done!

### Codes Update Every 30 Seconds
- If code doesn't work, wait for next one
- You have 5 attempts before lockout
- Restart dashboard to reset attempts

---

## ⚙️ Configuration Options

### Optional Settings in .env:

```env
# Change max login attempts (default: 5)
TOTP_MAX_ATTEMPTS=10

# Set custom session secret (recommended for production)
SESSION_SECRET=your-random-secret-here
```

### Generate Secure Session Secret:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🆘 Troubleshooting

### "Invalid code" Error
- ✅ Check your device time is correct (Settings → Date & Time → Automatic)
- ✅ Wait for next code (they expire every 30 seconds)
- ✅ Make sure you scanned the right QR code

### Dashboard Locked (5 Failed Attempts)
- ✅ Restart: `Ctrl+C` then `python admin_dashboard.py`
- ✅ Counter resets on restart

### Lost Authenticator App
- ✅ Use backup secret key from step 5
- ✅ Add to new authenticator app manually
- ⚠️ Or remove `TOTP_SECRET` from .env (generates new QR, old codes won't work)

---

## 📱 Recommended Authenticator Apps

### iOS
- Google Authenticator (Free)
- Microsoft Authenticator (Free)
- Authy (Free, cloud backup)

### Android  
- Google Authenticator (Free)
- Microsoft Authenticator (Free)
- Authy (Free, cloud backup)
- andOTP (Free, open source)

---

## 🔒 Security Tips

✅ **DO:**
- Keep your secret key backed up securely
- Use strong SESSION_SECRET in production
- Enable device time sync

❌ **DON'T:**
- Share your TOTP secret with anyone
- Commit .env file to git
- Screenshot QR codes and share them

---

## 📋 What Changed?

### Before TOTP
```
Visit dashboard → Dashboard loads
```

### After TOTP
```
Visit dashboard → Login page → Enter TOTP code → Dashboard loads
```

### Protected Routes
All dashboard and API routes now require authentication:
- ✅ `/` (dashboard)
- ✅ `/api/*` (all API endpoints)
- ❌ `/login` (public)
- ❌ `/logout` (public)
- ❌ `/health` (public)

---

## 🎯 Complete .env Example

```env
# Bot Config
BOT_TOKEN=your_telegram_bot_token
REDIS_URL=redis://localhost:6379/0
ADMIN_IDS=123456789

# Dashboard
DASHBOARD_PORT=5000
DASHBOARD_HOST=0.0.0.0
ENVIRONMENT=development

# TOTP (Add after first run)
TOTP_SECRET=
TOTP_MAX_ATTEMPTS=5
SESSION_SECRET=
```

---

## ✨ That's It!

You now have a secure, TOTP-protected admin dashboard! 🎉

For detailed documentation, see: **TOTP_AUTH_GUIDE.md**
