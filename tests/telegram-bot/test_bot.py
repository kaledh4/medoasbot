import os
import time
import requests
from datetime import datetime

def send_telegram_message(message):
    """Send a message to Telegram bot"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("Telegram credentials not set!")
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False

def test_telegram_bot():
    """Test Telegram bot functionality"""
    test_message = f"🚀 Telegram Bot Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    if send_telegram_message(test_message):
        print("✅ Telegram bot test successful!")
        return True
    else:
        print("❌ Telegram bot test failed!")
        return False

if __name__ == "__main__":
    print("🔧 Testing Telegram Bot...")
    test_telegram_bot()