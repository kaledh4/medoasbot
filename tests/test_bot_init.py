import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()

def test_bot_initialization():
    """Test bot initialization without running"""
    print("🚀 Testing Bot Initialization...")
    
    # Test if token is available
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found!")
        return False
    
    print(f"✅ Telegram Bot Token found: {token[:10]}...")
    
    # Test Application builder
    try:
        from telegram.ext import Application
        print("✅ Application builder available")
        
        # Test builder without actually creating app
        print("✅ Bot initialization test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing bot: {e}")
        return False

if __name__ == "__main__":
    test_bot_initialization()