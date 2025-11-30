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
| `/report` | Report abuse (placeholder for moderation) |

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
│   │   └── matching.py        # Pairing and state management
│   ├── db/
│   │   └── redis_client.py    # Redis connection pool
│   └── utils/
│       ├── logger.py          # Structured logging
│       └── decorators.py      # Rate limiting, etc.
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
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

### Railway.app

1. Create new project on [Railway](https://railway.app)
2. Add Redis service from marketplace
3. Connect GitHub repository
4. Add environment variables:
   - `BOT_TOKEN`
   - `REDIS_URL` (auto-provided by Railway)
5. Deploy!

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
- [ ] User statistics dashboard
- [ ] Admin panel

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
