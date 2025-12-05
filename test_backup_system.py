"""Test Redis backup system."""
import asyncio
from src.db.redis_client import RedisClient
from src.services.backup import BackupService
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def test_backup_system():
    """Test backup creation and restore."""
    print("=" * 60)
    print("Testing Redis Backup System")
    print("=" * 60)
    print()
    
    try:
        # Connect to Redis
        print("1. Connecting to Redis...")
        client = RedisClient()
        await client.connect()
        print("   ✅ Connected successfully")
        print()
        
        # Create backup service
        backup = BackupService(client)
        
        # Test 1: Create test data
        print("2. Creating test data...")
        test_key = "backup_test:data"
        test_value = "This is a test value for backup"
        await client.client.set(test_key, test_value)
        await client.client.expire(test_key, 3600)  # 1 hour TTL
        print(f"   ✅ Created test key: {test_key}")
        print()
        
        # Test 2: Create backup
        print("3. Creating backup...")
        backup_result = await backup.create_backup(compress=True)
        
        if backup_result['success']:
            print("   ✅ Backup created successfully!")
            print(f"   📁 Filename: {backup_result['filename']}")
            print(f"   📊 Size: {backup_result['size_mb']} MB")
            print(f"   🔑 Keys: {backup_result['keys_count']}")
            print()
        else:
            print(f"   ❌ Backup failed: {backup_result['error']}")
            return False
        
        # Test 3: List backups
        print("4. Listing backups...")
        backups = await backup.list_backups()
        print(f"   ✅ Found {len(backups)} backup(s)")
        if backups:
            latest = backups[0]
            print(f"   📄 Latest: {latest['filename']} ({latest['size_mb']} MB)")
        print()
        
        # Test 4: Get backup stats
        print("5. Getting backup statistics...")
        stats = await backup.get_backup_stats()
        print(f"   ✅ Total backups: {stats['total_backups']}")
        print(f"   💽 Total size: {stats['total_size_mb']} MB")
        print()
        
        # Test 5: Delete test key
        print("6. Deleting test key (to test restore)...")
        await client.client.delete(test_key)
        exists = await client.client.exists(test_key)
        print(f"   ✅ Test key deleted (exists: {exists == 0})")
        print()
        
        # Test 6: Restore backup
        print("7. Restoring from backup...")
        restore_result = await backup.restore_backup(
            backup_result['filename'],
            overwrite=True
        )
        
        if restore_result['success']:
            print("   ✅ Restore completed successfully!")
            print(f"   📊 Restored: {restore_result['restored_count']} keys")
            print(f"   ⏭️  Skipped: {restore_result['skipped_count']} keys")
            print(f"   ❌ Errors: {restore_result['error_count']} keys")
            print()
        else:
            print(f"   ❌ Restore failed: {restore_result['error']}")
            return False
        
        # Test 7: Verify restored data
        print("8. Verifying restored data...")
        restored_value = await client.client.get(test_key)
        restored_value_str = restored_value.decode('utf-8') if restored_value else None
        
        if restored_value_str == test_value:
            print("   ✅ Data restored correctly!")
            print(f"   ✔️  Value matches: '{restored_value_str}'")
            
            # Check TTL
            ttl = await client.client.ttl(test_key)
            print(f"   ✔️  TTL restored: {ttl} seconds")
        else:
            print(f"   ❌ Data mismatch!")
            print(f"   Expected: '{test_value}'")
            print(f"   Got: '{restored_value_str}'")
            return False
        print()
        
        # Test 8: Clean up test key
        print("9. Cleaning up test data...")
        await client.client.delete(test_key)
        print("   ✅ Test key deleted")
        print()
        
        # Close connection
        await client.close()
        
        print("=" * 60)
        print("✅ All tests passed successfully!")
        print("=" * 60)
        print()
        print("The backup system is working correctly. You can now:")
        print("  1. Create backups: python create_backup.py")
        print("  2. Start scheduler: python backup_scheduler.py")
        print("  3. Use admin dashboard: /api/backup/* endpoints")
        print()
        
        return True
        
    except Exception as e:
        print()
        print(f"❌ Test failed with error: {e}")
        print()
        logger.error("backup_test_failed", error=str(e))
        return False


if __name__ == '__main__':
    success = asyncio.run(test_backup_system())
    exit(0 if success else 1)
