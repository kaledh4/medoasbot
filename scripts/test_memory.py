import sys
import os
import time

# Add parent directory to path to import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.store import store_service

def test_memory():
    phone = "whatsapp:+966500000000"
    
    print(f"🧹 Clearing history for {phone}...")
    store_service.clear_conversation_history(phone)
    
    initial = store_service.get_conversation_history(phone)
    print(f"Empty History: {initial} (Expected [])")
    assert initial == []
    
    print("📝 Appending User Message...")
    store_service.append_conversation(phone, "user", "Hello Eventak")
    
    print("📝 Appending AI Message...")
    store_service.append_conversation(phone, "assistant", "Ahlan! How can I help?")
    
    history = store_service.get_conversation_history(phone)
    print(f"History after 2 messages: {history}")
    
    assert len(history) == 2
    assert history[0]['role'] == 'user'
    assert history[0]['content'] == 'Hello Eventak'
    assert history[1]['role'] == 'assistant'
    
    print("📝 Appending 9 more messages to test limit (10)...")
    for i in range(9):
        store_service.append_conversation(phone, "user", f"Msg {i}")
        
    final_history = store_service.get_conversation_history(phone)
    print(f"Final History Len: {len(final_history)}")
    print(f"Final History: {[m['content'] for m in final_history]}")
    
    assert len(final_history) == 10
    # The first messages should be gone
    assert final_history[0]['content'] != 'Hello Eventak'
    assert final_history[-1]['content'] == 'Msg 8'
    
    print("\n✅ Memory Test Passed!")

if __name__ == "__main__":
    try:
        test_memory()
    except AssertionError as e:
        print(f"\n❌ Test Failed: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
