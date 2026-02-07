import os
from dotenv import load_dotenv
load_dotenv()

def test_environment():
    """Test environment setup"""
    print("🔍 Testing Environment Setup...")
    
    # Test TELEGRAM_BOT_TOKEN
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if token:
        print(f"✅ TELEGRAM_BOT_TOKEN: {token[:10]}... (valid)")
    else:
        print("❌ TELEGRAM_BOT_TOKEN not found!")
        return False
    
    # Test if python-telegram-bot is installed
    try:
        import telegram
        print("✅ python-telegram-bot library installed")
    except ImportError:
        print("❌ python-telegram-bot not installed!")
        return False
    
    # Test if python-dotenv is installed
    try:
        import dotenv
        print("✅ python-dotenv library installed")
    except ImportError:
        print("❌ python-dotenv not installed!")
        return False
    
    print("🎉 All environment tests passed!")
    return True

if __name__ == "__main__":
    test_environment()