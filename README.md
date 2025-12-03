# 🤖 Telegram Random Chat Bot

A production-ready, fully anonymous Telegram bot that randomly connects users for 1-to-1 conversations. Built with Python, python-telegram-bot, and Redis for scalability and reliability.

## ✨ Features

- 🎭 **Completely Anonymous** - No user identity or profile information shared
- 🔄 **Smart Matching** - Atomic queue operations prevent race conditions
- 💬 **Full Media Support** - Text, photos, videos, stickers, voice notes, documents, and more
- ⚡ **High Performance** - Redis-backed with connection pooling
- 🛡️ **Rate Limited** - Prevents spam and abuse
- 🔒 **Production Ready** - Comprehensive error handling and logging
- 📊 **Scalable** - Handles 1000+ concurrent users
- 🐳 **Docker Support** - Easy deployment with Docker Compose
- 📱 **Admin Dashboard** - Web-based monitoring and user management
- 🚫 **Ban/Unban System** - Complete moderation tools with auto-ban from reports

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Redis 7.0+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

### Local Setup

1. **Clone and setup:**
```bash
cd "d:\programming exercise\antigravity\telegram bot"
```

2. **Create virtual environment:**
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
cp .env.example .env
```

Edit `.env` and add your bot token:
```env
BOT_TOKEN=your_bot_token_from_botfather
REDIS_URL=redis://localhost:6379/0
```

5. **Start Redis:**
```bash
# Windows (using Docker)
# Download from : https://docs.docker.com/desktop/setup/install/windows-install/
docker run -d -p 6379:6379 redis:7-alpine

# Or install Redis natively
# Download from: https://github.com/microsoftarchive/redis/releases or https://redis.io/download
```

6. **Run the bot:**
```bash
python -m src.bot
```

The bot is now running! 🎉

## 📊 Admin Dashboard

The bot includes a powerful web-based admin dashboard for monitoring and managing users.

### Quick Start Dashboard

```bash
# Install dashboard dependencies (if not already installed)
pip install flask flask-cors

# Start the dashboard
python admin_dashboard.py

# Or use the startup script (Windows)
start_dashboard.bat
```

Access at: **http://localhost:5000**

### Dashboard Features

- 📈 **Real-time Statistics** - Total users, active users, queue status
- 👥 **User Management** - View all users with pagination
- 🟢 **Online Monitoring** - See currently active users
- 💬 **Chat Monitoring** - View active chat sessions and pairs
- ⏳ **Queue Status** - Monitor users waiting for matches
- 🔍 **Search Users** - Find users by ID, username, gender, country
- 📋 **User Details** - Complete profile and preference information

### Documentation

- **Quick Start:** See `DASHBOARD_QUICKSTART.md` for 5-minute setup
- **Full Guide:** See `ADMIN_DASHBOARD.md` for complete documentation

### Configuration

Add to your `.env` file:
```env
DASHBOARD_PORT=5000        # Dashboard port (default: 5000)
DASHBOARD_HOST=0.0.0.0     # Host address
```

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

1. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your BOT_TOKEN
```

2. **Start services:**
```bash
docker-compose up -d
```

3. **View logs:**
```bash
docker-compose logs -f bot
```

4. **Stop services:**
```bash
docker-compose down
```

### Manual Docker Build

```bash
docker build -t telegram-chat-bot .
docker run -d --name chat-bot --env-file .env telegram-chat-bot
```

## 📋 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and bot introduction |
| `/chat` | Join queue and find a random partner |
| `/stop` | End current chat session |
| `/next` | Skip to next partner (auto-rejoin queue) |
| `/help` | Show help and usage instructions |
| `/report` | Report abuse (triggers auto-ban after 5 reports) |

## 🛡️ Moderation System

### Ban/Unban Features

The bot includes a comprehensive moderation system for admins:

**Admin Commands:**
- `/admin` - Show admin panel with all commands
- `/ban` - Ban a user (temporary or permanent)
- `/unban` - Unban a user
- `/warn` - Add warning to a user
- `/checkban <user_id>` - Check ban status
- `/bannedlist` - View all banned users
- `/warninglist` - View users with warnings

**Features:**
- ✅ Temporary bans (1h, 24h, 7d, 30d)
- ✅ Permanent bans
- ✅ Auto-ban after 5 reports
- ✅ Warning system
- ✅ 5 ban reasons: nudity, spam, abuse, fake reports, harassment
- ✅ User notifications
- ✅ Ban history tracking

**Documentation:**
- 📖 **Quick Guide:** `ADMIN_BAN_GUIDE.md` - Admin quick reference
- 📖 **Complete Guide:** `BAN_SYSTEM.md` - Full system documentation
- 📖 **Architecture:** `BAN_SYSTEM_ARCHITECTURE.md` - Technical details
- 📖 **Testing:** `TESTING_CHECKLIST.md` - Test procedures

## 🏗️ Architecture

```
telegram-random-chat-bot/
├── src/
│   ├── bot.py                 # Main application entry point
│   ├── config.py              # Configuration management
│   ├── handlers/
│   │   ├── commands.py        # Command handlers (/start, /chat, etc.)
│   │   └── messages.py        # Message routing logic
│   ├── services/
│   │   ├── queue.py           # Queue management with Lua scripts
│   │   ├── matching.py        # Pairing and state management
│   │   └── dashboard.py       # Dashboard service layer
│   ├── db/
│   │   └── redis_client.py    # Redis connection pool
│   └── utils/
│       ├── logger.py          # Structured logging
│       └── decorators.py      # Rate limiting, etc.
├── templates/
│   └── dashboard.html         # Admin dashboard UI
├── static/
│   ├── css/
│   │   └── dashboard.css      # Dashboard styling
│   └── js/
│       └── dashboard.js       # Dashboard functionality
├── admin_dashboard.py         # Dashboard Flask application
├── start_dashboard.bat        # Dashboard startup script (Windows)
├── start_dashboard.ps1        # Dashboard startup script (PowerShell)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── ADMIN_DASHBOARD.md         # Dashboard documentation
├── DASHBOARD_QUICKSTART.md    # Dashboard quick start guide
└── README.md
```

## 🔧 Configuration

Environment variables (`.env`):

```env
# Required
BOT_TOKEN=your_bot_token_here
REDIS_URL=redis://localhost:6379/0

# Optional
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR
MAX_QUEUE_SIZE=500              # Maximum waiting queue size
MESSAGE_RATE_LIMIT=30           # Messages per minute per user
CHAT_TIMEOUT=600                # Auto-disconnect after inactivity (seconds)
NEXT_COMMAND_LIMIT=10           # Max /next commands per minute
ENVIRONMENT=development         # development or production
```

## 📊 Redis Data Structure

| Key Pattern | Type | Purpose |
|-------------|------|---------|
| `queue:waiting` | LIST | FIFO queue of waiting users |
| `pair:{user_id}` | STRING | Maps user to their partner |
| `state:{user_id}` | STRING | User state (IDLE/IN_QUEUE/IN_CHAT) |
| `ratelimit:{function}:{user_id}` | STRING | Rate limiting counters |

All keys have TTL (Time To Live) for automatic cleanup.

## 🚢 Deployment Options

### Railway.app (Recommended - No Sleep!)

**✅ Runs 24/7 with no automatic sleep**  
**✅ Perfect for Telegram bots with polling**  
**✅ Free tier: $5 credit/month (~500-600 hours)**

#### Quick Deploy (5 minutes):

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Deploy to Railway"
   git push origin main
   ```

2. **Deploy on Railway:**
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Add Redis database (+ New → Database → Redis)

3. **Set Variables:**
   - `BOT_TOKEN` - Your bot token
   - `ADMIN_IDS` - Your Telegram user ID
   - `ENVIRONMENT` - `production`

4. **Done!** Bot deploys in 2-3 minutes

📖 **Full Guide:** See `RAILWAY_DEPLOYMENT.md` for detailed instructions  
🚀 **Quick Start:** See `QUICK_DEPLOY.md` for fast deployment  
✅ **Pre-flight Check:** Run `python check_deployment.py` before deploying

### Render.com

1. Create new Web Service on [Render](https://render.com)
2. Connect repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python -m src.bot`
5. Add Redis addon
6. Configure environment variables
7. Deploy!

### Linux VPS (systemd)

1. **Install dependencies:**
```bash
sudo apt update
sudo apt install python3.11 python3-pip redis-server
```

2. **Clone and setup:**
```bash
git clone <your-repo> /opt/telegram-bot
cd /opt/telegram-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Create systemd service** (`/etc/systemd/system/telegram-bot.service`):
```ini
[Unit]
Description=Telegram Random Chat Bot
After=network.target redis.service

[Service]
Type=simple
User=botuser
WorkingDirectory=/opt/telegram-bot
Environment="BOT_TOKEN=your_token_here"
Environment="REDIS_URL=redis://localhost:6379/0"
ExecStart=/opt/telegram-bot/venv/bin/python -m src.bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

4. **Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
```

5. **View logs:**
```bash
sudo journalctl -u telegram-bot -f
```

## 🧪 Testing

### Manual Testing Checklist

- [ ] `/start` - Welcome message displays
- [ ] `/chat` - User joins queue
- [ ] Two users get matched and can exchange messages
- [ ] Text messages route correctly
- [ ] Photos/stickers/media route correctly
- [ ] `/stop` ends chat for both users
- [ ] `/next` skips to new partner
- [ ] Partner disconnect notification works
- [ ] Rate limiting prevents spam
- [ ] Queue full error when limit reached
- [ ] Bot handles partner blocking gracefully

### Load Testing

```python
# Install: pip install locust
# Create locustfile.py and run:
# locust -f locustfile.py
```

## 🐛 Troubleshooting

### Bot not starting

**Error:** `ValueError: BOT_TOKEN environment variable is required`
```bash
# Solution: Check .env file exists and has BOT_TOKEN
cat .env
```

**Error:** `redis.exceptions.ConnectionError`
```bash
# Solution: Ensure Redis is running
redis-cli ping  # Should return PONG

# Start Redis:
docker run -d -p 6379:6379 redis:7-alpine
```

### Messages not routing

**Check logs:**
```bash
# Docker
docker-compose logs -f bot

# Local
python -m src.bot  # Watch console output
```

**Check Redis connection:**
```bash
redis-cli
> KEYS *
> GET state:123456
```

### High memory usage

**Clear expired keys:**
```bash
redis-cli
> KEYS pair:*
> TTL pair:123456  # Check if keys have TTL
```

**Restart Redis:**
```bash
docker-compose restart redis
```

## 📈 Monitoring

### Key Metrics

- Active chat pairs: `redis-cli KEYS "pair:*" | wc -l`
- Queue length: `redis-cli LLEN queue:waiting`
- Bot uptime: `systemctl status telegram-bot`

### Logs

Structured JSON logs in production mode:
```json
{
  "event": "match_found",
  "user_id": 123456,
  "partner_id": 789012,
  "timestamp": "2025-11-29T10:30:45Z"
}
```

## 🔐 Security Best Practices

1. **Never commit `.env` file** - It's in `.gitignore`
2. **Use Redis password** in production:
   ```env
   REDIS_URL=redis://:password@host:port/0
   ```
3. **Enable Redis persistence** for data durability
4. **Use HTTPS** for webhook mode (if switching from polling)
5. **Implement content moderation** for production use
6. **Monitor rate limits** to prevent abuse

## 🛣️ Roadmap

### Phase 1: Core ✅
- [x] Basic matching system
- [x] Message routing
- [x] Commands (/start, /chat, /stop, /next)
- [x] Docker deployment

### Phase 2: Enhancement
- [ ] Gender/age filters
- [ ] Language preferences
- [x] User statistics dashboard
- [x] Admin panel

### Phase 3: Advanced
- [ ] AI content moderation
- [ ] Analytics and insights
- [ ] Multi-language support
- [ ] Premium features

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

MIT License - feel free to use for your own projects!

## 💬 Support

- **Issues:** Open a GitHub issue
- **Telegram:** [@YourSupportUsername](https://t.me/yourusername)

## 🙏 Acknowledgments

- Built with [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- Inspired by RandomMeetBot
- Redis for rock-solid queue management

---

**Made with ❤️ for anonymous conversations**
