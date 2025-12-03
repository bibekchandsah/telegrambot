#!/usr/bin/env python3
"""
Pre-deployment checklist script for Railway deployment.
Run this before deploying to ensure everything is configured correctly.
"""
import os
import sys
from pathlib import Path


def check_file_exists(filepath: str, required: bool = True) -> bool:
    """Check if a file exists."""
    exists = Path(filepath).exists()
    status = "✅" if exists else ("❌" if required else "⚠️")
    req_text = "REQUIRED" if required else "OPTIONAL"
    print(f"{status} {filepath} - {req_text}")
    return exists


def check_env_var(var_name: str, required: bool = True) -> bool:
    """Check if environment variable is set."""
    value = os.getenv(var_name)
    exists = value is not None and value != ""
    status = "✅" if exists else ("❌" if required else "⚠️")
    req_text = "REQUIRED" if required else "OPTIONAL"
    print(f"{status} {var_name} - {req_text}")
    if exists and var_name != "BOT_TOKEN":  # Don't print token
        print(f"    Value: {value}")
    return exists


def check_git_status():
    """Check git status."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout.strip():
            print("⚠️  Uncommitted changes detected:")
            print(result.stdout)
            return False
        else:
            print("✅ Git working tree is clean")
            return True
    except Exception as e:
        print(f"⚠️  Could not check git status: {e}")
        return False


def main():
    """Run pre-deployment checks."""
    print("=" * 60)
    print("🚂 RAILWAY DEPLOYMENT PRE-FLIGHT CHECK")
    print("=" * 60)
    print()
    
    all_checks = []
    
    # Check required files
    print("📁 Checking Required Files:")
    print("-" * 60)
    all_checks.append(check_file_exists("Dockerfile", required=True))
    all_checks.append(check_file_exists("railway.json", required=True))
    all_checks.append(check_file_exists("requirements.txt", required=True))
    all_checks.append(check_file_exists("src/bot.py", required=True))
    all_checks.append(check_file_exists("src/config.py", required=True))
    all_checks.append(check_file_exists(".gitignore", required=True))
    print()
    
    # Check optional files
    print("📄 Checking Optional Files:")
    print("-" * 60)
    check_file_exists("README.md", required=False)
    check_file_exists("RAILWAY_DEPLOYMENT.md", required=False)
    check_file_exists(".env.example", required=False)
    print()
    
    # Check .env is NOT committed
    print("🔒 Checking Security:")
    print("-" * 60)
    if check_file_exists(".env", required=False):
        print("⚠️  WARNING: .env file exists locally")
        print("    Make sure it's in .gitignore!")
        print("    Use Railway Variables instead for production")
    else:
        print("✅ No .env file (good - use Railway Variables)")
    
    # Check .gitignore contains .env
    try:
        with open(".gitignore", "r") as f:
            gitignore_content = f.read()
            if ".env" in gitignore_content:
                print("✅ .env is in .gitignore")
            else:
                print("❌ .env is NOT in .gitignore - ADD IT!")
                all_checks.append(False)
    except Exception as e:
        print(f"⚠️  Could not read .gitignore: {e}")
    print()
    
    # Check environment variables (if .env exists)
    print("🔧 Checking Environment Variables:")
    print("-" * 60)
    print("(These should be set in Railway Variables tab)")
    print()
    
    # Load .env if exists (for local check)
    if Path(".env").exists():
        from dotenv import load_dotenv
        load_dotenv()
        print("📋 Loaded from local .env file:")
    else:
        print("📋 Required Railway Variables:")
    
    all_checks.append(check_env_var("BOT_TOKEN", required=True))
    check_env_var("REDIS_URL", required=False)  # Railway provides this
    check_env_var("ADMIN_IDS", required=False)
    check_env_var("ENVIRONMENT", required=False)
    check_env_var("LOG_LEVEL", required=False)
    print()
    
    # Check git status
    print("📦 Checking Git Status:")
    print("-" * 60)
    git_clean = check_git_status()
    if not git_clean:
        print("⚠️  Commit changes before deploying")
    print()
    
    # Check Python dependencies
    print("🐍 Checking Python Dependencies:")
    print("-" * 60)
    try:
        import telegram
        print(f"✅ python-telegram-bot {telegram.__version__}")
    except ImportError:
        print("❌ python-telegram-bot not installed")
        all_checks.append(False)
    
    try:
        import redis
        print(f"✅ redis {redis.__version__}")
    except ImportError:
        print("❌ redis not installed")
        all_checks.append(False)
    
    try:
        import dotenv
        print("✅ python-dotenv installed")
    except ImportError:
        print("⚠️  python-dotenv not installed (optional)")
    print()
    
    # Final summary
    print("=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    if all(all_checks):
        print("✅ ALL CRITICAL CHECKS PASSED!")
        print()
        print("🚀 Ready to deploy to Railway!")
        print()
        print("Next steps:")
        print("1. Commit and push to GitHub:")
        print("   git add .")
        print("   git commit -m 'Ready for Railway deployment'")
        print("   git push origin main")
        print()
        print("2. Go to railway.app and deploy from GitHub")
        print("3. Add Redis database in Railway")
        print("4. Set BOT_TOKEN in Railway Variables")
        print("5. Monitor logs for successful startup")
        print()
        print("📖 See RAILWAY_DEPLOYMENT.md for detailed instructions")
        return 0
    else:
        print("❌ SOME CHECKS FAILED!")
        print()
        print("⚠️  Fix the issues above before deploying")
        print()
        print("Common fixes:")
        print("- Install missing dependencies: pip install -r requirements.txt")
        print("- Set BOT_TOKEN in .env or Railway Variables")
        print("- Commit all changes: git add . && git commit")
        print("- Add .env to .gitignore")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Check interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error running checks: {e}")
        sys.exit(1)
