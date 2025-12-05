"""Automated Redis backup scheduler."""
import asyncio
import schedule
import time
from datetime import datetime
from src.db.redis_client import RedisClient
from src.services.backup import BackupService
from src.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BackupScheduler:
    """Scheduler for automated Redis backups."""
    
    def __init__(self, interval_hours: int = 24, compress: bool = True, max_backups: int = 7):
        """Initialize backup scheduler.
        
        Args:
            interval_hours: Hours between automatic backups
            compress: Whether to compress backup files
            max_backups: Maximum number of backups to keep (oldest will be deleted)
        """
        self.interval_hours = interval_hours
        self.compress = compress
        self.max_backups = max_backups
        self.redis_client = None
        self.backup_service = None
    
    async def initialize(self):
        """Initialize Redis client and backup service."""
        self.redis_client = RedisClient()
        await self.redis_client.connect()
        self.backup_service = BackupService(self.redis_client)
        logger.info("Backup scheduler initialized")
    
    async def create_scheduled_backup(self):
        """Create a scheduled backup and manage old backups."""
        try:
            logger.info("Starting scheduled backup...")
            
            # Create backup
            result = await self.backup_service.create_backup(compress=self.compress)
            
            if result.get('success'):
                logger.info(
                    "scheduled_backup_created",
                    filename=result['filename'],
                    size_mb=result['size_mb'],
                    keys_count=result['keys_count']
                )
                
                # Clean up old backups
                await self.cleanup_old_backups()
            else:
                logger.error("scheduled_backup_failed", error=result.get('error'))
        
        except Exception as e:
            logger.error("scheduled_backup_error", error=str(e))
    
    async def cleanup_old_backups(self):
        """Delete old backups keeping only max_backups most recent."""
        try:
            backups = await self.backup_service.list_backups()
            
            if len(backups) > self.max_backups:
                # Sort by creation time (newest first)
                backups.sort(key=lambda x: x['created_at'], reverse=True)
                
                # Delete old backups
                for backup in backups[self.max_backups:]:
                    result = await self.backup_service.delete_backup(backup['filename'])
                    if result.get('success'):
                        logger.info("old_backup_deleted", filename=backup['filename'])
        
        except Exception as e:
            logger.error("cleanup_old_backups_error", error=str(e))
    
    def schedule_backups(self):
        """Schedule automatic backups."""
        def run_backup():
            asyncio.run(self.create_scheduled_backup())
        
        # Schedule backup
        schedule.every(self.interval_hours).hours.do(run_backup)
        
        # Also run at specific time (e.g., 3 AM daily)
        schedule.every().day.at("03:00").do(run_backup)
        
        logger.info(
            "backup_schedule_configured",
            interval_hours=self.interval_hours,
            daily_time="03:00",
            max_backups=self.max_backups
        )
        
        # Create initial backup
        logger.info("Creating initial backup...")
        run_backup()
    
    async def run_forever(self):
        """Run the scheduler continuously."""
        await self.initialize()
        self.schedule_backups()
        
        logger.info("Backup scheduler running...")
        
        try:
            while True:
                schedule.run_pending()
                await asyncio.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Backup scheduler stopped by user")
        finally:
            await self.redis_client.close()


async def main():
    """Main entry point."""
    import sys
    
    # Parse command line arguments
    interval_hours = 24
    compress = True
    max_backups = 7
    
    if len(sys.argv) > 1:
        try:
            interval_hours = int(sys.argv[1])
        except ValueError:
            print(f"Invalid interval hours: {sys.argv[1]}")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        compress = sys.argv[2].lower() in ('true', '1', 'yes', 'y')
    
    if len(sys.argv) > 3:
        try:
            max_backups = int(sys.argv[3])
        except ValueError:
            print(f"Invalid max backups: {sys.argv[3]}")
            sys.exit(1)
    
    print(f"Starting backup scheduler:")
    print(f"  Interval: {interval_hours} hours")
    print(f"  Compress: {compress}")
    print(f"  Max backups: {max_backups}")
    print(f"  Daily backup at: 03:00")
    print()
    
    scheduler = BackupScheduler(
        interval_hours=interval_hours,
        compress=compress,
        max_backups=max_backups
    )
    
    await scheduler.run_forever()


if __name__ == '__main__':
    asyncio.run(main())
