"""Create a manual Redis backup."""
import asyncio
import sys
from src.db.redis_client import RedisClient
from src.services.backup import BackupService
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def main():
    """Create a backup and display results."""
    print("=" * 60)
    print("Redis Backup Tool")
    print("=" * 60)
    print()
    
    # Check for compression flag
    compress = True
    if len(sys.argv) > 1:
        compress = sys.argv[1].lower() in ('true', '1', 'yes', 'y', 'compressed')
    
    print(f"Creating {'compressed' if compress else 'uncompressed'} backup...")
    print()
    
    try:
        # Connect to Redis
        client = RedisClient()
        await client.connect()
        print("✅ Connected to Redis")
        
        # Create backup
        backup = BackupService(client)
        result = await backup.create_backup(compress=compress)
        
        if result['success']:
            print()
            print("✅ Backup created successfully!")
            print()
            print("Backup Details:")
            print(f"  📁 Filename: {result['filename']}")
            print(f"  📊 Size: {result['size_mb']} MB ({result['size']} bytes)")
            print(f"  🔑 Keys backed up: {result['keys_count']}")
            print(f"  🗜️  Compressed: {'Yes' if result['compressed'] else 'No'}")
            print(f"  📍 Location: {result['filepath']}")
            print()
            print("💡 Tip: Download this file and store it safely!")
            print()
        else:
            print()
            print(f"❌ Backup failed: {result['error']}")
            print()
            sys.exit(1)
        
        # Show backup statistics
        stats = await backup.get_backup_stats()
        print("Backup Statistics:")
        print(f"  Total backups: {stats['total_backups']}")
        print(f"  Total size: {stats['total_size_mb']} MB")
        if stats['latest_backup']:
            print(f"  Latest backup: {stats['latest_backup']['filename']}")
        print()
        
        await client.close()
        print("✅ Backup complete!")
        
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        print()
        logger.error("backup_tool_error", error=str(e))
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
