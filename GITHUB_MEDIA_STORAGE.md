# GitHub Media Storage Feature

## Overview
This feature automatically uploads photos, stickers, GIFs, and documents shared by users to a GitHub repository. This allows admins to review potentially abusive content when users report violations.

## Configuration

### Environment Variables
Add these to your `.env` file:

```env
# GitHub Repository URL
GITHUB_REPO=https://github.com/bibekchandsah/webservicelogs
GITHUB_BRANCH=main
GITHUB_TOKEN=your_github_personal_access_token

# Storage Paths
GITHUB_PATH=webservicelogs/meetgrid bot/
MEETGRID_PHOTOS=webservicelogs/meetgrid bot/photos/
MEETGRID_STICKERS=webservicelogs/meetgrid bot/stickers/
MEETGRID_GIFS=webservicelogs/meetgrid bot/gifs/
MEETGRID_DOCUMENTS=webservicelogs/meetgrid bot/documents/
```

### GitHub Token Setup

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a name (e.g., "Meetgrid Bot Media Upload")
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
5. Generate token and copy it to your `.env` file

### Repository Structure

```
webservicelogs/
└── meetgrid bot/
    ├── photos/          # User photos
    ├── stickers/        # Stickers
    ├── gifs/           # GIFs and animations
    └── documents/      # Documents and files
```

## How It Works

### Automatic Upload Process

1. **User sends media** during chat (photo, sticker, GIF, or document)
2. **Bot intercepts** the media before forwarding to partner
3. **Downloads** the file from Telegram servers
4. **Checks file size** (max 100 MB for GitHub)
5. **Uploads to GitHub** with naming format: `{user_id}_{timestamp}_{original_filename}`
6. **Logs GitHub URL** in Shared Data tab for admin review
7. **Forwards media** to chat partner

### File Naming Convention

Files are named with this format:
```
{user_id}_{timestamp}_{filename}
```

Example:
```
721000596_20251204_104930_photo_abc123.jpg
```

### Size Limits

- **Maximum file size**: 100 MB
- Files larger than 100 MB are **not uploaded** (logged as warning)
- User can still send the file, but it won't be stored on GitHub

## Admin Dashboard Integration

### Shared Data Tab

The dashboard shows all shared media with:
- 📷 **Photo** - Blue badge
- 🎨 **Sticker** - Orange badge
- 🎬 **GIF** - Blue badge
- 📄 **Document** - Red badge
- 🔗 **URL** - Blue badge (text-based)
- 📞 **Contact** - Orange badge (phone numbers)
- 📍 **Location** - Green badge (GPS coordinates)

### Viewing Media

1. Open admin dashboard
2. Navigate to "📤 Shared Data" tab
3. Click "🔄 Refresh" to load latest data
4. Click "View on GitHub" link to see the media file
5. Review content and take appropriate action if abusive

## Security Considerations

### Token Security
- ⚠️ **Never commit** the GitHub token to your repository
- ⚠️ Keep `.env` in `.gitignore`
- ⚠️ Rotate tokens periodically
- ⚠️ Use a dedicated repository for media storage

### Repository Visibility
- Consider using a **private repository** for sensitive content
- Limit repository access to admin team only
- Enable branch protection rules

### Data Retention
- Implement periodic cleanup of old files
- Consider GDPR compliance for user data
- Store only necessary media for moderation

## Testing

### Local Testing
```bash
# Make sure GitHub credentials are in .env
python src/bot.py
```

### Verify Upload
1. Send a photo/sticker/GIF/document in a test chat
2. Check bot logs for `github_upload_success`
3. Open GitHub repository to verify file uploaded
4. Check dashboard Shared Data tab for entry

## Troubleshooting

### Upload Fails
- Check GitHub token is valid and has `repo` scope
- Verify repository exists and bot has write access
- Check file size is under 100 MB
- Review logs for specific error messages

### Files Not Appearing
- Ensure GitHub uploader is configured (check bot startup logs)
- Verify users are in active chat (not sending to bot directly)
- Check Redis connection is working
- Refresh dashboard after sending media

### Common Errors

**"'RedisClient' object has no attribute 'zadd'"**
- Update `redis_client.py` with sorted set methods

**"GitHub API error: 401"**
- Token is invalid or expired
- Generate new token with correct permissions

**"File size exceeds 100MB limit"**
- File is too large for GitHub
- Consider using alternative storage (AWS S3, etc.)

## Performance Considerations

- Uploads happen **asynchronously** (non-blocking)
- Failed uploads are logged but don't stop message routing
- Large files may take longer to upload
- Consider implementing upload queue for high traffic

## Future Enhancements

- [ ] Add image compression before upload
- [ ] Implement automatic NSFW detection
- [ ] Add batch deletion of old files
- [ ] Support alternative storage providers (S3, Cloudflare R2)
- [ ] Add admin bulk download feature
- [ ] Implement file hash checking to avoid duplicates
