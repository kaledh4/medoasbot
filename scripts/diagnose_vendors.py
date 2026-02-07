import sys
import os
import firebase_admin
from firebase_admin import credentials, firestore

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def diagnose():
    # Redirect stdout to file with UTF-8 encoding
    with open("gateway/diagnostics_internal.log", "w", encoding="utf-8") as f:
        # Init DB (Copy logic from store.py)
        try:
            # 1. Try Env Var
            env_creds = os.environ.get("FIREBASE_CREDENTIALS_JSON")
            if env_creds:
                import json
                cred_dict = json.loads(env_creds)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                f.write("[INFO] Real Firebase Connected (Env Var)\n")
            # 2. Try Key File
            elif os.path.exists("firebase_key.json"):
                cred = credentials.Certificate("firebase_key.json")
                firebase_admin.initialize_app(cred)
                f.write("[INFO] Real Firebase Connected (Key File)\n")
            # 3. Try ADC
            else:
                firebase_admin.initialize_app()
                f.write("[INFO] Real Firebase Connected (ADC)\n")
                
            db = firestore.client()
            
            f.write("\n--- VENDOR INSPECTION ---\n")
            docs = db.collection('vendors').stream()
            count = 0
            for doc in docs:
                v = doc.to_dict()
                f.write(f"\nID: {doc.id}\n")
                f.write(f"Name_Repr: {repr(v.get('name'))}\n")
                f.write(f"Phone: {v.get('phone')}\n")
                
                cities = v.get('serving_cities')
                f.write(f"ServingCities_Repr: {repr(cities)} (Type: {type(cities)})\n")
                
                categories = v.get('categories')
                f.write(f"Categories_Repr: {repr(categories)} (Type: {type(categories)})\n")
                
                if 'city' in v:
                     f.write(f"LegacyCity_Repr: {repr(v.get('city'))}\n")
                
                count += 1
                
            f.write(f"\nTotal Vendors Found: {count}\n")
            
        except Exception as e:
            f.write(f"❌ Error: {e}\n")

if __name__ == "__main__":
    diagnose()
