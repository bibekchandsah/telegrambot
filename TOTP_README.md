# 🔐 Admin Dashboard - TOTP Authentication

## What's New?

The admin dashboard is now secured with **Two-Factor Authentication (TOTP)**!

### ✨ Features

- 🔒 **Secure TOTP-based 2FA** - Only authorized admins can access
- 📱 **QR Code Setup** - Easy first-time configuration
- 🔢 **6-Digit Codes** - Standard TOTP authentication
- ⚡ **Attempt Limiting** - Configurable max failed attempts
- 🎯 **Session Management** - Stay logged in during your session

## 🚀 Quick Start

### 1. Install New Dependencies
```bash
pip install -r requirements.txt
```

New packages added:
- `pyotp==2.9.0` - TOTP authentication
- `qrcode==7.4.2` - QR code generation
- `pillow==10.1.0` - Image processing

### 2. First Run (No Configuration Needed!)
```bash
python admin_dashboard.py
```

### 3. Visit Login Page
```
http://localhost:5000/login
```

### 4. Scan QR Code
- You'll see a QR code on the screen
- Scan it with your authenticator app (Google Authenticator, Authy, etc.)
- Save the secret key shown below the QR code

### 5. Add Secret to .env
```env
TOTP_SECRET=YOUR_SECRET_FROM_QR_CODE
```

### 6. Restart and Login!
```bash
python admin_dashboard.py
```

Now enter your 6-digit code to access the dashboard! 🎉

## 📖 Documentation

- **Quick Start:** See [TOTP_QUICKSTART.md](TOTP_QUICKSTART.md)
- **Full Guide:** See [TOTP_AUTH_GUIDE.md](TOTP_AUTH_GUIDE.md)

## 🔧 Configuration

### Environment Variables (.env)

```env
# Required after first setup
TOTP_SECRET=

# Optional (default: 5)
TOTP_MAX_ATTEMPTS=5

# Optional (auto-generated if not set)
SESSION_SECRET=
```

### Default Settings
- **Max Attempts:** 5 failed attempts before lockout
- **Code Validity:** 30 seconds per code
- **Session:** Expires when browser closes

## 🆘 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Invalid code | Check device time sync |
| Dashboard locked | Restart the dashboard |
| Lost authenticator | Use backup secret key |
| QR not showing | Remove TOTP_SECRET from .env |

## 🔐 Security Features

### What's Protected?
✅ Dashboard homepage (`/`)  
✅ All API endpoints (`/api/*`)  
✅ Settings and configuration  
✅ User management  
✅ Reports and moderation  

### What's Public?
❌ Login page (`/login`)  
❌ Logout endpoint (`/logout`)  
❌ Health check (`/health`)  

## 📱 Compatible Authenticator Apps

- **Google Authenticator** (iOS/Android)
- **Microsoft Authenticator** (iOS/Android)
- **Authy** (iOS/Android/Desktop)
- **1Password** (with TOTP support)
- Any RFC 6238 compatible TOTP app

## 🎯 Usage Flow

```
┌─────────────────┐
│ Start Dashboard │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Visit /login   │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  First time?    │
│  QR Code shown  │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Scan with app   │
│ Add to .env     │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Restart & Login │
│ Enter 6 digits  │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Access Dashboard│
└─────────────────┘
```

## 🛡️ Security Best Practices

✅ **DO:**
- Keep TOTP_SECRET private and secure
- Use strong SESSION_SECRET in production
- Backup your secret key safely
- Enable automatic time sync on devices

❌ **DON'T:**
- Share your TOTP secret
- Commit .env to version control
- Store secrets in plain text
- Use same secret across projects

## 🔄 Migration from Old Version

Already running the dashboard without TOTP?

1. Install new dependencies: `pip install -r requirements.txt`
2. Run dashboard - QR code will show automatically
3. Scan QR and add to .env
4. Restart
5. Done! ✅

## 💡 Tips

- **Codes change every 30 seconds** - If one doesn't work, wait for the next
- **Save your secret key** - You'll need it if you lose your phone
- **Time matters** - TOTP depends on accurate system time
- **5 attempts** - Default limit before lockout (configurable)

## 🎉 That's All!

Your admin dashboard is now secured with industry-standard TOTP authentication!

---

**Need Help?**
- Read [TOTP_QUICKSTART.md](TOTP_QUICKSTART.md) for step-by-step setup
- Read [TOTP_AUTH_GUIDE.md](TOTP_AUTH_GUIDE.md) for detailed documentation
- Check troubleshooting section for common issues

**Questions?**
Open an issue or check the documentation files.
