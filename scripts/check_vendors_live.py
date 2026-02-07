import firebase_admin
from firebase_admin import credentials, firestore
import os

def check_vendors():
    # 1. Connect to Real DB
    if not os.path.exists("firebase_key.json"):
        print("❌ Error: firebase_key.json not found!")
        return

    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("🔥 Connected to Firestore.")

    # 2. Query Vendors
    docs = db.collection('vendors').stream()
    vendors = []
    for doc in docs:
        v = doc.to_dict()
        vendors.append(v)

    # 3. Report
    print(f"\n📊 Total Vendors Found: {len(vendors)}")
    print("-" * 30)
    for i, v in enumerate(vendors, 1):
        status = v.get('status', 'MISSING')
        phone = v.get('phone', 'MISSING')
        name = v.get('name', 'Unknown')
        print(f"{i}. {name} | Phone: {phone} | Status: {status}")
    print("-" * 30)

if __name__ == "__main__":
    check_vendors()
