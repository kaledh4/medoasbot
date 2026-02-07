
import sys
import os
import firebase_admin
from firebase_admin import credentials, firestore

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MAPPING = {
    "cat_catering": "FEASTS",   # ولائم
    "cat_coffee": "COFFEE",     # قهوة
    "cat_gifts": "GIFTS",       # هدايا
    "cat_equipment": "EVENTS",  # معدات -> EVENTS (General)
    "cat_photo": "EVENTS",      # تصوير -> EVENTS
    "cat_beauty": "BEAUTY",     # تجميل
    "cat_ent": "EVENTS",        # ترفيه
    "cat_other": "EVENTS"
}

DEFAULT_CITIES = ["Riyadh", "الرياض", "Dammam", "الدمام", "Jeddah", "جدة", "Khobar", "الخبر"]

def migrate():
    # Init DB
    if os.path.exists("firebase_key.json"):
        cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred)
    else:
        firebase_admin.initialize_app()
        
    db = firestore.client()
    print("🔥 Connected to DB")
    
    docs = db.collection('vendors').stream()
    batch = db.batch()
    count = 0
    
    for doc in docs:
        v = doc.to_dict()
        ref = db.collection('vendors').document(doc.id)
        updates = {}
        
        # 1. Fix Categories
        current_cats = v.get('categories', [])
        new_cats = set()
        
        # If it's a list, iterate
        if isinstance(current_cats, list):
            for c in current_cats:
                # If matches mapping key, use value
                if c in MAPPING:
                    new_cats.add(MAPPING[c])
                # If it IS a value (already migrated?), keep it
                elif c in MAPPING.values():
                    new_cats.add(c)
                # Fallback
                else:
                    new_cats.add("EVENTS")
        
        # Update if changed
        final_list = list(new_cats)
        if final_list:
            updates['categories'] = final_list
            
        # 2. Fix Cities (If None or Empty)
        current_cities = v.get('serving_cities')
        if not current_cities:
            updates['serving_cities'] = DEFAULT_CITIES
        
        if updates:
            print(f"🛠️ Migrating {doc.id} -> {updates}")
            batch.update(ref, updates)
            count += 1
            
    if count > 0:
        batch.commit()
        print(f"✅ Migrated {count} vendors successfully!")
    else:
        print("🎉 No vendors needed migration.")

if __name__ == "__main__":
    migrate()
