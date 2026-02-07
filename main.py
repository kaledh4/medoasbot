import os
import re
import asyncio
import secrets
from firebase_admin import firestore
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pydantic import BaseModel
import uvicorn
import re
from config import SERVICES_MENU, CATEGORY_QUESTIONS, OCCASION_MENU, WA_FLOW_ID
from utils import is_cancellation # Robust Check
from services.store import store_service
from services.twilio import twilio_service
from services import ranking as ranking_service # New Ranking Engine
from services.ai_agent import receptionist # V2 Brain
from datetime import datetime
import time
import json

def classify_message_intent(message: str) -> str:
    """
    Determine the user's intent from their message.
    
    Returns:
    - "accept_offer": User wants to accept an offer
    - "reject_offer": User wants to reject offers
    - "view_offers": User wants to see their offers
    - "cancel_request": User wants to cancel (handled separately above)
    - "new_request": Default - treat as new request
    """
    msg_lower = message.lower().strip()
    
    # Accept patterns
    if any(word in msg_lower for word in ["قبول", "موافق", "تمام", "اعتمد", "قبلت", "accept"]):
        return "accept_offer"
    
    # Numbers only (1, 2, 3) = Accept that offer number
    if msg_lower.isdigit() and len(msg_lower) <= 2:
        return "accept_offer"
    
    # Reject patterns
    if any(word in msg_lower for word in ["رفض", "لا شكرا", "لا أريد", "reject", "no"]):
        return "reject_offer"
    
    # View offers patterns
    if any(word in msg_lower for word in ["عروض", "اعرض", "show", "offers"]):
        return "view_offers"
    
    # Default: new request
    return "new_request"


def parse_offer_number(message: str) -> int or None:
    """Extract offer number from message. Returns 1, 2, 3, etc. or None."""
    msg_lower = message.lower().strip()
    
    # Direct number
    if msg_lower.isdigit():
        return int(msg_lower)
    
    # "قبول 1" or "accept 2"
    match = re.search(r'(\d+)', msg_lower)
    if match:
        return int(match.group(1))
    
    return None


# ======================================
# DELETED: Marketplace Functions (Lead Gen Model)
# - handle_offer_acceptance() - No longer needed (direct contact)
# - handle_offer_rejection() - No longer needed (direct contact)
# ======================================


def handle_view_offers(request_id: str, sender: str):
    """Resend offers list to customer."""
    # Fetch offers
    offers_ref = store_service.db.collection('offers').where('request_id', '==', request_id)
    offers = list(offers_ref.stream())
    
    if not offers:
        twilio_service.send_whatsapp(
            f"whatsapp:{sender}",
            "لم تصل أي عروض بعد.\nسنخبرك فور وصول العروض! ⏳"
        )
        return
    
    # Build offers message
    msg = f"📋 *عروضك لطلب {request_id}:*\n\n"
    
    for i, offer in enumerate(offers, 1):
        offer_data = offer.to_dict()
        msg += f"{i}️⃣ *{offer_data.get('vendor_name')}*\n"
        msg += f"   السعر: {offer_data.get('price')} ريال\n\n"
    
    msg += "\n✅ *للقبول:* أرسل رقم العرض (مثال: 1)\n"
    msg += "❌ *للرفض:* أرسل 'رفض الكل'"
    
    twilio_service.send_whatsapp(f"whatsapp:{sender}", msg)
    return {"status": "offers_sent"}


def send_instant_offer_notification(request_id: str, offer_data: dict):
    """
    Send instant offer notification to customer with interactive buttons.
    Called immediately when vendor submits an offer.
    """
    from services.twilio import twilio_service
    from firebase_admin import firestore
    
    # Get request data
    request_ref = store_service.db.collection('requests').document(request_id)
    request_doc = request_ref.get()
    
    if not request_doc.exists:
        print(f"❌ Request {request_id} not found")
        return
    
    request_data = request_doc.to_dict()
    customer_phone = request_data.get('client_phone')
    
    # Ensure WhatsApp prefix
    if customer_phone and not customer_phone.startswith('whatsapp:'):
        customer_phone = f'whatsapp:{customer_phone}'
    
    if not customer_phone:
        print(f"❌ No customer phone for request {request_id}")
        return
    
    # Count offers
    all_offers = list(store_service.db.collection('offers').where('request_id', '==', request_id).stream())
    offer_num = len(all_offers)
    total_vendors = request_data.get('vendors_notified', 3)
    
    # Get latest offer ID - SIMPLIFIED to avoid composite index
    # Filter in Python instead of complex Firestore query
    vendor_phone_target = offer_data.get('vendor_phone')
    vendor_offers = [o for o in all_offers if o.to_dict().get('vendor_phone') == vendor_phone_target]
    
    if not vendor_offers:
        print(f"❌ No offers found for vendor {vendor_phone_target}")
        return
    
    # Get the latest (most recent in list)
    latest_offer = vendor_offers[-1]
    offer_id = latest_offer.id
    
    # Send direct contact card (Lead Gen Model)
    print(f"📤 Instant offer {offer_num}/{total_vendors}: {offer_data.get('vendor_name')} → {customer_phone}")
    
    try:
        # Get vendor data for contact info
        vendor_phone = offer_data.get('vendor_phone')
        vendor_id = offer_data.get('vendor_id')
        
        # Build vendor_data dict
        vendor_data = {
            'name': offer_data.get('vendor_name'),
            'phone': vendor_phone,
            'rating': offer_data.get('rating', 'NEW'),  # From offer or default
            'portfolio_image': offer_data.get('portfolio_image')
        }
        
        # Use new Lead Gen function - NO approval needed!
        twilio_service.send_direct_contact_card(
            customer_phone=customer_phone,
            vendor_data=vendor_data,
            offer_data=offer_data
        )
        
        print(f"✅ Direct contact card sent: {offer_data.get('vendor_name')}")
        
        # If all offers received, send summary
        if offer_num >= total_vendors:
            summary_msg = f"""
📊 *جميع العروض وصلت!* ({offer_num} من {total_vendors})

🔗 تم إرسال تفاصيل التواصل لكل مزود.
يمكنك التواصل مباشرة مع المزود الذي تفضله.

شكراً لاستخدامك هدهد! 🦦
            """.strip()
            
            twilio_service.send_whatsapp(customer_phone, summary_msg)
            print(f"✅ Summary sent - all {total_vendors} offers received")
    
    except Exception as e:
        print(f"❌ Error sending instant offer: {e}")
        import traceback
        traceback.print_exc()

def contains_phone_number(text):
    """
    Checks for phone numbers (English/Arabic) to prevent leaks.
    """
    # Convert Eastern Arabic Numerals
    table = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
    clean_text = text.translate(table)
    
    # Pattern: Saudi (05, 9665) OR generic 8+ digits
    pattern = r'(\+?966|0)?5\d{8}|\d{8,}'
    
    if re.search(pattern, clean_text):
        return True
    return False

load_dotenv()

app = FastAPI(title="Eventak AI Gateway", version="1.0.0")

# ===== STARTUP: Instant Offer System =====
@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup."""
    # DISABLED: Aggregation Engine (switched to instant offers)
    # from services.aggregation import aggregation_engine
    # import asyncio
    # loop = asyncio.get_event_loop()
    # loop.create_task(aggregation_engine.start_monitoring())
    
    print("🚀 Instant Offer System: Ready (immediate delivery)")




# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🛡️ SECURITY HEADERS MIDDLEWARE (Sentinel)
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Eventak AI Gateway",
        "version": "1.0.0"
    }

# Services
from services.deepseek import deepseek_service
from services.twilio import twilio_service
from services.backend import backend_service
from services.image_gen import image_service
from services.store import store_service
# from services.gemini import gemini_service

class TextRequest(BaseModel):
    text: str

@app.post("/analyze")
async def analyze_text(request: TextRequest):
    """
    Analyzes the text using the AI Service (Gemini).
    Returns intent and extracted entities.
    """
    intent = await deepseek_service.classify_intent(request.text)
    entities = await deepseek_service.extract_entities(request.text)
    
    return {
        "text": request.text,
        "classification": intent,
        "extraction": entities
    }



# Config & Helpers

async def validate_coverage(city: str, category: str) -> dict:
    """
    Validates if there are vendors available for the given city and category.
    
    Args:
        city: City name (e.g., "الرياض", "جدة")
        category: Service category (e.g., "CATERING", "PHOTOGRAPHY")
    
    Returns:
        {
            'has_coverage': bool,
            'vendor_count': int,
            'message': str  # User-facing message
        }
    """
    try:
        # Normalize city name
        city_normalized = city.strip().lower()
        
        # Query Firestore for vendors
        db = firestore.client()
        vendors_ref = db.collection('vendors')
        
        # Filter by city and category
        query = vendors_ref.where('city', '==', city_normalized)\
                          .where('category', '==', category)\
                          .where('status', '==', 'active')
        
        vendors = list(query.stream())
        vendor_count = len(vendors)
        
        if vendor_count > 0:
            return {
                'has_coverage': True,
                'vendor_count': vendor_count,
                'message': f"✅ يوجد {vendor_count} مزودين متاحين في {city}"
            }
        else:
            return {
                'has_coverage': False,
                'vendor_count': 0,
                'message': f"❌ عذراً، ما عندنا مزودين في {city} لهذا التصنيف حالياً"
            }
            
    except Exception as e:
        print(f"❌ Coverage Validation Error: {e}")
        return {
            'has_coverage': False,
            'vendor_count': 0,
            'message': "❌ حدث خطأ في التحقق من التغطية"
        }

async def lock_request(request_id: str, accepted_offer_id: str) -> bool:
    """
    Lock a request after customer accepts an offer.
    
    Args:
        request_id: The request ID
        accepted_offer_id: The offer ID that was accepted
    
    Returns:
        bool: True if locked successfully
    """
    try:
        db = firestore.client()
        request_ref = db.collection('requests').document(request_id)
        
        # Update request status
        request_ref.update({
            'status': 'COMPLETED',
            'accepted_offer_id': accepted_offer_id,
            'completed_at': firestore.SERVER_TIMESTAMP,
            'locked': True
        })
        
        print(f"🔒 Request {request_id} locked successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to lock request: {e}")
        return False

async def check_request_locked(request_id: str) -> dict:
    """
    Check if a request is locked.
    
    Returns:
        {'is_locked': bool, 'message': str}
    """
    try:
        db = firestore.client()
        request_ref = db.collection('requests').document(request_id)
        request_doc = request_ref.get()
        
        if not request_doc.exists:
            return {'is_locked': True, 'message': 'الطلب غير موجود'}
        
        request_data = request_doc.to_dict()
        status = request_data.get('status')
        
        if status == 'COMPLETED':
            return {'is_locked': True, 'message': '❌ الطلب مغلق. العميل اعتمد عرضاً آخر'}
        
        return {'is_locked': False, 'message': ''}
        
    except Exception as e:
        print(f"❌ Lock check error: {e}")
        return {'is_locked': False, 'message': ''}

from config import SERVICES_MENU, CATEGORY_QUESTIONS
from fastapi import Depends, Header

# --- Admin Dashboard API ---

class VendorModel(BaseModel):
    name: str
    phone: str
    category: str = "OTHER"
    status: str = "ACTIVE"

# Secure Admin Secret Handling
ADMIN_SECRET = os.getenv("ADMIN_SECRET")
if not ADMIN_SECRET:
    ADMIN_SECRET = secrets.token_hex(32) # 64 characters of randomness
    print(f"\n{'='*50}\n⚠️  SECURITY WARNING: ADMIN_SECRET not set!\n🔑 Generated Temporary Secret: {ADMIN_SECRET}\n{'='*50}\n")

def check_admin_auth(x_admin_secret: str = Header(None)):
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/api/vendors", dependencies=[Depends(check_admin_auth)])
async def get_vendors():
    return store_service.get_all_vendors()

@app.post("/api/vendors", dependencies=[Depends(check_admin_auth)])
async def add_vendor(vendor: VendorModel):
    new_vendor = {
        "id": f"v_{os.urandom(4).hex()}",
        "name": vendor.name,
        "phone": vendor.phone,
        "category": vendor.category,
        "status": vendor.status,
        "active_chat_client": None
    }
    store_service.add_vendor(new_vendor)
    return {"status": "success", "vendor": new_vendor}

@app.put("/api/vendors/{vendor_id}", dependencies=[Depends(check_admin_auth)])
async def update_vendor(vendor_id: str, vendor: VendorModel):
    # Only update updatable fields
    update_data = {
        "name": vendor.name,
        "phone": vendor.phone,
        "category": vendor.category,
        "status": vendor.status
    }
    updated = store_service.update_vendor(vendor_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return {"status": "updated", "vendor": updated}

@app.delete("/api/vendors/{vendor_id}", dependencies=[Depends(check_admin_auth)])
async def delete_vendor(vendor_id: str):
    store_service.delete_vendor(vendor_id)
    return {"status": "deleted"}

# --- Category API ---
class CategoryModel(BaseModel):
    title: str
    internal_id: str = "OTHER"

@app.get("/api/categories", dependencies=[Depends(check_admin_auth)])
async def get_categories():
    return store_service.get_all_categories()

@app.post("/api/categories", dependencies=[Depends(check_admin_auth)])
async def add_category(cat: CategoryModel):
    new_cat = {
        "id": f"cat_{os.urandom(4).hex()}",
        "title": cat.title,
        "internal_id": cat.internal_id.upper()
    }
    store_service.add_category(new_cat)
    return {"status": "success", "category": new_cat}

@app.delete("/api/categories/{cat_id}", dependencies=[Depends(check_admin_auth)])
async def delete_category(cat_id: str):
    store_service.delete_category(cat_id)
    return {"status": "deleted"}

# --- Client Request API (Web-First Intake) ---

class ClientRequestModel(BaseModel):
    occasion: str
    city: str
    district: str
    services: list[str]
    details: str
    date: str
    client_phone: str = "WEB_USER" # Optional: could capture phone in form

@app.post("/api/requests")
async def create_client_request(req: ClientRequestModel):
    print(f"📝 Web Request Received: {req}")
    
    # 1. Format Data for Firestore
    # Map Services
    service_map = {
        "catering": "بوفيه / ولائم", "hospitality": "ضيافة وقهوجية",
        "furniture": "طاولات وكراسي", "tents": "خيام",
        "lighting": "إضاءة وصوتيات", "decor": "تنسيق ورود",
        "photography": "تصوير", "staff": "عمالة"
    }
    services_text = ", ".join([service_map.get(s, s) for s in req.services])
    
    request_data = {
        "occasion": req.occasion,
        "city": req.city,
        "district": req.district,
        "category": "متعدد: " + services_text,
        "details": f"{req.details}\n📅 التاريخ: {req.date}\n(الخدمات: {services_text})",
        "status": "OPEN",
        "source": "web_form",
        "client_phone": req.client_phone # Should ideally be authenticated user phone
    }
    
    # 2. Save Request
    # Use a dummy phone if not provided, or better: 
    # In a real app, user is logged in. 
    # For this MVP "Intake Link", if we don't have phone, we can't notify them on WhatsApp!
    # CRITICAL: The Smart Link 'waiter' needs to link this Web Request back to the WhatsApp User.
    # We should pass ?phone=... in the URL from WhatsApp logic!
    
    # However, for now, let's assume valid generation.
    req_id = store_service.save_request(req.client_phone, request_data)
    
    # 3. Broadcast to Vendors (Real Logic)
    vendors = store_service.get_eligible_vendors(req.city, "general")
    count = 0
    for v in vendors:
        # Avoid self-message if vendor tested it
        if v.get('phone') == req.client_phone: continue
        
        tv_msg = (
            f"🔔 *طلب جديد!* (Web Form)\n"
            f"📌 التصنيف: {request_data['category']}\n"
            f"📍 الموقع: {req.city} - {req.district}\n"
            f"📝 التفاصيل: {request_data['details']}\n\n"
            "للتقديم، رد بـ *عرض سعر*."
        )
        twilio_service.send_whatsapp(f"whatsapp:{v['phone']}", tv_msg)
        count += 1
        
    print(f"🚀 Broadcasted Web Request {req_id} to {count} vendors.")
    
    # Return Info for Redirect
    return {
        "status": "success",
        "req_id": req_id,
        "bot_phone": os.getenv("TWILIO_PHONE_NUMBER", "").replace("whatsapp:", "")
    }

# --- Webhook ---

# 🔒 IDENTITY GUARD
async def get_identity(phone: str):
    db = firestore.client()
    vendors = list(db.collection('vendors').where('phone', '==', phone).limit(1).stream())
    if vendors:
        data = vendors[0].to_dict()
        data['id'] = vendors[0].id
        return ("VENDOR", data)
    user = db.collection('users').document(phone).get()
    if user.exists:
        return ("CUSTOMER", user.to_dict())
    return ("NEW_GUEST", None)

async def handle_vendor_message(phone: str, msg: str, vendor_data: dict):
    """Route vendor messages to bidding logic."""
    from services.offer_collector import offer_collector
    from services.twilio import twilio_service
    resp = offer_collector.handle_vendor_message(phone, msg)
    if resp['completed'] and resp['offer_data']:
        offer_collector.save_offer(resp['offer_data'])
        # INSTANT OFFERS: Send notification immediately instead of batching
        send_instant_offer_notification(resp['offer_data']['request_id'], resp['offer_data'])
    # FIX: Ensure whatsapp: prefix for vendor replies
    vendor_whatsapp = phone if phone.startswith('whatsapp:') else f'whatsapp:{phone}'
    twilio_service.send_whatsapp(vendor_whatsapp, resp['reply'])
    return {"status": "ok"}

@app.post("/webhook")
async def webhook(request: Request):
    # 1. Parse Data
    content_type = request.headers.get("Content-Type", "")
    if "application/json" in content_type:
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)

    sender = data.get("From", "").replace("whatsapp:", "")
    message = data.get("Body", "").strip()
    button_payload = data.get("ButtonPayload")
    
    print(f"\n📩 RECEIVED from {sender}: {message} | Payload: {button_payload}")

    # === IDENTITY GUARD: Prevent Vendor-Customer Confusion ===
    role, profile = await get_identity(sender)
    if role == "VENDOR":
        return await handle_vendor_message(sender, message, profile)
    # Continue with customer flow

    # -------------------------------------------------------------
    # 0. HANDLE WHATSAPP FLOW RESPONSE (nfm_reply)
    # -------------------------------------------------------------
    # Check for interactive message with nfm_reply
    interactive = {}
    if data.get("InteractionType") == "nfm_reply": # Twilio generic
         interactive = {"type": "nfm_reply", "nfm_reply": data.get("NfmReply")}
    elif data.get("type") == "interactive": # Standard WhatsApp Cloud API structure usually mirrored
         interactive = data.get("interactive", {})

    # In Twilio Webhook, nfm_reply often comes as 'NfmReply' in form data or JSON
    # We must be robust.
    
    if interactive.get("type") == "nfm_reply" or data.get("NfmReply"):
        print(f"🌊 Flow Response Detected!")
        try:
            resp_json = interactive.get("nfm_reply", {}).get("response_json") or data.get("NfmReply", {}).get("response_json")
            if not resp_json and isinstance(data.get("NfmReply"), str):
                 try:
                     resp_json = json.loads(data["NfmReply"])["response_json"]
                 except: 
                     resp_json = data["NfmReply"] # Sometimes it's direct

            if resp_json:
                flow_data = json.loads(resp_json)
                print(f"🌊 Flow Data Parsed: {flow_data}")

                # Extract 4-Screen Data
                # { "occasion": "...", "city": "...", "district": "...", "services": [...], "vision": "..." }
                
                # Helper to Convert Service IDs to readable text for Vendor
                service_map = {
                    "srv_catering": "بوفيه / ولائم", "srv_coffee": "ضيافة وقهوجية",
                    "srv_chairs": "طاولات وكراسي", "srv_tents": "خيام",
                    "srv_lights": "إضاءة وصوتيات", "srv_flowers": "تنسيق ورود",
                    "srv_photography": "تصوير", "srv_workers": "عمالة"
                }
                
                services_list = flow_data.get("services", [])
                # Ensure list
                if isinstance(services_list, str): services_list = [services_list]

                services_text = ", ".join([service_map.get(s, s) for s in services_list])
                
                # Map to Request Structure
                req_data = {
                    "occasion": flow_data.get("occasion", "occ_other").replace("occ_", ""),
                    "city": flow_data.get("city", "Riyadh"),
                    "district": flow_data.get("district", "Unknown"),
                    "category": "متعدد: " + services_text, 
                    "details": f"{flow_data.get('vision', '')}\n(الخدمات المطلوبة: {services_text})",
                    "client_notes": flow_data.get("vision", ""), # High Value Context
                    "status": "OPEN",
                    "source": "whatsapp_flow",
                    "flow_raw": flow_data
                }
                
                # Save Request Direct (One-Shot)
                req_id = store_service.save_request(sender, req_data)
                
                # Reset Step
                store_service.update_step(sender, 'IDLE')
                
                # Notify Client
                twilio_service.send_whatsapp(f"whatsapp:{sender}", "✅ تم استلام طلبك بنجاح! جاري إرساله لأفضل مقدمي الخدمات... 🚀")
                
                # Broadcast Logic (Inline for MVP)
                vendors = store_service.get_eligible_vendors(req_data["city"], "general") 
                
                count = 0
                for v in vendors:
                    tv_msg = f"🔔 *طلب جديد!* ({req_data['category']})\n\n📍 الموقع: {req_data['city']} - {req_data['district']}\n📝 التفاصيل: {req_data['details']}\n\nللتقديم، رد بـ *عرض سعر*."
                    twilio_service.send_whatsapp(f"whatsapp:{v['phone']}", tv_msg)
                    count += 1
                
                print(f"📢 Broadcasted Flow Request {req_id} to {count} vendors.")
                return {"status": "flow_processed", "req_id": req_id}

        except Exception as e:
            print(f"❌ Flow Parse Error: {e}")
            twilio_service.send_whatsapp(f"whatsapp:{sender}", "حدث خطأ في معالجة الطلب. يرجى المحاولة مرة أخرى.")
            return {"status": "flow_error"}


    # ==========================================================
    # SCENARIO A: Vendor Reply (Smart Bidding Engine v4.0) 💬
    # ==========================================================
    # 1. Check if Vendor is in a "Bidding State"
    vendor_state = store_service.get_vendor_state(sender)
    
    if vendor_state:
        current_status = vendor_state.get('status')
        target_request_id = vendor_state.get('current_active_request')
        temp_price = vendor_state.get('temp_price')
        
        # --- SUB-STATE: WAITING FOR PRICE 💰 ---
        if current_status == 'WAITING_FOR_PRICE':
            # Validation: Must have digits
            if not re.search(r'\d+', message):
                 twilio_service.send_whatsapp(f"whatsapp:{sender}", "⛔ *الرجاء كتابة السعر بالأرقام.*\nمثال: 450")
                 return {"status": "blocked_no_price"}

            # Save Price temporarily & Transition
            clean_price = re.search(r'\d+', message).group()
            
            # Transition to NOTE CHOICE
            store_service.set_vendor_state(sender, {
                "status": "WAITING_FOR_NOTE_CHOICE",
                "current_active_request": target_request_id,
                "temp_price": clean_price
            })
            
            # Ask Decision
            twilio_service.send_whatsapp_buttons(
                f"whatsapp:{sender}",
                f"✅ تم حفظ السعر: *{clean_price} ريال*.\nهل تريد إضافة تفاصيل؟",
                [
                    {"id": "SEND_NOW", "title": "🚀 إرسال العرض فوراً"},
                    {"id": "ADD_NOTE", "title": "📝 إضافة ملاحظة"}
                ]
            )
            return {"status": "price_received_await_choice"}

        # --- SUB-STATE: WAITING FOR NOTE CHOICE 🔀 ---
        elif current_status == 'WAITING_FOR_NOTE_CHOICE':
            choice = button_payload or message  # Handle button or text fallback
            
            if "ADD_NOTE" in choice:
                # Transition to NOTE TEXT
                store_service.set_vendor_state(sender, {
                    "status": "WAITING_FOR_NOTE_TEXT",
                    "current_active_request": target_request_id,
                    "temp_price": temp_price
                })
                twilio_service.send_whatsapp(f"whatsapp:{sender}", "📝 اكتب ملاحظاتك في رسالة واحدة:\n(مثال: شامل التوصيل والسخانات)")
                return {"status": "awaiting_note_text"}
            
            else:
                # Default/SEND_NOW -> Submit Immediate
                # Proceed to SUBMIT BLOCK at bottom
                pass

        # --- SUB-STATE: WAITING FOR NOTE TEXT 📝 ---
        elif current_status == 'WAITING_FOR_NOTE_TEXT':
             # Note text is the message
             # Proceed to SUBMIT BLOCK
             pass
        
        # --- COMMON SUBMIT BLOCK 🚀 ---
        if current_status in ['WAITING_FOR_NOTE_CHOICE', 'WAITING_FOR_NOTE_TEXT']:
            
            # Prepare Final Data
            final_note = message if current_status == 'WAITING_FOR_NOTE_TEXT' else "عرض سعر (بدون ملاحظات)"
            # Handle SEND_NOW case where message might be button ID
            if "SEND_NOW" in final_note: final_note = "عرض سعر (بدون ملاحظات)"
            
            # Lookup Request
            original_req = store_service.get_request(target_request_id)
            if not original_req:
                 twilio_service.send_whatsapp(f"whatsapp:{sender}", "⚠️ انتهت صلاحية هذا الطلب.")
                 store_service.set_vendor_state(sender, {"status": "IDLE", "current_active_request": None})
                 return {"status": "req_gone"}

            # Commit Offer
            target_client = original_req['client_phone']
            vendor_me = store_service.get_vendor_by_phone(sender)
            offer_id = f"off_{os.urandom(4).hex()}"
            
            store_service.save_offer(
                offer_id, target_client, vendor_me['id'], 
                final_note, temp_price, request_id=target_request_id
            )

            # Notify Client
            security_token = original_req.get('security_token', 'default')
            base_url = os.getenv("FRONTEND_URL", "https://eventak-head.onrender.com")
            track_link = f"{base_url}/track/{target_request_id}?token={security_token}"
            
            notify_msg = (
                f"🎉 *وصلك عرض جديد!*\n"
                f"💰 السعر: *{temp_price} ريال*\n"
                f"من: {vendor_me.get('name')}\n"
                f"📝 {final_note[:50]}...\n\n"
                f"📄 *للمقارنة والاعتماد:* 👇\n{track_link}"
            )
            
            try:
                if "WEB_USER_PENDING" not in target_client:
                    twilio_service.send_whatsapp(f"whatsapp:{target_client}", notify_msg)
            except: pass

            twilio_service.send_whatsapp(f"whatsapp:{sender}", "✅ تم إرسال العرض بنجاح! 🚀")
            
            # Reset
            store_service.set_vendor_state(sender, {"status": "IDLE", "current_active_request": None})
            return {"status": "bid_submitted_v4"}
        


    # Fallback: Check if generic vendor
    vendor_me = store_service.get_vendor_by_phone(sender)
    if vendor_me:
         # Only if NOT in bidding state
         active_client = vendor_me.get('active_chat_client')
         if active_client:
             # Proxy Reply
             twilio_service.send_whatsapp(f"whatsapp:{active_client}", f"🔔 *رد من المزود:*\n{message}")
             return {"status": "vendor_proxy"}






    print(f"DEBUG: Vendor State: {vendor_state}")
    
    # ----------------------------------------------------------
    # SCENARIO B: Client Flow (The State Machine)
    # ----------------------------------------------------------
    # ----------------------------------------------------------
    # SCENARIO A.2: Lazy Vendor Activation (The "Wake Up" Logic)
    # ----------------------------------------------------------
    vendor_me = store_service.get_vendor_by_phone(sender)
    
    # Logic: If Vendor + (Keyword OR Number) -> Activate
    is_keyword = "عرض" in message or "offer" in message.lower() or "سعر" in message
    is_numeric = re.fullmatch(r'\d+', message.strip())
    
    if vendor_me and (is_keyword or is_numeric):
         print(f"🔔 Lazy Vendor Activation: {sender}")
         
         # 1. Find the most recent OPEN request
         most_recent_req = store_service.get_latest_open_request()
             
         if most_recent_req:
             target_req_id = most_recent_req['request_id']
             
             # CASE A: Explicit Number ("300") -> S U B M I T   I M M E D I A T E L Y
             if is_numeric:
                 print(f"💰 Direct Bid Detected from Idle Vendor: {message}")
                 price_value = message.strip()
                 target_client = most_recent_req['client_phone']
                 
                 # 1. Create Offer
                 offer_id = f"off_{os.urandom(4).hex()}"
                 store_service.save_offer(
                    offer_id, 
                    target_client, 
                    vendor_me['id'], 
                    f"Offer for {target_req_id}", 
                    price_value,
                    request_id=target_req_id
                 )
                 
                 # 2. Notify Client (Copy of Scenario A Logic)
                 security_token = most_recent_req.get('security_token', 'default_token')
                 base_url = os.getenv("FRONTEND_URL", "https://eventak-head.onrender.com")
                 track_link = f"{base_url}/track/{target_req_id}?token={security_token}"
                 
                 notify_msg = (
                    f"🎉 *وصلك عرض جديد!*\n"
                    f"💰 السعر: *{price_value} ريال*\n"
                    f"من: {vendor_me.get('name')}\n\n"
                    f"📄 *لمشاهدة الصور والمقارنة واعتماد العرض:* 👇\n"
                    f"{track_link}"
                 )
                 
                 try:
                    if "WEB_USER_PENDING" in target_client:
                        print(f"⚠️ Skipping Client Notification (Pending User)")
                    else:
                        twilio_service.send_whatsapp(f"whatsapp:{target_client}", notify_msg)
                 except Exception as e:
                    print(f"❌ Client Notification Failed: {e}")

                 # 3. ACK Vendor
                 twilio_service.send_whatsapp(f"whatsapp:{sender}", "✅ تم إرسال عرضك للعميل بنجاح! (تم ربطه بآخر طلب وصلك).")
                 return {"status": "lazy_bid_auto_submitted"}

             # CASE B: Keyword ("عرض سعر") -> Ask for Price
             else:
                 # Set State to WAITING
                 store_service.set_vendor_state(sender, {
                     "status": "WAITING_FOR_BID", 
                     "current_active_request": target_req_id
                 })
                 
                 twilio_service.send_whatsapp(f"whatsapp:{sender}", 
                     f"✅ ممتاز! لقد التقطنا طلب: {most_recent_req.get('category', 'عام')}\n"
                     f"💰 *كم سعرك؟* (أرسل الرقم فقط، مثلاً: 500)")
                 return {"status": "vendor_activated"}
         else:
             twilio_service.send_whatsapp(f"whatsapp:{sender}", "⚠️ لا توجد طلبات مفتوحة حالياً.")
             return {"status": "no_open_reqs"}

    print("DEBUG: Entering Scenario B (Client Flow)")
    
    # OLD CANCELLATION CHECK REMOVED - Now handled by GATEKEEPER (line 880+)
    

    # CHECK BUTTON PAYLOADS (Interactive)
    # The payload might be in 'button_payload' OR the text body if Quick Reply
    
    # Priority: Button Payload > Text Body matching Pattern
    action_payload = button_payload or message
    
    # ----------------------------------------------------------
    # NATIVE BRIDGE HANDLER (Web Confirmation)
    # ----------------------------------------------------------
    if "CONFIRMED_REQ_" in action_payload:
        req_id = action_payload.replace("CONFIRMED_REQ_", "").strip()
        print(f"🌉 Native Bridge Confirmation: {req_id}")
        
        # Verify Request Exists?
        # For speed, we just reply. The broadcast happened in the POST API.
        
        reply_msg = (
            "✅ *تم استلام طلبك بنجاح!*\n\n"
            "جاري إرساله الآن لأفضل مقدمي الخدمات... 🚀\n"
            "بيوصلك عروض الأسعار هنا في الشات قريباً."
        )
        twilio_service.send_whatsapp(f"whatsapp:{sender}", reply_msg)
        return {"status": "native_bridge_confirmed"}

    if "ACCEPT_" in action_payload:
        # Extract ID
        offer_id = action_payload.replace("ACCEPT_", "").strip()
        print(f"✅ Accepting Offer ID: {offer_id}")
        
        # In a real DB, we fetch BY ID. 
        # But 'get_last_offer' was a hack. Let's try to find it.
        # Since we don't have get_offer_by_id exposed in store yet, we might need it.
        # However, for MVP, we can iterate or just assume if it's recent?
        # WAIT! store_service HAS 'get_last_offer', but keys are random.
        # We need `get_offer(id)`. 
        # Let's check store.py. It has `save_offer(offer_id, ...)` so it stores by ID.
        # We should add `get_offer(offer_id)` to store or use existing lookup?
        # Actually, let's look at `store_service.db.collection('offers').document(offer_id).get()`
        
        # Quick Hack using internal DB access or adding a method.
        # Adding method on fly is hard. Let's use direct access if needed or just
        # rely on 'get_last_offer' if we assume single thread? NO. User said "Multiple offers".
        
        # We need to fetch specific offer.
        # Let's Assume `store_service.get_offer(offer_id)` exists or add it?
        # Store.py: `save_offer` writes to `offers/{id}`.
        # But `get_request` exists. `get_offer` is missing?
        # `get_last_offer` uses query.
        
        # Let's add `get_offer` to store first? 
        # Or just access the private `db` if lazy? 
        # Better: Add `get_offer` to store.py in next step.
        # For NOW, I will implement the Logic assuming `store_service.get_offer(offer_id)` exists
        # and then I will go fix `store.py` immediately.
        
        target_offer = store_service.get_offer(offer_id)
        
        if target_offer:
            # 🛑 CHECK OFFER STATUS
            if target_offer.get('status') == 'REJECTED':
                twilio_service.send_whatsapp(f"whatsapp:{sender}", "⛔ لقد قمت برفض هذا العرض سابقاً.")
                return {"status": "offer_already_rejected"}
            
            if target_offer.get('status') == 'ACCEPTED':
                 twilio_service.send_whatsapp(f"whatsapp:{sender}", "✅ هذا العرض معتمد بالفعل.")
                 return {"status": "offer_already_accepted"}

            # 🛑 SECURITY CHECK Phase (The Backend Lock)
            # 1. Fetch Request Status
            req_id = target_offer.get('request_id')
            if req_id:
                request_data = store_service.get_request(req_id)
                if request_data:
                    current_status = request_data.get('status', 'OPEN')
                    
                    if current_status == 'ASSIGNED':
                         twilio_service.send_whatsapp(f"whatsapp:{sender}", "⛔ *عذراً، تم إغلاق هذا الطلب واعتماد عرض آخر.*\nلا يمكن قبول أكثر من عرض لنفس الطلب.")
                         return {"status": "request_already_assigned"}
                    
                    if current_status == 'CANCELLED':
                         twilio_service.send_whatsapp(f"whatsapp:{sender}", "⚠️ هذا الطلب ملغي.")
                         return {"status": "request_cancelled"}

            # ✅ Proceed (Lock & Load)
            # 1. Lock Request
            if req_id:
                store_service.update_request_status(req_id, 'ASSIGNED')
                
            # 2. Mark Offer as Winner
            store_service.update_offer_status(offer_id, 'ACCEPTED')
            
            # AUTO-CLOSE: Reject all other pending offers for this request
            request_id = target_offer.get('request_id')
            if request_id:
                # Get all other offers for this request
                other_offers = store_service.db.collection('offers')\
                    .where('request_id', '==', request_id)\
                    .where('status', '==', 'PENDING')\
                    .stream()
                
                for other_offer in other_offers:
                    if other_offer.id != offer_id:
                        # Auto-reject this offer
                        other_offer.reference.update({'status': 'AUTO_REJECTED'})
                        
                        # Notify vendor politely
                        other_vendor_phone = other_offer.to_dict().get('vendor_phone')
                        if other_vendor_phone:
                            twilio_service.send_whatsapp(
                                f"whatsapp:{other_vendor_phone}",
                                "شكراً لعرضك. تم اختيار مزود آخر من قبل العميل.❤️\nنتمنى لك التوفيق في الفرص القادمة!"
                            )
                        print(f"✅ Auto-rejected offer {other_offer.id}")
                
                # Update request status
                store_service.db.collection('requests').document(request_id).update({
                    'status': 'ACCEPTED',
                    'accepted_offer_id': offer_id,
                    'accepted_at': firestore.SERVER_TIMESTAMP
                })
            
            # 3. Reveal Data
            vendor = store_service.get_vendor(target_offer['vendor_id'])
            msg_to_client = (
                f"🥳 *مبروك! تم اعتماد العرض.*\n\n"
                f"تواصل مباشرة مع الأسرة المنتجة:\n"
                f"👤 الاسم: {vendor.get('name')}\n"
                f"📱 واتساب: https://wa.me/{vendor.get('phone').replace('+','')}\n\n"
                f"شكراً لثقتك في إيفنتك!"
            )
            
            # Notify Client
            twilio_service.send_whatsapp(f"whatsapp:{sender}", msg_to_client)
            
            # Notify Vendor
            twilio_service.send_whatsapp(f"whatsapp:{vendor['phone']}", f"✅ مبروك! العميل وافق على عرضك ({target_offer['price']}). سيتواصل معك الآن.")
            
            # Reset
            store_service.reset_user(sender)
            return {"status": "deal_closed"}
        else:
             twilio_service.send_whatsapp(f"whatsapp:{sender}", "⚠️ عذراً، هذا العرض لم يعد متاحاً.")
             return {"status": "offer_expired"}

    elif "REJECT_" in action_payload:
        # Extract ID
        offer_id = action_payload.replace("REJECT_", "").strip()
        target_offer = store_service.get_offer(offer_id)
        
        if target_offer:
            # Check Status
            if target_offer.get('status') == 'ACCEPTED':
                twilio_service.send_whatsapp(f"whatsapp:{sender}", "⛔ لا يمكنك رفض عرض تم اعتماده مسبقاً.")
                return {"status": "cannot_reject_accepted"}
            
            if target_offer.get('status') == 'REJECTED':
                twilio_service.send_whatsapp(f"whatsapp:{sender}", "⚠️ تم رفض هذا العرض بالفعل.")
                return {"status": "already_rejected"}

            # Mark as Rejected
            store_service.update_offer_status(offer_id, 'REJECTED')
            twilio_service.send_whatsapp(f"whatsapp:{sender}", "تم رفض العرض. ❌\nننتظر عروضاً أخرى...")
            return {"status": "offer_rejected"}
        else:
             twilio_service.send_whatsapp(f"whatsapp:{sender}", "⚠️ العرض غير موجود.")
             return {"status": "offer_not_found"}

    # Get User Step
    step = store_service.get_step(sender)
    
    # Check for List Selection ID in Payload (Interactive Answer)
    # Twilio sends list selection ID in 'ButtonPayload' or Body (if title matches)
    # in Sandbox or specific clients, the ID is sent as the Text Body.
    incoming_selection = button_payload or message.strip()

    print(f"👣 User Step: {step} | Selection: {incoming_selection}")

    # -------------------------------------------------------------
    # -------------------------------------------------------------
    # STEP 0: THE GATEKEEPER 🛡️ (Single Active Request Policy)
    # -------------------------------------------------------------
    
    # 1. Check for Active Request
    active_req = store_service.get_active_request(sender)
    
    # 2. PRIORITY: Handle "Cancel" Command FIRST (before blocking)
    is_cancel = is_cancellation(message)
    
    if is_cancel and active_req:
            print(f"🚨 CANCEL TRIGGERED for {sender} | Request: {active_req.get('request_id')}")
            # Execute Cancellation (FLUSH ALL)
            store_service.cancel_all_requests(sender)
            store_service.reset_user(sender)
            store_service.clear_conversation_history(sender)
            store_service.clear_conversation_history(sender)
            welcome_msg = (
                "يا هلا! نوّرت منصة هدهد \n"
                "نساعدك تجهز مناسباتك بأفضل الأسعار.\n"
                "دورنا نقدم لك أفضل عروض الأسعار من مقدمي الخدمات للمناسبات.\n"
                "بس نحتاج نفهم طلبك في رسالة واحدة\n"
                "مثال: أبي بوفيه عشاء لـ 20 شخص في الرياض حي الملقا يوم الجمعة الساعة 9 المساء\n"
                "آمرني.. بأيش أخدمك اليوم؟"
            )
            twilio_service.send_whatsapp(f"whatsapp:{sender}", welcome_msg)
            print(f"✅ CANCEL COMPLETED: Sent welcome message to {sender}")
            # Continue to AI to let them start immediately? Or Return?
            # Blueprint says: "Reply Done, Route to AI to start fresh."
            # So we pass through! But we need to clear message variable?
            # Actually, "Route to AI to start fresh" means let them talk.
            # But the current message was "Cancel". Sending "Cancel" to AI might trigger "Cancelled" again.
            # Let's just return to allow them to type next msg?
            # "Route to AI to start fresh" -> The USER must type a new request.
            return {"status": "request_cancelled"}
    
    
    # 3. If active request exists (and NOT canceling), handle based on intent
    if active_req:
        request_id = active_req.get('request_id')
        
        # Classify user's intent
        intent = classify_message_intent(message)
        
        print(f"🎯 Intent detected: {intent} for active request {request_id}")
        
        # ✅ ALLOW: Actions on current request
        if intent == "accept_offer":
            print(f"✅ Processing offer acceptance for {request_id}")
            result = handle_offer_acceptance(request_id, message, sender)
            return result
        
        elif intent == "reject_offer":
            print(f"❌ Processing offer rejection for {request_id}")
            result = handle_offer_rejection(request_id, message, sender)
            return result
        
        elif intent == "view_offers":
            print(f"📋 Showing offers for {request_id}")
            result = handle_view_offers(request_id, sender)
            return result
        
        # ❌ BLOCK: New request (user's intent is to create something new)
        elif intent == "new_request":
            frontend_url = os.getenv("FRONTEND_URL", "https://eventak-head-production.up.railway.app")
            if 'request_id' in active_req:
                track_link = f"{frontend_url}/track/{active_req['request_id']}"
            else:
                track_link = frontend_url
            
            block_msg = (
                "⛔ *عذراً، لديك طلب مفتوح حالياً.*\n\n"
                f"📋 رقم الطلب: {request_id}\n\n"
                "💡 *يمكنك:*\n"
                "• قبول عرض: أرسل رقم العرض (1، 2، 3)\n"
                "• رفض: أرسل 'رفض الكل'\n"
                "• مراجعة العروض: أرسل 'عروض'\n"
                "• إلغاء الطلب: أرسل 'إلغاء'\n\n"
                f"📌 لمتابعة العروض: {track_link}"
            )
            twilio_service.send_whatsapp(f"whatsapp:{sender}", block_msg)
            return {"status": "blocked_new_request_active_exists"}


    # -------------------------------------------------------------
    # STEP 1: AI RECEPTIONIST (Conversational Intake) 🧠
    # -------------------------------------------------------------
    
    # 1. Process Input via Saudi Receptionist
    print(f"🧠 AI Processing: {message}")
    
    # A. Fetch Context Memory 🧠
    history = store_service.get_conversation_history(sender)
    
    # B. Generate AI Response
    extraction = receptionist.process_input(message, conversation_history=history)
    
    # 2. Check AI Decision
    if extraction.is_canceled:
         store_service.reset_user(sender)
         store_service.clear_conversation_history(sender) # Clean Slate
         welcome_msg = (
            "يا هلا! نوّرت منصة هدهد \n"
            "نساعدك تجهز مناسباتك بأفضل الأسعار.\n"
            "دورنا نقدم لك أفضل عروض الأسعار من مقدمي الخدمات للمناسبات.\n"
            "بس نحتاج نفهم طلبك في رسالة واحدة\n"
            "مثال: أبي بوفيه عشاء لـ 20 شخص في الرياض حي الملقا يوم الجمعة الساعة 9 المساء\n"
            "آمرني.. بأيش أخدمك اليوم؟"
         )
         twilio_service.send_whatsapp(f"whatsapp:{sender}", welcome_msg)
         return {"status": "ai_cancel"}

    # C. Save User + Assistant Message to History (If not cancelled)
    # We save AFTER processing to ensure valid turn.
    store_service.append_conversation(sender, "user", message)
    store_service.append_conversation(sender, "assistant", extraction.ai_reply) # Reply is always present

    if extraction.ready_to_book:
        print(f"✅ Request Ready: {extraction.occasion} in {extraction.city}")
        
        # A. Create Request Object
        req_id = f"REQ_{os.urandom(4).hex().upper()}"
        req_data = {
            "occasion": extraction.occasion,
            "city": extraction.city,
            "district": extraction.district or "Unknown",
            "date": extraction.event_date,
            "details": extraction.details or f"AI Request: {message}",
            "category": extraction.occasion, 
            "status": "OPEN",
            "source": "ai_chat",
            "client_phone": sender,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "request_id": req_id
        }
        
        # B. Save Request (Returns ID and Token)
        saved_id, saved_token = store_service.save_request(sender, req_data)
        
        # C. Broadcast to Vendors (With Strict Matching)
        target_category = extraction.category if extraction.category else "EVENTS" # Fallback?
        vendors = store_service.get_eligible_vendors(extraction.city, target_category)
        # 🎯 Hudhud v2.0: Start bidding conversations
        from services.offer_collector import offer_collector
        count = 0
        for v in vendors:
             if v.get('phone') == sender: continue 
             
             # Build detailed vendor notification with request details
             vendor_msg = (
                 f"🔔 *طلب جديد!*\n\n"
                 f"📍 المدينة: {extraction.city}\n"
                 f"📌 المناسبة: {extraction.occasion}\n"
                 f"📅 التاريخ: {extraction.event_date}\n"
                 f"📝 التفاصيل: {req_data['details']}\n\n"
                 f"💰 *كم السعر اللي تقدر تقدمه؟*\n"
                 f"(اكتب المبلغ بالريال فقط)"
             )
             
             # Initialize offer collection state
             offer_collector.start_offer(v['phone'], saved_id, v)
             
             # Send detailed message
             twilio_service.send_whatsapp(f"whatsapp:{v['phone']}", vendor_msg)
             count += 1
             
        # 🚀 Hudhud v2.0: Initialize smart batching (5min OR 6 offers)
        from services.aggregation import aggregation_engine
        # Note: aggregation engine monitors ALL requests automatically via on_offer_received()
        
        # ✅ Confirm to User - NO tracking link!
        final_msg = (
            f"{extraction.ai_reply}\n\n"
            f"📋 *رقم الطلب:* {req_id}\n\n"
            f"✅ تم إرسال الطلب لـ {count} مزود خدمة.\n"
            f"⏱️ ستصلك العروض خلال دقائق في محادثة WhatsApp!\n"
            f"📋 بتعرض لك قائمة تقدر تختار منها"
        )
        twilio_service.send_whatsapp(f"whatsapp:{sender}", final_msg)
        
        # Wipe Memory for next fresh request
        store_service.clear_conversation_history(sender)
        
        return {"status": "ai_request_created", "req_id": req_id}
        
    else:
        # Request NOT ready -> Just send the AI reply (Question/Negotiation)
        twilio_service.send_whatsapp(f"whatsapp:{sender}", extraction.ai_reply)
        return {"status": "ai_negotiating"}

    # -------------------------------------------------------------
    # LEGACY CHAT STEPS REMOVED (Web-First / Voice Only now)
    # -------------------------------------------------------------
    # Code removed to prevent SyntaxError
    
    return {"status": "ignored"}

# -----------------------------------------------------
# API Endpoints (Viewer Logic)
# -----------------------------------------------------
@app.get("/api/public/track/{request_id}")
async def get_track_data(request_id: str, token: str):
    # 1. Fetch Request
    req_data = store_service.get_request(request_id)
    if not req_data:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # 2. Security Check
    if req_data.get('security_token') != token:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # 3. Fetch Offers
    offers = store_service.get_request_offers(request_id)
    
    # 4. Sanitize 🙈
    clean_offers = []
    for off in offers:
        vid = off.get('vendor_id')
        vendor = store_service.get_vendor(vid) or {}
        
        clean_offers.append({
            "id": off.get('id'),
            "price": off.get('price'),
            "notes": off.get('notes'),
            "status": off.get('status'),
            "vendor_name": vendor.get('name', 'Unknown'),
            "portfolio": vendor.get('portfolio', {}),
            "rating": vendor.get('rating', 5.0)
            # NO PHONE
        })
    
    # Debug log
    print(f"📡 API Track: Found {len(clean_offers)} offers for {request_id}")
        
    return {
        "request": {
            "id": request_id,
            "category": req_data.get('category_name'),
            "status": req_data.get('status'),
            "created_at": req_data.get('created_at')
        },
        "offers": clean_offers
    }

@app.post("/api/public/offer/{offer_id}/accept")
async def accept_offer_api(offer_id: str, token: str):
    # Retrieve Request ID from token validation effectively
    # Faster: Get offer -> Get Request -> Validate Token
    offer = store_service.get_offer(offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
        
    req_id = offer.get('request_id')
    req_data = store_service.get_request(req_id)
    
    # Security Check (Strict)
    stored_token = req_data.get('security_token')
    
    if not stored_token or token != stored_token:
         raise HTTPException(status_code=403, detail="Unauthorized")
         
    # EXECUTE ACCEPTANCE LOGIC
    if req_data.get('status') == 'ASSIGNED':
         raise HTTPException(status_code=400, detail="Request already closed")

    # 1. Update DB
    store_service.update_request_status(req_id, 'ASSIGNED')
    store_service.update_offer_status(offer_id, 'ACCEPTED')
    
    # 2. Notify Types (Client + Vendor)
    client_phone = req_data.get('client_phone')
    vendor_id = offer.get('vendor_id')
    vendor = store_service.get_vendor(vendor_id)
    
    # Client Msg
    twilio_service.send_whatsapp(f"whatsapp:{client_phone}", 
        f"✅ *تم اعتماد العرض بنجاح!* \n\n"
        f"تواصل مع {vendor.get('name')}: https://wa.me/{vendor.get('phone').replace('+','')}"
    )
    
    # Vendor Msg
    twilio_service.send_whatsapp(f"whatsapp:{vendor.get('phone')}",
        "🎉 *مبروك! العميل وافق على عرضك.*\nسيتم التواصل معك قريباً."
    )
    
    return {"status": "success"}

# -----------------------------------------------------
# SPA Serving (React Frontend)
# -----------------------------------------------------
from fastapi.responses import FileResponse

# 1. Serve Static Assets (JS/CSS/Images)
# Robust Path Finding
candidates = [
    os.path.join(os.getcwd(), "dist"), # Proj Root
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "dist"), # Relative to file
    "/opt/render/project/src/dist", # Hardcoded Render Path
]

DIST_DIR = None
for path in candidates:
    if os.path.exists(path):
        DIST_DIR = path
        break

# Default to first candidate if none found (for error reporting)
if not DIST_DIR:
    DIST_DIR = candidates[0]

if os.path.exists(DIST_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="assets")

# 2. Catch-All Route (Serve index.html for React Router)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Allow API calls to pass through
    if full_path.startswith("api"):
        raise HTTPException(status_code=404, detail="API Endpoint Not Found")
    
    if DIST_DIR and os.path.exists(os.path.join(DIST_DIR, "index.html")):
        return FileResponse(os.path.join(DIST_DIR, "index.html"))
    
    # ADVANCED DEBUGGING
    cwd = os.getcwd()
    try:
        files = os.listdir(cwd)
    except:
        files = ["error_reading_cwd"]
        
    return {
        "status": "frontend_lost", 
        "debug": {
            "tried_paths": candidates,
            "cwd": cwd,
            "cwd_files": files[:20], # First 20 files
            "__file__": __file__,
            "found_dist_dir": DIST_DIR,
            "exists": os.path.exists(DIST_DIR) if DIST_DIR else False
        }
    }

if __name__ == "__main__":
    import uvicorn
    # Make sure Gateway runs on 8081 to avoid conflict with Node (8080)
    port = int(os.getenv("PORT", 8081))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
