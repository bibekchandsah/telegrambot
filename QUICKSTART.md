# 🚀 Quick Setup Guide

## Get Your Bot Running in 5 Minutes

### Step 1: Get Bot Token
1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow instructions
3. Copy your bot token (looks like: `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`)

### Step 2: Setup Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env and paste your token
notepad .env  # Windows
# nano .env    # Linux/Mac
```

Your `.env` should look like:
```env
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
REDIS_URL=redis://localhost:6379/0
```

### Step 3: Start with Docker (Easiest)
```bash
docker-compose up -d
```

That's it! Your bot is running. 🎉

**View logs:**
```bash
docker-compose logs -f bot
```

**Stop bot:**
```bash
docker-compose down
```

### Alternative: Run Locally

**Install Python dependencies:**
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

**Start Redis (using Docker):**
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**Run bot:**
```bash
python -m src.bot
```

## Testing Your Bot

1. Open Telegram and find your bot (search for the username you gave BotFather)
2. Send `/start` - you should see a welcome message
3. Open your bot in another account or ask a friend
4. Both users send `/chat`
5. You should be matched! Try sending messages

## Common Issues

**"Redis connection failed"**
- Make sure Redis is running: `docker ps` (should see redis container)
- Or start it: `docker run -d -p 6379:6379 redis:7-alpine`

**"Bot token is invalid"**
- Check your `.env` file has the correct token from BotFather
- Make sure there are no extra spaces or quotes

**Bot not responding**
- Check logs: `docker-compose logs bot`
- Verify bot is running: `docker-compose ps`

## What's Next?

Check the main [README.md](README.md) for:
- Full deployment instructions
- Production hosting (Railway, Render, VPS)
- Advanced configuration
- Troubleshooting guide

## Need Help?

- Read the [README.md](README.md) for detailed documentation
- Check [instruction.md](instruction.md) for the full specification
- Open an issue on GitHub

Happy chatting! 🎭💬
