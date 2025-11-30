# Testing Checklist

## Manual Testing

### Basic Functionality
- [ ] Bot starts without errors
- [ ] Redis connection successful
- [ ] Bot responds to `/start` command
- [ ] Welcome message displays correctly

### Queue System
- [ ] User can join queue with `/chat`
- [ ] Queue status message shows correct count
- [ ] User cannot join queue twice simultaneously
- [ ] Queue full error when MAX_QUEUE_SIZE reached
- [ ] User can leave queue with `/stop`

### Matching System
- [ ] Two users get matched when both use `/chat`
- [ ] Both users receive "Partner found" notification
- [ ] Match is created correctly in Redis
- [ ] No duplicate pairing occurs
- [ ] User states update to IN_CHAT

### Message Routing
- [ ] Text messages route correctly
- [ ] Emoji messages work
- [ ] Photo messages forward successfully
- [ ] Video messages forward successfully
- [ ] Sticker messages forward successfully
- [ ] Voice notes forward successfully
- [ ] Audio files forward successfully
- [ ] Documents forward successfully
- [ ] Video notes (round videos) forward
- [ ] GIFs/animations forward successfully
- [ ] Location sharing works
- [ ] Contact sharing works

### Chat Management
- [ ] `/stop` ends chat for sender
- [ ] Partner receives disconnect notification
- [ ] Both users return to IDLE state
- [ ] Pair mappings deleted from Redis
- [ ] Users can rejoin queue after `/stop`

### Next Command
- [ ] `/next` ends current chat
- [ ] User automatically searches for new partner
- [ ] Previous partner notified of skip
- [ ] New match works correctly
- [ ] Rate limiting prevents spam

### Error Handling
- [ ] Partner blocks bot - chat ends gracefully
- [ ] Message send failure handled properly
- [ ] User not in chat - receives appropriate message
- [ ] Redis connection failure handled
- [ ] Invalid commands ignored

### Rate Limiting
- [ ] `/chat` rate limited (5 calls/minute)
- [ ] `/next` rate limited (10 calls/minute)
- [ ] Rate limit message shows correctly
- [ ] Rate limit resets after time period

### Edge Cases
- [ ] User leaves Telegram during chat
- [ ] Both users use `/stop` simultaneously
- [ ] User spams commands
- [ ] Queue operations during high load
- [ ] Chat timeout after inactivity

### Graceful Shutdown
- [ ] Active users notified on shutdown
- [ ] Redis connections closed properly
- [ ] No data loss on restart
- [ ] Bot restarts successfully

## Load Testing

### Concurrent Users Test
```bash
# Test with 10 users
# Test with 50 users
# Test with 100 users
# Test with 500 users
# Test with 1000 users
```

### Metrics to Monitor
- [ ] CPU usage under load
- [ ] Memory usage under load
- [ ] Redis memory usage
- [ ] Message latency
- [ ] Match success rate
- [ ] Queue processing speed

## Redis Verification

### Check Data Structure
```bash
redis-cli

# Check queue
LLEN queue:waiting

# Check active pairs
KEYS pair:*

# Check user states
KEYS state:*

# Verify TTLs are set
TTL pair:123456
TTL state:123456

# Check rate limits
KEYS ratelimit:*
```

## Deployment Testing

### Docker
- [ ] `docker-compose up` works
- [ ] Bot connects to Redis container
- [ ] Logs visible with `docker-compose logs`
- [ ] Container restarts on failure
- [ ] `docker-compose down` stops cleanly

### Railway.app
- [ ] Deployment succeeds
- [ ] Environment variables configured
- [ ] Redis addon connected
- [ ] Bot shows as running
- [ ] Logs accessible

### Render.com
- [ ] Service deploys successfully
- [ ] Redis instance created
- [ ] Environment variables set
- [ ] Auto-deploy on git push works
- [ ] Logs viewable in dashboard

### VPS (systemd)
- [ ] Service file installed correctly
- [ ] Service starts with `systemctl start`
- [ ] Service auto-starts on boot
- [ ] Logs visible with `journalctl`
- [ ] Service restarts on failure

## Security Testing

- [ ] `.env` file not committed to git
- [ ] Bot token not exposed in logs
- [ ] Redis password configured (production)
- [ ] No user PII logged
- [ ] Rate limiting prevents DoS

## Performance Benchmarks

### Target Metrics
- Message routing latency: < 100ms
- Queue join operation: < 50ms
- Match creation: < 100ms
- Memory per active pair: < 10KB
- Redis memory for 1000 pairs: < 50MB

## Post-Deployment Checklist

- [ ] Bot responding in Telegram
- [ ] All commands working
- [ ] Monitoring setup complete
- [ ] Logs being collected
- [ ] Alerts configured
- [ ] Backup strategy in place
- [ ] Documentation updated
- [ ] Team notified of deployment

## Bug Report Template

When reporting issues, include:
- Bot version/commit hash
- Environment (local/docker/production)
- Steps to reproduce
- Expected behavior
- Actual behavior
- Logs (with sensitive data removed)
- Redis state (if applicable)

## Notes

- Test with at least 2 different Telegram accounts
- Test on both mobile and desktop Telegram
- Verify behavior with slow network connections
- Test during Redis restarts
- Simulate bot restarts during active chats
