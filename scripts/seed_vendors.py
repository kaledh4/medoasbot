import firebase_admin
from firebase_admin import credentials, firestore
import os

def seed_db():
    if not os.path.exists("firebase_key.json"):
        print("❌ Connect Key missing.")
        return

    # Connect
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("🔥 Connected for Seeding...")

    # Data to Upload
    vendors = [
        {
            "id": "vendor_friend_1",
            "phone": "+966535910204",
            "name": "أم سلطان",
            "status": "ACTIVE",
            "rating": 4.9,
            "categories": ["cat_catering", "cat_food"]
        },
        {
            "id": "vendor_friend_2",
            "phone": "+966596268690",
            "name": "الشيف أحمد",
            "status": "ACTIVE",
            "rating": 4.7,
            "categories": ["cat_catering", "cat_food"]
        },
        {
            "id": "vendor_friend_3",
            "phone": "+966538463004",
            "name": "أم عمر",
            "status": "ACTIVE",
            "rating": 4.8,
            "categories": ["cat_sweets", "cat_gifts"]
        }
    ]

    # Upload
    for v in vendors:
        db.collection('vendors').document(v['id']).set(v)
        print(f"✅ Uploaded: {v['name']}")

    print("🎉 Seeding Complete!")

if __name__ == "__main__":
    seed_db()
