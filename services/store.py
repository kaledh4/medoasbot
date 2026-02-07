import firebase_admin
from firebase_admin import credentials, firestore
import os
import time
import sys

class StoreService:
    def __init__(self):
        self.db = None
        self.last_active_client = "966551315886" # Default Fallback
        self._init_db()

    def _init_db(self):
        try:
            # 1. NEW: Try Env Var (Secure for Render)
            env_creds = os.environ.get("FIREBASE_CREDENTIALS_JSON")
            if env_creds:
                import json
                cred_dict = json.loads(env_creds)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                self.db = firestore.client()
                print("🔥 Real Firebase Connected (Env Var)")
                return

            # 2. Try Key File (Local Dashboard)
            if os.path.exists("firebase_key.json"):
                cred = credentials.Certificate("firebase_key.json")
                firebase_admin.initialize_app(cred)
                self.db = firestore.client()
                print("🔥 Real Firebase Connected (Key File)")
            # 3. Try ADC (Render/Cloud Fallback)
            else:
                firebase_admin.initialize_app()
                self.db = firestore.client()
                print("🔥 Real Firebase Connected (ADC)")

        except Exception as e:
            print(f"❌ FATAL: Firebase Init Failed. Mock Data is FORBIDDEN. Exiting.")
            raise e

    def save_request(self, client_phone, draft_data):
        import uuid
        # Use existing ID or Generate new
        req_id = draft_data.get('request_id') or f"REQ_{str(uuid.uuid4())[:8].upper()}"
        
        # Generate Security Token (Required for Tracking)
        token = str(uuid.uuid4())
        
        clean_client = client_phone.replace("whatsapp:", "")
        data = {
            "request_id": req_id,
            "security_token": token,
            "client_phone": clean_client,
            "details": draft_data.get('details'),
            "category": draft_data.get('category'),
            "location": draft_data.get('location'),
            
            "city": draft_data.get('city'),
            "district": draft_data.get('district'),
            "occasion": draft_data.get('occasion'),
            "date": draft_data.get('date'),
            
            "status": "OPEN",
            "timestamp": firestore.SERVER_TIMESTAMP,
            "source": "WEB"
        }
        
        self.db.collection('requests').document(req_id).set(data)
        return req_id, token

    def get_request(self, req_id):
        doc = self.db.collection('requests').document(req_id).get()
        if doc.exists:
            return doc.to_dict()
        return None

    def get_offer(self, offer_id):
        doc = self.db.collection("offers").document(offer_id).get()
        if doc.exists:
            return doc.to_dict()
        return None

    # --- Gatekeeper Logic 🛡️ ---
    def get_active_request(self, phone):
        """
        Check if user has an OPEN, WAITING_OFFERS, or NEGOTIATING request.
        """
        clean_phone = phone.replace("whatsapp:", "")
        
        print(f"🔍 CANCEL DEBUG: Searching for active requests for {clean_phone}")
        
        docs = self.db.collection('requests')\
            .where('client_phone', '==', clean_phone)\
            .where('status', 'in', ["OPEN", "WAITING_OFFERS", "NEGOTIATING"])\
            .limit(1)\
            .stream()
            
        for doc in docs:
            return doc.to_dict() # Return first active found
        return None

    def check_city_coverage(self, city_name):
        """
        Check if ANY vendor contributes to this city.
        """
        if not city_name: return False
        
        # Firestore Array Contains
        results = self.db.collection('vendors').where('serving_cities', 'array_contains', city_name).limit(1).get()
        if results: return True
        
        # Fallback: Try Capitalized
        results = self.db.collection('vendors').where('serving_cities', 'array_contains', city_name.capitalize()).limit(1).get()
        return len(results) > 0

    def cancel_all_requests(self, phone):
        """
        Emergency FLUSH: Cancel ALL active requests for this user.
        """
        clean_phone = phone.replace("whatsapp:", "")
        
        
        docs = self.db.collection('requests')\
            .where('client_phone', '==', clean_phone)\
            .where('status', 'in', ["OPEN", "WAITING_OFFERS", "NEGOTIATING"])\
            .stream()
            
        batch = self.db.batch()
        count = 0
        cancelled_ids = []
        for doc in docs:
            ref = self.db.collection('requests').document(doc.id)
            batch.update(ref, {"status": "CANCELLED"})
            cancelled_ids.append(doc.id)
            count += 1
        
        if count > 0:
            batch.commit()
            print(f"✅ CANCEL SUCCESS: Cancelled {count} requests: {cancelled_ids}")
            print(f"🧹 Flushed {count} active requests for {clean_phone}")

    def get_request_offers(self, request_id):
        """Fetch all offers for a request"""
        docs = self.db.collection("offers").where("request_id", "==", request_id).stream()
        results = []
        for d in docs:
            data = d.to_dict()
            data['id'] = d.id
            results.append(data)
        return results

    def set_vendor_state(self, vendor_phone, state_data):
        clean_phone = vendor_phone.replace("whatsapp:", "").replace("+", "")
        self.db.collection('vendor_states').document(clean_phone).set(state_data, merge=True)

    def get_vendor_state(self, vendor_phone):
        clean_phone = vendor_phone.replace("whatsapp:", "").replace("+", "")
        doc = self.db.collection('vendor_states').document(clean_phone).get()
        if doc.exists:
            return doc.to_dict()
        return None
    
    def set_last_active_client(self, phone):
        self.last_active_client = phone.replace("whatsapp:", "")

    def get_last_active_client(self):
        return self.last_active_client

    # --- Matching Engine ---
    def get_eligible_vendors(self, city, category_key):
        """
        Returns list of vendors matching STRICT criteria from Golden Master:
        1. Serves the City (serving_cities CONTAINS request city)
        2. Serves the Category (categories CONTAINS request category)
        """
        all_vendors = self.get_all_vendors()
        matched = []
        
        target_city = city.strip().lower() if city else ""
        
        for v in all_vendors:
            # --- 1. City Match ---
            v_cities = [str(c).lower() for c in v.get('serving_cities', [])]
            # Legacy fallback
            if 'city' in v and v['city']: 
                v_cities.append(str(v['city']).lower())
            
            city_match = any(target_city in vc or vc in target_city for vc in v_cities)
            
            if not city_match:
                continue

            # --- 2. Category Match ---
            v_cats = v.get('categories', [])
            if not isinstance(v_cats, list):
                v_cats = []
                
            if category_key not in v_cats:
                 continue
                 
            matched.append(v)
            
        print(f"🤝 Matching Engine: Found {len(matched)} vendors for {category_key} in {city}")
        return matched

    def get_user_state(self, phone):
        """Returns {current_state, active_vendor_id}"""
        clean_phone = phone.replace("whatsapp:", "")
        
        doc = self.db.collection('users').document(clean_phone).get()
        if doc.exists:
            data = doc.to_dict()
            if "current_state" not in data: data["current_state"] = "IDLE"
            if "active_vendor_id" not in data: data["active_vendor_id"] = None
            if "step" not in data: data["step"] = "START"
            return data
            
        return {"current_state": "IDLE", "active_vendor_id": None, "step": "START"}

    def set_user_state(self, phone, state, vendor_id=None):
        clean_phone = phone.replace("whatsapp:", "")
        data = {
            "current_state": state,
            "active_vendor_id": vendor_id
        }
        self.db.collection('users').document(clean_phone).set(data, merge=True)

    def save_offer(self, offer_id, client_phone, vendor_id, details, price, request_id):
        clean_client = client_phone.replace("whatsapp:", "")
        
        # 1. Fetch Vendor Snapshot
        vendor_data = self.get_vendor(vendor_id)
        vendor_name = vendor_data.get('name', 'Unknown Vendor') if vendor_data else 'Unknown Vendor'
        vendor_rating = vendor_data.get('rating', 'New') if vendor_data else 'New'
        
        # Portfolio Image Logic (Backwards Compatibility)
        # Try to find 'portfolio_images' list, else 'cover_image' inside portfolio dict
        portfolio_snapshot = {}
        if vendor_data:
            portfolio = vendor_data.get('portfolio', {})
            if isinstance(portfolio, dict):
                 portfolio_snapshot['cover_image'] = portfolio.get('cover_image')
            
            # Allow rich gallery if available
            portfolio_snapshot['gallery'] = vendor_data.get('portfolio_images', [])

        data = {
            "offer_id": offer_id,
            "request_id": request_id, 
            "client_phone": clean_client,
            "vendor_id": vendor_id,
            "vendor_name": vendor_name, # Snapshot name
            "rating": vendor_rating,    # Snapshot rating
            "portfolio": portfolio_snapshot, # Snapshot images
            "details": details,
            "price": price,
            "status": "PENDING", 
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        self.db.collection('offers').document(offer_id).set(data)
    
    def update_request_status(self, req_id, status):
        self.db.collection('requests').document(req_id).update({"status": status})

    def update_offer_status(self, offer_id, status):
        self.db.collection('offers').document(offer_id).update({"status": status})

    def reject_other_offers(self, req_id, winner_offer_id):
        # Implementation depends on business logic, currently placeholder in original
        pass

    def get_last_offer(self, client_phone):
        clean_client = client_phone.replace("whatsapp:", "")
        docs = self.db.collection('offers').where('client_phone', '==', clean_client)\
                 .order_by('timestamp', direction=firestore.Query.DESCENDING).limit(1).get()
        if docs:
            return docs[0].to_dict()
        return None

    def get_latest_open_request(self):
        try:
            # FIX: Remove order_by to avoid "Composite Index" requirement errors
            docs_stream = self.db.collection('requests').where('status', '==', 'OPEN').stream()
            
            all_open = []
            for doc in docs_stream:
                d = doc.to_dict()
                # Ensure timestamp exists
                if 'timestamp' in d:
                    all_open.append(d)
            
            # Sort in Python (Descending)
            if all_open:
                # Handle Firestore Timestamp objects or generic time
                all_open.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
                return all_open[0]
                
            return None
        except Exception as e:
            print(f"⚠️ Error fetching latest request: {e}")
            return None

    def get_vendor(self, vendor_id):
        doc = self.db.collection('vendors').document(vendor_id).get()
        if doc.exists:
            return doc.to_dict()
        return None
    
    def get_vendor_by_phone(self, phone):
        clean_phone = phone.replace("whatsapp:", "").replace("+", "")
        q_phone = "+" + clean_phone if not clean_phone.startswith("+") else clean_phone
        docs = self.db.collection('vendors').where('phone', '==', q_phone).stream()
        for doc in docs:
            return doc.to_dict()
        return None

    def set_vendor_active_chat(self, vendor_id, client_phone):
        self.db.collection('vendors').document(vendor_id).update({
            "active_chat_client": client_phone
        })

    def update_vendor_metrics(self, vendor_id, response_speed_seconds):
        vendor = self.get_vendor(vendor_id)
        if not vendor: return

        current_avg = vendor.get('average_response_seconds')
        total_offers = int(vendor.get('metrics_total_offers', 0))
        
        if current_avg is None:
            new_avg = response_speed_seconds
        else:
            new_avg = ((float(current_avg) * total_offers) + response_speed_seconds) / (total_offers + 1)
            
        update_data = {
            "average_response_seconds": round(new_avg, 2),
            "metrics_total_offers": total_offers + 1,
            "last_active_at": firestore.SERVER_TIMESTAMP
        }
        self.db.collection('vendors').document(vendor_id).update(update_data)

    # --- Vendor Management (Admin Dashboard) ---
    def get_all_vendors(self):
        vendors = []
        docs = self.db.collection('vendors').stream()
        for doc in docs:
            vendors.append(doc.to_dict())
        return vendors

    def add_vendor(self, vendor_data):
        self.db.collection('vendors').document(vendor_data['id']).set(vendor_data)
        return vendor_data

    def update_vendor(self, vendor_id, update_data):
        self.db.collection('vendors').document(vendor_id).update(update_data)
        return {"id": vendor_id, **update_data}

    def delete_vendor(self, vendor_id):
        self.db.collection('vendors').document(vendor_id).delete()
        return True

    # --- Category Management ---
    def get_all_categories(self):
        cats = []
        try:
            docs = self.db.collection('categories').stream()
            for doc in docs:
                cats.append(doc.to_dict())
        except:
            pass
        return cats

    def add_category(self, cat_data):
        self.db.collection('categories').document(cat_data['id']).set(cat_data)
        return cat_data

    def delete_category(self, cat_id):
        self.db.collection('categories').document(cat_id).delete()
        return True

    def get_draft(self, phone):
        clean_phone = phone.replace("whatsapp:", "")
        doc = self.db.collection('users').document(clean_phone).get()
        if doc.exists:
            return doc.to_dict().get("draft", "")
        return ""

    def save_draft(self, phone, context):
        clean_phone = phone.replace("whatsapp:", "")
        self.db.collection('users').document(clean_phone).set({"draft": context}, merge=True)

    def clear_draft(self, phone):
        clean_phone = phone.replace("whatsapp:", "")
        self.db.collection('users').document(clean_phone).update({"draft": firestore.DELETE_FIELD})

    # --- AI Context Memory 🧠 ---
    def append_conversation(self, phone, role, content):
        clean_phone = phone.replace("whatsapp:", "")
        msg = {"role": role, "content": content, "timestamp": time.time()}
        
        doc_ref = self.db.collection('users').document(clean_phone)
        try:
            doc = doc_ref.get()
            current_hist = []
            if doc.exists:
                current_hist = doc.to_dict().get('conversation_history', [])
            
            current_hist.append(msg)
            # Keep last 10
            if len(current_hist) > 10:
                current_hist = current_hist[-10:]
            
            doc_ref.set({"conversation_history": current_hist}, merge=True)
        except Exception as e:
            print(f"⚠️ Memory Error: {e}")

    def get_conversation_history(self, phone):
        clean_phone = phone.replace("whatsapp:", "")
        doc = self.db.collection('users').document(clean_phone).get()
        if doc.exists:
            raw = doc.to_dict().get('conversation_history', [])
            return [{"role": m["role"], "content": m["content"]} for m in raw]
        return []

    def clear_conversation_history(self, phone):
        clean_phone = phone.replace("whatsapp:", "")
        try:
            self.db.collection('users').document(clean_phone).update({"conversation_history": firestore.DELETE_FIELD})
        except:
            pass

    # --- Draft & State Management (Eventak 3.0) ---
    def update_step(self, phone, step):
        clean_phone = phone.replace("whatsapp:", "")
        self.db.collection('users').document(clean_phone).set({"step": step}, merge=True)

    def get_step(self, phone):
        user_data = self.get_user_state(phone)
        return user_data.get("step", "START")

    def save_draft_field(self, phone, key, value):
        clean_phone = phone.replace("whatsapp:", "")
        self.db.collection('users').document(clean_phone).set({
            "draft_data": {key: value}
        }, merge=True)

    def get_draft_value(self, phone, key):
        clean_phone = phone.replace("whatsapp:", "")
        doc = self.db.collection('users').document(clean_phone).get()
        if doc.exists:
            data = doc.to_dict()
            return data.get("draft_data", {}).get(key)
        return None

    def get_full_draft(self, phone):
        clean_phone = phone.replace("whatsapp:", "")
        doc = self.db.collection('users').document(clean_phone).get()
        if doc.exists:
            return doc.to_dict().get("draft_data", {})
        return {}
    
    def reset_user(self, phone):
        clean_phone = phone.replace("whatsapp:", "")
        self.db.collection('users').document(clean_phone).set({
            "step": "START",
            "draft_data": {}
        }, merge=True)

store_service = StoreService()
