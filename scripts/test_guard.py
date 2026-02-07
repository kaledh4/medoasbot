import os
import asyncio
import sys
from dotenv import load_dotenv

# Add parent dir to path to import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from services.deepseek import deepseek_service

async def test():
    print("🧪 Testing AI Guard Logic (DeepSeek)...")
    
    # Test 1: Invalid Location
    print("\n1. Testing Invalid Location ('البيت')...")
    res1 = await deepseek_service.validate_input_guard("البيت", "LOCATION")
    print(f"Result: {res1}")
    
    # Test 2: Valid Location
    print("\n2. Testing Valid Location ('الرياض حي الملقا')...")
    res2 = await deepseek_service.validate_input_guard("الرياض حي الملقا", "LOCATION")
    print(f"Result: {res2}")

    # Test 3: Valid Time with correction logic
    print("\n3. Testing Date ('بعد العشاء')...")
    res3 = await deepseek_service.validate_input_guard("بعد العشاء", "DATE")
    print(f"Result: {res3}")

    # Test 4: Context Injection (The 'Video' Problem)
    print("\n4. Testing Context Injection (Category: Photography, Input: 'Video coverage')...")
    mock_draft = {"category_name": "تصوير وميديا", "location": "الرياض", "date": "غداً"}
    res4 = await deepseek_service.validate_input_guard("تغطية فيديو", "DETAILS", full_draft=mock_draft)
    print(f"Result: {res4}")

if __name__ == "__main__":
    asyncio.run(test())
