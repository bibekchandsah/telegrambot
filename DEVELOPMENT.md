# 🔧 Development Guide

## Setting Up Development Environment

### 1. Clone and Install

```bash
cd "d:\programming exercise\antigravity\telegram bot"

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Development Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your development bot token
notepad .env
```

**Recommended: Create a separate development bot**
- Go to [@BotFather](https://t.me/BotFather)
- Create a new bot for testing (`/newbot`)
- Use this token in your `.env` file
- Never use production bot token for development!

### 3. Start Redis

```bash
# Using Docker (recommended)
docker run -d -p 6379:6379 --name redis-dev redis:7-alpine

# Or install Redis locally on Windows
# Download from: https://github.com/microsoftarchive/redis/releases
```

### 4. Run the Bot

```bash
python -m src.bot
```

## Code Style Guidelines

### Python Style
- Follow PEP 8
- Use type hints where possible
- Docstrings for all functions
- Max line length: 88 (Black formatter default)

### Example:
```python
async def find_partner(self, user_id: int) -> Optional[int]:
    """
    Find a chat partner for the user.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        Partner ID if found, None if added to queue
    """
    pass
```

## Project Architecture

### Adding New Commands

1. **Define handler in `src/handlers/commands.py`:**
```python
async def new_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /new command."""
    user_id = update.effective_user.id
    await update.message.reply_text("New command response")
```

2. **Register in `src/bot.py`:**
```python
application.add_handler(CommandHandler("new", new_command))
```

### Adding New Features

1. **Business logic goes in `src/services/`**
2. **Database operations in `src/db/redis_client.py`**
3. **Utilities in `src/utils/`**
4. **Configuration in `src/config.py`**

## Testing Locally

### Manual Testing

1. **Start the bot**
2. **Use 2 Telegram accounts:**
   - Your main account
   - Telegram Web or another device
3. **Test scenarios from `TESTING.md`**

### Redis Inspection

```bash
# Connect to Redis
redis-cli

# View queue
LLEN queue:waiting
LRANGE queue:waiting 0 -1

# View active pairs
KEYS pair:*
GET pair:123456

# View user states
KEYS state:*
GET state:123456

# Check TTLs
TTL pair:123456
TTL state:123456

# Clear all data (development only!)
FLUSHDB
```

### Debugging Tips

1. **Enable debug logging:**
```env
LOG_LEVEL=DEBUG
```

2. **Add debug statements:**
```python
logger.debug("debugging_info", user_id=user_id, state=state)
```

3. **Check bot updates:**
```python
# Add to handler
logger.info("update_received", update=update.to_dict())
```

## Common Development Tasks

### Add Rate Limiting to Command

```python
from src.utils.decorators import rate_limit

@rate_limit(max_calls=5, period=60)
async def my_command(update, context):
    pass
```

### Add User State Requirement

```python
from src.utils.decorators import require_state

@require_state("IN_CHAT")
async def chat_only_command(update, context):
    pass
```

### Add New Redis Operation

In `src/db/redis_client.py`:
```python
async def custom_operation(self, key: str) -> any:
    """Your custom Redis operation."""
    try:
        return await self.client.custom_command(key)
    except RedisError as e:
        logger.error("custom_error", key=key, error=str(e))
        raise
```

## Deployment Workflow

### Development → Staging → Production

1. **Development:**
```bash
# Local testing
python -m src.bot
```

2. **Staging (Docker):**
```bash
# Build and test with Docker
docker-compose up --build
```

3. **Production:**
```bash
# Push to GitHub
git add .
git commit -m "feat: new feature"
git push origin main

# Railway/Render auto-deploys
```

## Git Workflow

### Branch Strategy

```
main (production)
  ↑
  └── develop (staging)
        ↑
        ├── feature/add-filters
        ├── feature/add-analytics
        └── bugfix/message-routing
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add gender filter
fix: message routing for stickers
docs: update README
refactor: simplify queue logic
test: add matching tests
```

## Performance Profiling

### Memory Usage

```python
import tracemalloc

tracemalloc.start()
# ... your code ...
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
```

### Timing Operations

```python
import time

start = time.time()
await matching.find_partner(user_id)
elapsed = time.time() - start
logger.info("operation_timing", operation="find_partner", elapsed_ms=elapsed*1000)
```

## Environment Variables

### Development `.env`
```env
BOT_TOKEN=your_dev_bot_token
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=DEBUG
ENVIRONMENT=development
```

### Production `.env`
```env
BOT_TOKEN=your_prod_bot_token
REDIS_URL=redis://:password@host:port/0
LOG_LEVEL=INFO
ENVIRONMENT=production
```

## Troubleshooting Development Issues

### Issue: ImportError

**Problem:** `ModuleNotFoundError: No module named 'src'`

**Solution:**
```bash
# Make sure you're in the project root
cd "d:\programming exercise\antigravity\telegram bot"

# Run as module
python -m src.bot
```

### Issue: Redis Connection Failed

**Problem:** `redis.exceptions.ConnectionError`

**Solution:**
```bash
# Check Redis is running
docker ps | findstr redis

# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Test connection
redis-cli ping
```

### Issue: Bot Not Responding

**Solution:**
1. Check bot token is correct
2. Verify bot is running (check logs)
3. Check network connectivity
4. Ensure no firewall blocking

### Issue: Messages Not Routing

**Debug steps:**
```python
# Add logging in messages.py
logger.info("message_details", 
    sender=sender_id,
    partner=partner_id,
    message_type=type(update.message))
```

## IDE Setup

### VS Code

**Recommended Extensions:**
- Python (Microsoft)
- Pylance
- Docker
- GitLens
- Better Comments

**settings.json:**
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  }
}
```

### PyCharm

1. **Create Python Interpreter:** Settings → Project → Python Interpreter
2. **Enable type checking:** Settings → Editor → Inspections → Python
3. **Set run configuration:** Run → Edit Configurations → Add Python

## Code Review Checklist

Before submitting PR:

- [ ] Code follows style guidelines
- [ ] All functions have docstrings
- [ ] Type hints added
- [ ] Error handling implemented
- [ ] Logging added for important operations
- [ ] No hardcoded values (use config)
- [ ] No secrets in code
- [ ] Manual testing completed
- [ ] Redis data structures documented
- [ ] Performance impact considered

## Useful Commands

```bash
# Format code
black src/

# Check style
pylint src/

# Type checking
mypy src/

# Count lines of code
Get-ChildItem -Recurse -Include *.py | Select-String . | Measure-Object

# Find TODOs
Get-ChildItem -Recurse -Include *.py | Select-String "TODO"

# Search for pattern
Get-ChildItem -Recurse -Include *.py | Select-String "pattern"
```

## Resources

### Documentation
- [python-telegram-bot docs](https://docs.python-telegram-bot.org/)
- [Redis commands](https://redis.io/commands)
- [Telegram Bot API](https://core.telegram.org/bots/api)

### Tools
- [Redis GUI](https://github.com/qishibo/AnotherRedisDesktopManager)
- [Postman for testing](https://www.postman.com/)
- [ngrok for webhooks](https://ngrok.com/)

### Learning
- [Async Python](https://realpython.com/async-io-python/)
- [Redis patterns](https://redis.io/topics/patterns)
- [Telegram bot best practices](https://core.telegram.org/bots/tutorial)

## Getting Help

1. **Check documentation first** - README.md, QUICKSTART.md
2. **Search issues** - GitHub issues
3. **Check logs** - Enable DEBUG level
4. **Ask in discussions** - GitHub discussions
5. **Stack Overflow** - Tag with `python-telegram-bot`

## Contributing

See main README.md for contribution guidelines.

## License

MIT License - See LICENSE file
