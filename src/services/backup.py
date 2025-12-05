"""Redis backup and restore service."""
import json
import gzip
import os
import base64
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from src.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BackupService:
    """Service for backing up and restoring Redis data."""
    
    def __init__(self, redis_client):
        """Initialize backup service.
        
        Args:
            redis_client: RedisClient instance
        """
        self.redis = redis_client
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # GitHub configuration
        self.github_enabled = bool(Config.GITHUB_REPO and Config.GITHUB_TOKEN)
        if self.github_enabled:
            parts = Config.GITHUB_REPO.rstrip('/').split('/')
            self.github_owner = parts[-2] if len(parts) >= 2 else ""
            self.github_repo = parts[-1] if len(parts) >= 1 else ""
            self.github_token = Config.GITHUB_TOKEN
            self.github_branch = Config.GITHUB_BRANCH
            self.github_backup_path = Config.MEETGRID_BACKUPS
        else:
            logger.info("GitHub backup storage not configured - using local storage only")
    
    async def create_backup(self, compress: bool = True) -> Dict[str, Any]:
        """Create a complete backup of all Redis data.
        
        Args:
            compress: Whether to compress the backup file
            
        Returns:
            Dict containing backup info (filename, size, timestamp, keys_count)
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_data = {
                "timestamp": timestamp,
                "created_at": datetime.now().isoformat(),
                "data": {}
            }
            
            # Get all keys using SCAN to avoid blocking
            cursor = 0
            all_keys = []
            while True:
                cursor, keys = await self.redis.client.scan(
                    cursor=cursor,
                    count=100
                )
                all_keys.extend(keys)
                if cursor == 0:
                    break
            
            logger.info(f"Found {len(all_keys)} keys to backup")
            
            # Backup each key with its type and value
            for key in all_keys:
                try:
                    key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                    
                    # Get key type
                    key_type = await self.redis.client.type(key)
                    key_type = key_type.decode('utf-8') if isinstance(key_type, bytes) else key_type
                    
                    # Get TTL
                    ttl = await self.redis.client.ttl(key)
                    
                    # Get value based on type
                    value = await self._get_key_value(key, key_type)
                    
                    backup_data["data"][key_str] = {
                        "type": key_type,
                        "value": value,
                        "ttl": ttl if ttl > 0 else None
                    }
                except Exception as e:
                    logger.error(f"Error backing up key {key}: {e}")
                    continue
            
            # Generate filename
            filename = f"redis_backup_{timestamp}.json"
            if compress:
                filename += ".gz"
            
            filepath = self.backup_dir / filename
            
            # Save backup
            json_data = json.dumps(backup_data, indent=2, default=str)
            
            if compress:
                with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                    f.write(json_data)
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(json_data)
            
            file_size = filepath.stat().st_size
            
            logger.info(
                "backup_created",
                filename=filename,
                size=file_size,
                keys_count=len(backup_data["data"])
            )
            
            backup_result = {
                "success": True,
                "filename": filename,
                "filepath": str(filepath),
                "size": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2),
                "timestamp": timestamp,
                "keys_count": len(backup_data["data"]),
                "compressed": compress,
                "local_storage": True,
                "github_storage": False,
                "github_url": None
            }
            
            # Upload to GitHub if configured
            if self.github_enabled:
                github_success, github_url = await self._upload_to_github(filepath, filename)
                backup_result["github_storage"] = github_success
                backup_result["github_url"] = github_url
                
                if github_success:
                    logger.info(
                        "backup_uploaded_to_github",
                        filename=filename,
                        url=github_url
                    )
            
            return backup_result
            
        except Exception as e:
            logger.error("backup_failed", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_key_value(self, key: bytes, key_type: str) -> Any:
        """Get value for a key based on its type.
        
        Args:
            key: Redis key
            key_type: Type of the key (string, hash, list, set, zset)
            
        Returns:
            Value in appropriate format
        """
        if key_type == "string":
            value = await self.redis.client.get(key)
            # Try to decode as string, keep as base64 if binary
            try:
                return value.decode('utf-8') if isinstance(value, bytes) else value
            except UnicodeDecodeError:
                import base64
                return {"_binary": base64.b64encode(value).decode('utf-8')}
        
        elif key_type == "hash":
            hash_data = await self.redis.client.hgetall(key)
            result = {}
            for k, v in hash_data.items():
                k_str = k.decode('utf-8') if isinstance(k, bytes) else k
                try:
                    v_str = v.decode('utf-8') if isinstance(v, bytes) else v
                except UnicodeDecodeError:
                    import base64
                    v_str = {"_binary": base64.b64encode(v).decode('utf-8')}
                result[k_str] = v_str
            return result
        
        elif key_type == "list":
            list_data = await self.redis.client.lrange(key, 0, -1)
            result = []
            for item in list_data:
                try:
                    result.append(item.decode('utf-8') if isinstance(item, bytes) else item)
                except UnicodeDecodeError:
                    import base64
                    result.append({"_binary": base64.b64encode(item).decode('utf-8')})
            return result
        
        elif key_type == "set":
            set_data = await self.redis.client.smembers(key)
            result = []
            for item in set_data:
                try:
                    result.append(item.decode('utf-8') if isinstance(item, bytes) else item)
                except UnicodeDecodeError:
                    import base64
                    result.append({"_binary": base64.b64encode(item).decode('utf-8')})
            return result
        
        elif key_type == "zset":
            zset_data = await self.redis.client.zrange(key, 0, -1, withscores=True)
            result = []
            for i in range(0, len(zset_data), 2):
                member = zset_data[i]
                score = zset_data[i + 1] if i + 1 < len(zset_data) else 0
                try:
                    member_str = member.decode('utf-8') if isinstance(member, bytes) else member
                except UnicodeDecodeError:
                    import base64
                    member_str = {"_binary": base64.b64encode(member).decode('utf-8')}
                result.append({"member": member_str, "score": score})
            return result
        
        return None
    
    async def restore_backup(self, filename: str, overwrite: bool = False) -> Dict[str, Any]:
        """Restore Redis data from a backup file.
        
        Args:
            filename: Name of the backup file
            overwrite: Whether to overwrite existing keys
            
        Returns:
            Dict containing restore info
        """
        try:
            filepath = self.backup_dir / filename
            
            if not filepath.exists():
                return {
                    "success": False,
                    "error": "Backup file not found"
                }
            
            # Load backup data
            if filename.endswith('.gz'):
                with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                    backup_data = json.load(f)
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
            
            data = backup_data.get("data", {})
            restored_count = 0
            skipped_count = 0
            error_count = 0
            
            # Restore each key
            for key_str, key_data in data.items():
                try:
                    # Check if key exists
                    exists = await self.redis.client.exists(key_str)
                    if exists and not overwrite:
                        skipped_count += 1
                        continue
                    
                    key_type = key_data["type"]
                    value = key_data["value"]
                    ttl = key_data.get("ttl")
                    
                    # Restore based on type
                    await self._restore_key_value(key_str, key_type, value, ttl)
                    restored_count += 1
                    
                except Exception as e:
                    logger.error(f"Error restoring key {key_str}: {e}")
                    error_count += 1
                    continue
            
            logger.info(
                "backup_restored",
                filename=filename,
                restored=restored_count,
                skipped=skipped_count,
                errors=error_count
            )
            
            return {
                "success": True,
                "filename": filename,
                "restored_count": restored_count,
                "skipped_count": skipped_count,
                "error_count": error_count,
                "total_keys": len(data)
            }
            
        except Exception as e:
            logger.error("restore_failed", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _restore_key_value(self, key: str, key_type: str, value: Any, ttl: Optional[int]):
        """Restore a key with its value and type.
        
        Args:
            key: Redis key
            key_type: Type of the key
            value: Value to restore
            ttl: Time to live in seconds
        """
        import base64
        
        if key_type == "string":
            # Handle binary data
            if isinstance(value, dict) and "_binary" in value:
                value = base64.b64decode(value["_binary"])
            await self.redis.client.set(key, value)
        
        elif key_type == "hash":
            for k, v in value.items():
                if isinstance(v, dict) and "_binary" in v:
                    v = base64.b64decode(v["_binary"])
                await self.redis.client.hset(key, k, v)
        
        elif key_type == "list":
            for item in value:
                if isinstance(item, dict) and "_binary" in item:
                    item = base64.b64decode(item["_binary"])
                await self.redis.client.rpush(key, item)
        
        elif key_type == "set":
            for item in value:
                if isinstance(item, dict) and "_binary" in item:
                    item = base64.b64decode(item["_binary"])
                await self.redis.client.sadd(key, item)
        
        elif key_type == "zset":
            for item in value:
                member = item["member"]
                if isinstance(member, dict) and "_binary" in member:
                    member = base64.b64decode(member["_binary"])
                score = item["score"]
                await self.redis.client.zadd(key, {member: score})
        
        # Set TTL if specified
        if ttl:
            await self.redis.client.expire(key, ttl)
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backup files.
        
        Returns:
            List of backup file info
        """
        try:
            backups = []
            
            for filepath in sorted(self.backup_dir.glob("redis_backup_*.json*"), reverse=True):
                file_stat = filepath.stat()
                
                # Try to extract timestamp from filename
                filename = filepath.name
                timestamp_str = filename.replace("redis_backup_", "").replace(".json.gz", "").replace(".json", "")
                
                backups.append({
                    "filename": filename,
                    "filepath": str(filepath),
                    "size": file_stat.st_size,
                    "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                    "created_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    "timestamp": timestamp_str,
                    "compressed": filename.endswith('.gz')
                })
            
            return backups
            
        except Exception as e:
            logger.error("list_backups_failed", error=str(e))
            return []
    
    async def delete_backup(self, filename: str) -> Dict[str, Any]:
        """Delete a backup file.
        
        Args:
            filename: Name of the backup file to delete
            
        Returns:
            Dict containing deletion result
        """
        try:
            filepath = self.backup_dir / filename
            
            if not filepath.exists():
                return {
                    "success": False,
                    "error": "Backup file not found"
                }
            
            filepath.unlink()
            
            logger.info("backup_deleted", filename=filename)
            
            return {
                "success": True,
                "filename": filename
            }
            
        except Exception as e:
            logger.error("delete_backup_failed", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_backup_stats(self) -> Dict[str, Any]:
        """Get statistics about backups.
        
        Returns:
            Dict containing backup statistics
        """
        try:
            backups = await self.list_backups()
            
            total_size = sum(b["size"] for b in backups)
            
            stats = {
                "total_backups": len(backups),
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "latest_backup": backups[0] if backups else None,
                "oldest_backup": backups[-1] if backups else None,
                "github_enabled": self.github_enabled
            }
            
            # Get GitHub backups count if enabled
            if self.github_enabled:
                github_backups = await self._list_github_backups()
                stats["github_backups_count"] = len(github_backups)
            
            return stats
            
        except Exception as e:
            logger.error("get_backup_stats_failed", error=str(e))
            return {
                "total_backups": 0,
                "total_size": 0,
                "total_size_mb": 0,
                "github_enabled": self.github_enabled
            }
    
    async def _upload_to_github(self, filepath: Path, filename: str) -> Tuple[bool, Optional[str]]:
        """Upload backup file to GitHub.
        
        Args:
            filepath: Local file path
            filename: Backup filename
            
        Returns:
            Tuple of (success: bool, url: Optional[str])
        """
        try:
            # Read file content
            with open(filepath, 'rb') as f:
                file_content = f.read()
            
            # Check file size
            file_size = len(file_content)
            if file_size > Config.MAX_GITHUB_FILE_SIZE:
                logger.warning(
                    "backup_too_large_for_github",
                    filename=filename,
                    size_mb=file_size / (1024 * 1024)
                )
                return False, "File exceeds GitHub 100MB limit"
            
            # Encode to base64
            content_base64 = base64.b64encode(file_content).decode('utf-8')
            
            # GitHub API URL
            github_path = f"{self.github_backup_path}{filename}"
            api_url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/contents/{github_path}"
            
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                # Check if file exists
                async with session.get(api_url, headers=headers) as response:
                    sha = None
                    if response.status == 200:
                        existing = await response.json()
                        sha = existing.get('sha')
                
                # Prepare payload
                payload = {
                    "message": f"Backup: {filename}",
                    "content": content_base64,
                    "branch": self.github_branch
                }
                
                if sha:
                    payload["sha"] = sha
                
                # Upload file
                async with session.put(api_url, headers=headers, json=payload) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        file_url = result.get('content', {}).get('html_url')
                        return True, file_url
                    else:
                        error_text = await response.text()
                        logger.error(
                            "github_upload_failed",
                            filename=filename,
                            status=response.status,
                            error=error_text
                        )
                        return False, f"GitHub API error: {response.status}"
        
        except Exception as e:
            logger.error("github_upload_error", filename=filename, error=str(e))
            return False, str(e)
    
    async def _list_github_backups(self) -> List[Dict[str, Any]]:
        """List backups stored on GitHub.
        
        Returns:
            List of backup file info from GitHub
        """
        try:
            if not self.github_enabled:
                return []
            
            api_url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/contents/{self.github_backup_path}"
            
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers) as response:
                    if response.status == 200:
                        files = await response.json()
                        backups = []
                        
                        for file in files:
                            if file['name'].startswith('redis_backup_') and file['name'].endswith(('.json', '.json.gz')):
                                backups.append({
                                    "filename": file['name'],
                                    "size": file['size'],
                                    "size_mb": round(file['size'] / (1024 * 1024), 2),
                                    "url": file['html_url'],
                                    "download_url": file['download_url'],
                                    "sha": file['sha']
                                })
                        
                        return backups
                    else:
                        logger.warning("github_list_failed", status=response.status)
                        return []
        
        except Exception as e:
            logger.error("github_list_error", error=str(e))
            return []
    
    async def download_from_github(self, filename: str) -> Dict[str, Any]:
        """Download a backup from GitHub to local storage.
        
        Args:
            filename: Backup filename to download
            
        Returns:
            Dict containing download result
        """
        try:
            if not self.github_enabled:
                return {
                    "success": False,
                    "error": "GitHub storage not configured"
                }
            
            github_path = f"{self.github_backup_path}{filename}"
            api_url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/contents/{github_path}"
            
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers) as response:
                    if response.status == 200:
                        file_data = await response.json()
                        download_url = file_data.get('download_url')
                        
                        if not download_url:
                            return {
                                "success": False,
                                "error": "No download URL available"
                            }
                        
                        # Download file content
                        async with session.get(download_url) as download_response:
                            if download_response.status == 200:
                                content = await download_response.read()
                                
                                # Save to local storage
                                filepath = self.backup_dir / filename
                                with open(filepath, 'wb') as f:
                                    f.write(content)
                                
                                logger.info(
                                    "backup_downloaded_from_github",
                                    filename=filename,
                                    size_mb=len(content) / (1024 * 1024)
                                )
                                
                                return {
                                    "success": True,
                                    "filename": filename,
                                    "size": len(content),
                                    "size_mb": round(len(content) / (1024 * 1024), 2),
                                    "filepath": str(filepath)
                                }
                            else:
                                return {
                                    "success": False,
                                    "error": f"Download failed: {download_response.status}"
                                }
                    else:
                        return {
                            "success": False,
                            "error": f"File not found on GitHub: {response.status}"
                        }
        
        except Exception as e:
            logger.error("github_download_error", filename=filename, error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_all_backups(self) -> Dict[str, Any]:
        """List all backups from both local and GitHub storage.
        
        Returns:
            Dict containing local and GitHub backups
        """
        try:
            local_backups = await self.list_backups()
            github_backups = []
            
            if self.github_enabled:
                github_backups = await self._list_github_backups()
            
            return {
                "local": local_backups,
                "github": github_backups,
                "github_enabled": self.github_enabled
            }
        
        except Exception as e:
            logger.error("list_all_backups_error", error=str(e))
            return {
                "local": [],
                "github": [],
                "github_enabled": self.github_enabled
            }
