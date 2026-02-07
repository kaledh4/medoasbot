import sys
import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Path Setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load Env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

def health_check():
    print("🏥 STARTING SYSTEM HEALTH CHECK...")
    
    # 1. DB Connection
    db = None
    try:
        if not firebase_admin._apps:
            # Init Logic
            env_creds = os.environ.get("FIREBASE_CREDENTIALS_JSON")
            if env_creds:
                import json
                cred = credentials.Certificate(json.loads(env_creds))
                firebase_admin.initialize_app(cred)
                print("✅ Firebase Auth: Env Var Detected")
            elif os.path.exists("firebase_key.json"):
                cred = credentials.Certificate("firebase_key.json")
                firebase_admin.initialize_app(cred)
                print("✅ Firebase Auth: Key File Detected")
            else:
                firebase_admin.initialize_app()
                print("⚠️ Firebase Auth: Using Default Credentials (ADC)")
        
        db = firestore.client()
        print("✅ Database Connection: ACTIVE")
        
    except Exception as e:
        print(f"❌ CRITICAL: Database Connection Failed - {e}")
        return

    # 2. Data Integrity
    try:
        # Vendors
        vendors = list(db.collection('vendors').stream())
        print(f"📦 Vendors: {len(vendors)} found")
        
        # Categories
        cats = list(db.collection('categories').stream())
        print(f"📦 Categories: {len(cats)} found")
        
        # Active Requests
        reqs = db.collection('requests').where('status', 'in', ['OPEN', 'WAITING_OFFERS', 'NEGOTIATING']).stream()
        active_count = len(list(reqs))
        print(f"🔄 Active Requests: {active_count}")
        
    except Exception as e:
        print(f"❌ Data Access Error: {e}")

    # 3. Environment Checks
    print("\n--- Environment ---")
    print(f"DEEPSEEK_API_KEY: {'Set' if os.getenv('DEEPSEEK_API_KEY') else 'MISSING ❌'}")
    print(f"TWILIO_ACCOUNT_SID: {'Set' if os.getenv('TWILIO_ACCOUNT_SID') else 'MISSING ❌'}")
    
    print("\n✅ SYSTEM CHECK COMPLETE")

if __name__ == "__main__":
    health_check()
