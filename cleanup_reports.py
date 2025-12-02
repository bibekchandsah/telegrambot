"""
Redis Data Cleanup Script
Allows selective cleanup of different data categories for testing
"""
import asyncio
from src.db.redis_client import RedisClient


async def cleanup_user_profiles(redis_client):
    """Clean all user profiles"""
    keys = await redis_client.keys("profile:*")
    return keys, "User Profiles"


async def cleanup_user_preferences(redis_client):
    """Clean all user preferences"""
    keys = await redis_client.keys("preferences:*")
    return keys, "User Preferences"


async def cleanup_media_preferences(redis_client):
    """Clean all media preferences"""
    keys = await redis_client.keys("media_prefs:*")
    return keys, "Media Preferences"


async def cleanup_user_stats(redis_client):
    """Clean all user statistics"""
    stat_keys = await redis_client.keys("stats:*:*")
    return stat_keys, "User Statistics"


async def cleanup_chat_sessions(redis_client):
    """Clean all active chat sessions and pairs"""
    chat_keys = await redis_client.keys("chat:*")
    pair_keys = await redis_client.keys("pair:*")
    state_keys = await redis_client.keys("state:*")
    all_keys = chat_keys + pair_keys + state_keys
    return all_keys, "Chat Sessions & States"


async def cleanup_queue_data(redis_client):
    """Clean all queue data"""
    queue_keys = await redis_client.keys("queue:*")
    bot_queue = await redis_client.keys("bot:queue")
    all_keys = queue_keys + bot_queue
    return all_keys, "Queue Data"


async def cleanup_reports(redis_client):
    """Clean all report data"""
    report_keys = await redis_client.keys("stats:*:reports")
    report_count_keys = await redis_client.keys("stats:*:report_count")
    report_flag_keys = await redis_client.keys("stats:*:report_flags:*")
    approval_keys = await redis_client.keys("report:approvals:*")
    rejection_keys = await redis_client.keys("report:rejections:*")
    all_keys = report_keys + report_count_keys + report_flag_keys + approval_keys + rejection_keys
    return all_keys, "Reports & Safety Data"


async def cleanup_moderation_logs(redis_client):
    """Clean all moderation logs"""
    mod_log_keys = await redis_client.keys("bot:moderation_log")
    mod_action_keys = await redis_client.keys("moderation:*")
    all_keys = mod_log_keys + mod_action_keys
    return all_keys, "Moderation Logs"


async def cleanup_bans_warnings(redis_client):
    """Clean all bans and warnings"""
    ban_keys = await redis_client.keys("ban:*")
    warning_keys = await redis_client.keys("warnings:*")
    all_keys = ban_keys + warning_keys
    return all_keys, "Bans & Warnings"


async def cleanup_feedback(redis_client):
    """Clean all feedback data"""
    feedback_keys = await redis_client.keys("feedback:*")
    pending_keys = await redis_client.keys("pending_feedback:*")
    all_keys = feedback_keys + pending_keys
    return all_keys, "Feedback & Ratings"


async def cleanup_activity_tracking(redis_client):
    """Clean all activity tracking data"""
    activity_keys = await redis_client.keys("activity:*")
    last_seen_keys = await redis_client.keys("last_seen:*")
    all_keys = activity_keys + last_seen_keys
    return all_keys, "Activity Tracking"


async def cleanup_blocked_media(redis_client):
    """Clean blocked media types"""
    keys = await redis_client.keys("bot:blocked_media:*")
    return keys, "Blocked Media Types"


async def cleanup_bad_words(redis_client):
    """Clean bad words list"""
    keys = await redis_client.keys("bot:bad_words")
    return keys, "Bad Words Filter"


async def cleanup_bot_settings(redis_client):
    """Clean bot settings"""
    keys = await redis_client.keys("bot:settings:*")
    return keys, "Bot Settings"


async def cleanup_all_data(redis_client):
    """Clean ALL Redis data"""
    keys = await redis_client.keys("*")
    return keys, "ALL DATA (Complete Reset)"


async def perform_cleanup(cleanup_func, redis_client):
    """Perform the selected cleanup operation"""
    try:
        await redis_client.connect()
        print("\n✅ Connected to Redis")
        
        keys, category_name = await cleanup_func(redis_client)
        
        if not keys:
            print(f"\n⚠️  No {category_name} found to clean")
            return
        
        print(f"\n📊 Found {len(keys)} keys in '{category_name}'")
        
        # Show sample of keys (first 10)
        if len(keys) > 0:
            print("\n📋 Sample keys:")
            for i, key in enumerate(keys[:10]):
                key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                print(f"  {i+1}. {key_str}")
            if len(keys) > 10:
                print(f"  ... and {len(keys) - 10} more")
        
        print(f"\n⚠️  WARNING: This will delete {len(keys)} keys!")
        confirm = input("\nType 'YES' to confirm deletion: ")
        
        if confirm.strip().upper() != "YES":
            print("\n❌ Cleanup cancelled")
            return
        
        # Delete all keys
        deleted = 0
        for key in keys:
            if isinstance(key, bytes):
                key = key.decode('utf-8')
            await redis_client.delete(key)
            deleted += 1
        
        print(f"\n✅ Successfully deleted {deleted} keys from '{category_name}'")
        
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
    finally:
        await redis_client.close()
        print("✅ Redis connection closed")


def show_menu():
    """Display the cleanup menu"""
    print("\n" + "=" * 70)
    print("REDIS DATA CLEANUP MENU")
    print("=" * 70)
    print("\n📋 Select data category to clean:\n")
    
    options = {
        "1": ("User Profiles", cleanup_user_profiles),
        "2": ("User Preferences", cleanup_user_preferences),
        "3": ("Media Preferences", cleanup_media_preferences),
        "4": ("User Statistics", cleanup_user_stats),
        "5": ("Chat Sessions & States", cleanup_chat_sessions),
        "6": ("Queue Data", cleanup_queue_data),
        "7": ("Reports & Safety Data", cleanup_reports),
        "8": ("Moderation Logs", cleanup_moderation_logs),
        "9": ("Bans & Warnings", cleanup_bans_warnings),
        "10": ("Feedback & Ratings", cleanup_feedback),
        "11": ("Activity Tracking", cleanup_activity_tracking),
        "12": ("Blocked Media Types", cleanup_blocked_media),
        "13": ("Bad Words Filter", cleanup_bad_words),
        "14": ("Bot Settings", cleanup_bot_settings),
        "99": ("⚠️  ALL DATA (Complete Reset)", cleanup_all_data),
        "0": ("Exit", None),
    }
    
    for key, (name, _) in options.items():
        if key == "99":
            print(f"\n  {key}. {name}")
        elif key == "0":
            print(f"\n  {key}. {name}")
        else:
            print(f"  {key}. {name}")
    
    print("\n" + "=" * 70)
    
    return options


if __name__ == "__main__":
    print("\n" + "🧹" * 35)
    print("REDIS CLEANUP UTILITY")
    print("🧹" * 35)
    
    while True:
        options = show_menu()
        choice = input("\nEnter your choice: ").strip()
        
        if choice == "0":
            print("\n👋 Exiting cleanup utility...")
            break
        
        if choice not in options:
            print("\n❌ Invalid choice. Please try again.")
            continue
        
        name, cleanup_func = options[choice]
        
        if cleanup_func is None:
            continue
        
        print(f"\n🎯 Selected: {name}")
        
        redis_client = RedisClient()
        asyncio.run(perform_cleanup(cleanup_func, redis_client))
        
        input("\nPress Enter to continue...")
    
    print("\n✅ Cleanup utility closed.\n")
