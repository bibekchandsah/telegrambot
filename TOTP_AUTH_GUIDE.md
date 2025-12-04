# Admin Dashboard TOTP Authentication Guide

## Overview

The admin dashboard is now protected with **Time-based One-Time Password (TOTP)** authentication for enhanced security. This ensures only authorized administrators can access the dashboard.

## Features

✅ **Secure TOTP-based 2FA authentication**  
✅ **QR code generation for easy setup**  
✅ **Configurable maximum login attempts (default: 5)**  
✅ **Session-based authentication**  
✅ **First-time setup with visual QR code**  
✅ **Manual secret key display for backup**  

---

## Setup Instructions

### First Time Setup

When you first run the admin dashboard **without** a `TOTP_SECRET` configured in your `.env` file:

1. **Start the dashboard:**
   ```bash
   python admin_dashboard.py
   ```

2. **Visit the login page:**
   ```
   http://localhost:5000/login
   ```

3. **You'll see:**
   - A QR code displayed on the screen
   - A secret key shown below the QR code
   - Instructions for setup

4. **Scan the QR code** with your authenticator app:
   - Google Authenticator (iOS/Android)
   - Microsoft Authenticator
   - Authy
   - Any TOTP-compatible app

5. **Save the secret key** somewhere secure (password manager, encrypted note, etc.)

6. **Add to `.env` file:**
   ```env
   TOTP_SECRET=YOUR_GENERATED_SECRET_HERE
   ```

7. **Restart the dashboard** to apply the changes

---

## Environment Variables

Add these to your `.env` file:

```env
# TOTP Authentication (Required after first setup)
TOTP_SECRET=YOUR_SECRET_KEY_HERE

# Maximum login attempts before lockout (Optional, default: 5)
TOTP_MAX_ATTEMPTS=5

# Session secret for Flask sessions (Optional, auto-generated if not set)
SESSION_SECRET=your_random_secret_key_here
```

### Configuration Options

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `TOTP_SECRET` | Your TOTP secret key | Auto-generated on first run | Yes (after setup) |
| `TOTP_MAX_ATTEMPTS` | Max failed login attempts | 5 | No |
| `SESSION_SECRET` | Flask session encryption key | Auto-generated | No |

---

## Usage

### Logging In

1. **Visit:** `http://localhost:5000/login`
2. **Open your authenticator app** and get the 6-digit code
3. **Enter the code** in the input field
4. **Click "Verify & Login"**

### Login Attempts

- You have **5 attempts** by default (configurable via `TOTP_MAX_ATTEMPTS`)
- After 5 failed attempts, the dashboard locks
- To unlock, **restart the dashboard**
- Failed attempt counter resets on successful login

### Logging Out

- Click the logout button (if implemented in UI)
- Or visit: `http://localhost:5000/logout`
- Session expires when browser closes

---

## Security Features

### 🔒 What's Protected

All dashboard routes require authentication **except**:
- `/login` - Login page
- `/logout` - Logout endpoint  
- `/health` - Health check endpoint

### 🛡️ Security Measures

1. **Time-based OTP**: Codes expire every 30 seconds
2. **Valid window**: Accepts codes within 30-second tolerance
3. **Attempt limiting**: Configurable max attempts before lockout
4. **Session management**: Secure Flask sessions with secret key
5. **Auto-lockout**: Dashboard locks after max failed attempts

### ⚠️ Security Best Practices

✅ **DO:**
- Keep your `TOTP_SECRET` secure and private
- Use a strong `SESSION_SECRET` in production
- Store the secret key in a password manager
- Backup your authenticator app or secret key
- Use environment variables for secrets (never commit to git)

❌ **DON'T:**
- Share your TOTP secret with anyone
- Commit `.env` file to version control
- Use the same secret across multiple dashboards
- Store secrets in plain text files

---

## Troubleshooting

### Problem: "Invalid code" error

**Solutions:**
- Ensure your device time is synced (TOTP depends on accurate time)
- Wait for the next code (codes expire every 30 seconds)
- Check that you scanned the correct QR code
- Verify the secret key matches in your `.env` file

### Problem: Dashboard locked after 5 attempts

**Solution:**
- Restart the dashboard: `Ctrl+C` then run `python admin_dashboard.py` again
- The counter resets on restart

### Problem: QR code not showing on first run

**Check:**
- Ensure `TOTP_SECRET` is NOT set in `.env`
- Check console logs for any errors
- Verify `pyotp` and `qrcode` packages are installed

### Problem: Lost authenticator app access

**Recovery:**
1. Find your backed-up secret key
2. Add it to a new authenticator app manually
3. Or remove `TOTP_SECRET` from `.env` to regenerate (⚠️ old codes won't work)

---

## Installation Requirements

Install the required packages:

```bash
pip install -r requirements.txt
```

**New dependencies added:**
- `pyotp==2.9.0` - TOTP generation and verification
- `qrcode==7.4.2` - QR code generation
- `pillow==10.1.0` - Image processing for QR codes

---

## API Protection

All API endpoints are now protected with the `@require_auth` decorator:

```python
@app.route('/api/stats')
@require_auth
def get_stats():
    # Protected endpoint
    ...
```

**Unauthenticated requests** will be redirected to `/login`.

---

## Example `.env` Configuration

```env
# Bot Configuration
BOT_TOKEN=your_telegram_bot_token
REDIS_URL=redis://localhost:6379/0

# Admin IDs
ADMIN_IDS=123456789,987654321

# Dashboard Settings
DASHBOARD_PORT=5000
DASHBOARD_HOST=0.0.0.0
ENVIRONMENT=production

# TOTP Authentication
TOTP_SECRET=JBSWY3DPEHPK3PXP
TOTP_MAX_ATTEMPTS=5
SESSION_SECRET=your-secret-session-key-here
```

---

## Technical Details

### TOTP Algorithm

- **Algorithm:** SHA-1 (standard TOTP)
- **Time step:** 30 seconds
- **Code length:** 6 digits
- **Valid window:** ±1 time step (30 seconds before/after)

### Session Management

- Sessions are stored server-side using Flask's session management
- Session data is encrypted with `SESSION_SECRET`
- Sessions expire when browser closes (`session.permanent = False`)

### Authentication Flow

```
User visits /dashboard
    ↓
Check session['authenticated']
    ↓
If False → Redirect to /login
    ↓
User enters TOTP code
    ↓
Verify code with pyotp
    ↓
If valid → Set session['authenticated'] = True
    ↓
Redirect to dashboard
```

---

## Migration from Old Dashboard

If you're upgrading from a version without TOTP:

1. **Install new dependencies:**
   ```bash
   pip install pyotp qrcode pillow
   ```

2. **First login will show QR code** (no `.env` changes needed yet)

3. **Scan QR and add secret to `.env`**

4. **Restart dashboard**

5. Done! 🎉

---

## Support

If you encounter issues:

1. Check the console logs for detailed error messages
2. Verify all environment variables are set correctly
3. Ensure system time is accurate (critical for TOTP)
4. Check that all dependencies are installed

---

## Changelog

### Version 2.0 - TOTP Authentication
- ✅ Added TOTP-based 2FA authentication
- ✅ QR code generation for first-time setup
- ✅ Configurable max login attempts
- ✅ Session-based authentication
- ✅ Protected all API endpoints
- ✅ Added login/logout routes
- ✅ Professional login UI

---

## License

This authentication system is part of the Telegram Bot Admin Dashboard project.
