import os
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai

# Load env manually to be sure
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

async def main():
    api_key = os.getenv("GEMINI_API_KEY")
    print(f"🔑 API Key Loaded: {'YES' if api_key else 'NO'} ({api_key[:5]}...)")
    
    if not api_key:
        print("❌ No API Key found.")
        return

    genai.configure(api_key=api_key)
    
    print("\n🔍 Listing Models...")
    try:
        models = [m.name for m in genai.list_models()]
        print(f"📋 Found {len(models)} models: {models}")
    except Exception as e:
        print(f"❌ Failed to list models: {e}")

    print("\n🧪 Testing 'models/gemini-1.5-flash' specifically...")
    try:
        model = genai.GenerativeModel("models/gemini-1.5-flash")
        response = await model.generate_content_async("Say 'Hello Eventak' if you are working.")
        print(f"✅ Response: {response.text}")
    except Exception as e:
        print(f"❌ Generation Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
