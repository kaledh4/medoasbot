import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path="/root/daily_brief/.env")

def send_telegram_message(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = "54321896" # Placeholder, I should find the user's chat_id if possible
    # Wait, the bot token is from 8254321896:AAFCo5_g-QycANZyrJXbY_0kwhpVKRQbQro
    # I'll use the token from .env
    
    # I'll try to get chat_id from an environment variable or a config file
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not chat_id:
        print("TELEGRAM_CHAT_ID not set, skipping message.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False
