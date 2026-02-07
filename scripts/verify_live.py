import sys
import os
from dotenv import load_dotenv
from twilio.rest import Client
from openai import OpenAI

# Load .env explicitly
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(env_path)

def test_live():
    print("🔌 LIVE CONNECTIVITY TEST")
    print(f"Loading env from: {env_path}")
    
    # 1. Twilio Test
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    
    print(f"\n📱 Twilio Check (SID: {sid[:6] if sid else 'None'}...)")
    
    try:
        client = Client(sid, token)
        # Fetch Account to verify creds
        account = client.api.accounts(sid).fetch()
        print(f"✅ Twilio Auth Success! Status: {account.status} | Type: {account.type}")
    except Exception as e:
        print(f"❌ Twilio Failed: {e}")

    # 2. DeepSeek Test
    ak = os.getenv("DEEPSEEK_API_KEY")
    print(f"\n🧠 DeepSeek Check (Key: {ak[:6] if ak else 'None'}...)")
    
    try:
        client = OpenAI(api_key=ak, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": "Say 'Online'"}],
            max_tokens=5
        )
        print(f"✅ DeepSeek Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ DeepSeek Failed: {e}")

if __name__ == "__main__":
    test_live()
