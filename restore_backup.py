"""Restore Redis data from a backup file."""
import asyncio
import sys
from src.db.redis_client import RedisClient
from src.services.backup import BackupService
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def main():
    """Restore from a backup file."""
    print("=" * 60)
    print("Redis Restore Tool")
    print("=" * 60)
    print()
    
    # Check arguments
    if len(sys.argv) < 2:
        print("Usage: python restore_backup.py <backup_filename> [overwrite]")
        print()
        print("Examples:")
        print("  python restore_backup.py redis_backup_20231205_143022.json.gz")
        print("  python restore_backup.py redis_backup_20231205_143022.json.gz true")
        print()
        sys.exit(1)
    
    filename = sys.argv[1]
    overwrite = False
    
    if len(sys.argv) > 2:
        overwrite = sys.argv[2].lower() in ('true', '1', 'yes', 'y', 'overwrite')
    
    print(f"Backup file: {filename}")
    print(f"Overwrite existing keys: {'Yes' if overwrite else 'No'}")
    print()
    
    if not overwrite:
        print("⚠️  WARNING: Existing keys will be SKIPPED")
        print("   To overwrite existing keys, pass 'true' as second argument")
        print()
    else:
        print("⚠️  WARNING: This will OVERWRITE existing keys!")
        print()
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() not in ('yes', 'y'):
            print("Restore cancelled.")
            sys.exit(0)
        print()
    
    try:
        # Connect to Redis
        client = RedisClient()
        await client.connect()
        print("✅ Connected to Redis")
        
        # Restore backup
        backup = BackupService(client)
        
        # Check if backup exists
        backups = await backup.list_backups()
        backup_exists = any(b['filename'] == filename for b in backups)
        
        if not backup_exists:
            print()
            print(f"❌ Backup file not found: {filename}")
            print()
            print("Available backups:")
            for b in backups:
                print(f"  - {b['filename']} ({b['size_mb']} MB, {b['created_at']})")
            print()
            sys.exit(1)
        
        print(f"Restoring from {filename}...")
        print()
        
        result = await backup.restore_backup(filename, overwrite=overwrite)
        
        if result['success']:
            print()
            print("✅ Restore completed successfully!")
            print()
            print("Restore Details:")
            print(f"  📁 Filename: {result['filename']}")
            print(f"  ✅ Keys restored: {result['restored_count']}")
            print(f"  ⏭️  Keys skipped: {result['skipped_count']}")
            print(f"  ❌ Keys failed: {result['error_count']}")
            print(f"  📊 Total keys in backup: {result['total_keys']}")
            print()
            
            if result['skipped_count'] > 0 and not overwrite:
                print("💡 Tip: Some keys were skipped because they already exist.")
                print("   Run with 'true' argument to overwrite existing keys.")
                print()
            
            if result['error_count'] > 0:
                print("⚠️  Warning: Some keys failed to restore. Check logs for details.")
                print()
        else:
            print()
            print(f"❌ Restore failed: {result['error']}")
            print()
            sys.exit(1)
        
        await client.close()
        print("✅ Restore complete!")
        
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        print()
        logger.error("restore_tool_error", error=str(e))
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
