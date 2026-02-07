import os
import asyncio
from dotenv import load_dotenv
from openai import OpenAI

# Load env manually
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def main():
    api_key = os.getenv("DEEPSEEK_API_KEY")
    print(f"🔑 API Key Loaded: {'YES' if api_key else 'NO'}")
    
    if not api_key:
        print("❌ No API Key found.")
        return

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )

    print("\n🧪 Testing DeepSeek Chat...")
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'DeepSeek is Online'"}
            ],
            stream=False
        )
        print(f"✅ Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Generation Failed: {e}")

if __name__ == "__main__":
    main()
