import sys
import os
import firebase_admin
from firebase_admin import credentials, firestore

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CATEGORIES = [
    {"id": "FEASTS", "title": "🍖 ولائم ومناسف", "section": "الضيافة"},
    {"id": "APPETIZERS", "title": "🥐 معجنات ومقبلات", "section": "الضيافة"},
    {"id": "SWEETS", "title": "🍰 حلى وكيك", "section": "الضيافة"},
    {"id": "TRADITIONAL", "title": "🍲 اكلات شعبية", "section": "الضيافة"},
    {"id": "COFFEE", "title": "☕ قهوة وضيافة", "section": "الضيافة"},
    {"id": "BEAUTY", "title": "💄 تجميل وميكب", "section": "تجهيز العروس"},
    {"id": "FASHION", "title": "👗 أزياء ومشاغل", "section": "تجهيز العروس"},
    {"id": "EVENTS", "title": "🎉 تنظيم وتصوير", "section": "خدمات الحفل"}
]

def seed():
    # Init DB
    if os.path.exists("firebase_key.json"):
        cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred)
    else:
        firebase_admin.initialize_app()
        
    db = firestore.client()
    print("🔥 Connected to DB")
    
    # 1. Seed Categories
    print("🌱 Seeding Categories...")
    batch = db.batch()
    for cat in CATEGORIES:
        ref = db.collection('categories').document(cat['id'])
        batch.set(ref, cat)
    batch.commit()
    print("✅ Categories Updated!")

    # 2. Update Vendor_Friend_1 to be a "Super Vendor" for testing
    print("🦸 Updating Vendor 1 (Om Sultan) to cover BEAUTY & EVENTS...")
    v1_ref = db.collection('vendors').document('vendor_friend_1')
    v1_ref.update({
        "categories": ["FEASTS", "BEAUTY", "EVENTS"],
        "serving_cities": ["Riyadh", "الرياض", "Dammam", "الدمام", "Jeddah", "جدة"] # Ensure coverage
    })
    print("✅ Vendor 1 Updated!")

if __name__ == "__main__":
    seed()
