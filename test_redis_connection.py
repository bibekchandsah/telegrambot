"""Test Redis connection from localhost to Railway."""
import os
import sys
from dotenv import load_dotenv
import redis

# Load environment variables
load_dotenv()

def test_redis_connection():
    """Test Redis connection with detailed feedback."""
    redis_url = os.getenv("REDIS_URL")
    
    if not redis_url:
        print("❌ ERROR: REDIS_URL not found in .env file")
        return False
    
    print(f"🔍 Testing connection to: {redis_url}")
    print("=" * 60)
    
    try:
        # Parse URL to show details (without exposing full password)
        from urllib.parse import urlparse
        parsed = urlparse(redis_url)
        
        print(f"📍 Host: {parsed.hostname}")
        print(f"📍 Port: {parsed.port}")
        print(f"📍 Database: {parsed.path.lstrip('/')}")
        print(f"📍 Password: {'*' * 10 if parsed.password else 'None'}")
        print("=" * 60)
        
        # Create Redis client
        print("\n⏳ Connecting to Redis...")
        client = redis.from_url(redis_url, decode_responses=True)
        
        # Test connection
        print("⏳ Testing PING...")
        pong = client.ping()
        
        if pong:
            print("✅ Connection successful! Redis responded with PONG")
        
        # Test basic operations
        print("\n⏳ Testing SET operation...")
        client.set("test:connection", "success", ex=10)
        print("✅ SET successful")
        
        print("⏳ Testing GET operation...")
        value = client.get("test:connection")
        print(f"✅ GET successful: {value}")
        
        # Show some stats
        print("\n📊 Redis Info:")
        info = client.info()
        print(f"   • Redis Version: {info.get('redis_version', 'Unknown')}")
        print(f"   • Connected Clients: {info.get('connected_clients', 'Unknown')}")
        print(f"   • Used Memory: {info.get('used_memory_human', 'Unknown')}")
        print(f"   • Total Keys: {client.dbsize()}")
        
        # Test bot-specific keys
        print("\n🤖 Bot Data Check:")
        bot_keys = client.keys("*")
        if bot_keys:
            print(f"   • Found {len(bot_keys)} keys in database")
            print(f"   • Sample keys: {bot_keys[:5]}")
        else:
            print("   • No bot data found (database is empty)")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED! Redis connection is working.")
        print("=" * 60)
        
        client.close()
        return True
        
    except redis.ConnectionError as e:
        print(f"\n❌ CONNECTION ERROR: {e}")
        print("\n💡 Possible issues:")
        print("   1. Wrong host/port (check Railway public domain)")
        print("   2. Wrong password (check Railway variables)")
        print("   3. Firewall blocking connection")
        print("   4. Redis service not running on Railway")
        return False
        
    except redis.AuthenticationError as e:
        print(f"\n❌ AUTHENTICATION ERROR: {e}")
        print("\n💡 Password is incorrect. Check Railway variables for correct password.")
        return False
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    print("🔧 Redis Connection Test")
    print("=" * 60)
    
    success = test_redis_connection()
    
    if success:
        sys.exit(0)
    else:
        print("\n💡 To fix:")
        print("   1. Get public Redis URL from Railway dashboard")
        print("   2. Update REDIS_URL in .env file")
        print("   3. Format: redis://default:PASSWORD@HOST:PORT/0")
        sys.exit(1)
