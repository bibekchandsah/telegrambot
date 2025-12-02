"""
Cleanup script for reports and moderation logs data
"""
import asyncio
from src.db.redis_client import RedisClient

async def cleanup_reports_data():
    """Clean all report and moderation log data from Redis"""
    redis_client = RedisClient()
    
    try:
        await redis_client.connect()
        print("Connected to Redis")
        
        # Get all keys related to reports
        report_keys = await redis_client.keys("stats:*:reports")
        report_count_keys = await redis_client.keys("stats:*:report_count")
        report_flag_keys = await redis_client.keys("stats:*:report_flags:*")
        approval_keys = await redis_client.keys("report:approvals:*")
        rejection_keys = await redis_client.keys("report:rejections:*")
        
        # Get moderation log keys
        mod_log_keys = await redis_client.keys("bot:moderation_log")
        mod_log_action_keys = await redis_client.keys("moderation:*")
        
        all_keys = (
            report_keys + 
            report_count_keys + 
            report_flag_keys + 
            approval_keys + 
            rejection_keys + 
            mod_log_keys +
            mod_log_action_keys
        )
        
        if not all_keys:
            print("No report or moderation data found to clean")
            return
        
        print(f"\nFound {len(all_keys)} keys to delete:")
        print(f"  - Report data: {len(report_keys)}")
        print(f"  - Report counts: {len(report_count_keys)}")
        print(f"  - Report flags: {len(report_flag_keys)}")
        print(f"  - Approvals: {len(approval_keys)}")
        print(f"  - Rejections: {len(rejection_keys)}")
        print(f"  - Moderation logs: {len(mod_log_keys)}")
        
        # Delete all keys
        deleted = 0
        for key in all_keys:
            if isinstance(key, bytes):
                key = key.decode('utf-8')
            await redis_client.delete(key)
            deleted += 1
        
        print(f"\n✅ Successfully deleted {deleted} keys")
        print("All reports and moderation logs have been cleaned!")
        
    except Exception as e:
        print(f"❌ Error cleaning data: {e}")
    finally:
        await redis_client.close()
        print("Redis connection closed")

if __name__ == "__main__":
    print("=" * 60)
    print("CLEANUP REPORTS & MODERATION LOGS DATA")
    print("=" * 60)
    print("\nThis will delete:")
    print("  • All user reports")
    print("  • Report counts and flags")
    print("  • Report approvals and rejections")
    print("  • Moderation logs")
    print("\n⚠️  WARNING: This action cannot be undone!")
    print("=" * 60)
    
    response = input("\nType 'YES' to confirm cleanup: ")
    
    if response.strip().upper() == "YES":
        print("\nStarting cleanup...")
        asyncio.run(cleanup_reports_data())
    else:
        print("\n❌ Cleanup cancelled")
