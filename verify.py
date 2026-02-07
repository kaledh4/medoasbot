import requests
import json
import time

BASE_URL = "http://localhost:8081"

def test_analyze(text):
    print(f"\n--- Analyzing: '{text}' ---")
    try:
        response = requests.post(f"{BASE_URL}/analyze", json={"text": text})
        if response.status_code == 200:
            print("Response:", json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Connection Failed: {e}")

def main():
    print("Verifying Eventak AI Gateway...")
    
    # 1. Health Check
    try:
        resp = requests.get(f"{BASE_URL}/")
        print(f"Health Check: {resp.status_code} {resp.json()}")
    except Exception as e:
        print(f"Server not running? {e}")
        return

    # 3. Test 2-Person Flow
    print("\n--- Testing 2-Person Flow ---")
    
    client_phone = "whatsapp:+1234567890"
    vendor_phone = "whatsapp:+0987654321"

    # Step A: Client Sends Request
    print("👉 Step A: Client Request")
    requests.post(f"{BASE_URL}/webhook", json={
        "From": client_phone,
        "Body": "I need a wedding photographer in Riyadh"
    })
    time.sleep(1)

    # Step B: Vendor Sends Bid
    print("👉 Step B: Vendor Bid")
    requests.post(f"{BASE_URL}/webhook", json={
        "From": vendor_phone,
        "Body": "1500 SAR"
    })

if __name__ == "__main__":
    main()
