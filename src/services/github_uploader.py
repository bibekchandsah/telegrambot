"""GitHub uploader service for media files."""
import base64
import aiohttp
import os
from typing import Optional, Tuple
from datetime import datetime
from src.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GitHubUploader:
    """Service to upload media files to GitHub repository."""
    
    def __init__(self):
        """Initialize GitHub uploader."""
        self.repo = Config.GITHUB_REPO
        self.branch = Config.GITHUB_BRANCH
        self.token = Config.GITHUB_TOKEN
        self.max_size = Config.MAX_GITHUB_FILE_SIZE
        
        # Extract owner and repo name from URL
        # Format: https://github.com/owner/repo
        if self.repo:
            parts = self.repo.rstrip('/').split('/')
            self.owner = parts[-2] if len(parts) >= 2 else ""
            self.repo_name = parts[-1] if len(parts) >= 1 else ""
        else:
            self.owner = ""
            self.repo_name = ""
    
    def is_configured(self) -> bool:
        """Check if GitHub upload is configured."""
        return bool(self.repo and self.token and self.owner and self.repo_name)
    
    async def upload_file(
        self,
        file_content: bytes,
        user_id: int,
        filename: str,
        media_type: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Upload file to GitHub repository.
        
        Args:
            file_content: File content as bytes
            user_id: Telegram user ID
            filename: Original filename
            media_type: Type of media (photo, sticker, gif, document)
            
        Returns:
            Tuple of (success: bool, file_url: Optional[str])
        """
        if not self.is_configured():
            logger.warning("github_upload_not_configured")
            return False, None
        
        try:
            # Check file size
            file_size = len(file_content)
            if file_size > self.max_size:
                logger.warning(
                    "file_too_large",
                    user_id=user_id,
                    size_mb=file_size / (1024 * 1024),
                    max_mb=self.max_size / (1024 * 1024)
                )
                return False, "File size exceeds 100MB limit"
            
            # Get appropriate path based on media type
            path_map = {
                'photo': Config.MEETGRID_PHOTOS,
                'sticker': Config.MEETGRID_STICKERS,
                'gif': Config.MEETGRID_GIFS,
                'document': Config.MEETGRID_DOCUMENTS,
                'animation': Config.MEETGRID_GIFS,
            }
            
            base_path = path_map.get(media_type, Config.GITHUB_PATH)
            
            # Create filename with user_id prefix and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{user_id}_{timestamp}_{filename}"
            file_path = f"{base_path}{safe_filename}"
            
            # Encode content to base64
            content_base64 = base64.b64encode(file_content).decode('utf-8')
            
            # Prepare GitHub API request
            api_url = f"https://api.github.com/repos/{self.owner}/{self.repo_name}/contents/{file_path}"
            
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json"
            }
            
            # Check if file exists (to get SHA for update)
            async with aiohttp.ClientSession() as session:
                # Try to get existing file
                async with session.get(api_url, headers=headers) as response:
                    sha = None
                    if response.status == 200:
                        existing = await response.json()
                        sha = existing.get('sha')
                
                # Prepare payload
                payload = {
                    "message": f"Upload {media_type} from user {user_id}",
                    "content": content_base64,
                    "branch": self.branch
                }
                
                if sha:
                    payload["sha"] = sha
                
                # Upload file
                async with session.put(api_url, headers=headers, json=payload) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        file_url = result.get('content', {}).get('html_url')
                        
                        logger.info(
                            "github_upload_success",
                            user_id=user_id,
                            media_type=media_type,
                            filename=safe_filename,
                            size_kb=file_size / 1024
                        )
                        
                        return True, file_url
                    else:
                        error_text = await response.text()
                        logger.error(
                            "github_upload_failed",
                            user_id=user_id,
                            status=response.status,
                            error=error_text
                        )
                        return False, f"GitHub API error: {response.status}"
        
        except Exception as e:
            logger.error(
                "github_upload_error",
                user_id=user_id,
                media_type=media_type,
                error=str(e)
            )
            return False, str(e)
    
    async def download_telegram_file(
        self,
        bot,
        file_id: str,
        file_size: Optional[int] = None
    ) -> Optional[bytes]:
        """
        Download file from Telegram.
        
        Args:
            bot: Telegram bot instance
            file_id: Telegram file ID
            file_size: File size in bytes (optional, for pre-check)
            
        Returns:
            File content as bytes or None if failed
        """
        try:
            # Check size before downloading
            if file_size and file_size > self.max_size:
                logger.warning(
                    "telegram_file_too_large",
                    file_id=file_id,
                    size_mb=file_size / (1024 * 1024)
                )
                return None
            
            # Get file from Telegram
            file = await bot.get_file(file_id)
            
            # Download file content
            file_bytes = await file.download_as_bytearray()
            
            return bytes(file_bytes)
        
        except Exception as e:
            logger.error(
                "telegram_file_download_error",
                file_id=file_id,
                error=str(e)
            )
            return None
