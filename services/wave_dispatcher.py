"""
Wave Dispatcher Service for Lead Gen Model.

Manages cascading vendor dispatch with timing:
- Wave 1 (T+0): Top 5 vendors
- Wave 2 (T+5min): Next 5 vendors (if <3 replies)
- Timeout (T+10min): Apologize if 0 replies
"""

import asyncio
from datetime import datetime
from firebase_admin import firestore
from typing import List, Dict

class WaveDispatcher:
    """
    Cascading vendor dispatch system.
    
    Sends vendors in waves with delays to avoid overwhelming customers.
    """
    
    def __init__(self, db, twilio_service):
        self.db = db
        self.twilio = twilio_service
        self.wave_size = 5
        self.wave_2_delay = 300  # 5 minutes
        self.timeout_delay = 600  # 10 minutes
        
    async def dispatch_wave_1(self, request_id: str, city: str, category: str, request_text: str):
        """
        Initial dispatch to top 5 vendors.
        
        Args:
            request_id: The request ID
            city: Customer's city
            category: Service category
            request_text: Full request text for vendors
        """
        print(f"🌊 Wave 1 Dispatcher: Starting for {request_id}")
        
        # Get ALL vendors for this city+category
        all_vendors = self._query_vendors(city, category)
        total_count = len(all_vendors)
        
        print(f"📊 Total vendors available: {total_count}")
        
        if total_count == 0:
            # No vendors - notify customer immediately
            req_doc = self.db.collection('requests').document(request_id).get()
            customer_phone = req_doc.to_dict().get('client_phone')
            
            sorry_msg = """
عذراً، لا يوجد مزودون متاحون حالياً في منطقتك لهذه الخدمة. 😔

يمكنك:
• جرب مدينة أخرى
• اختر فئة خدمة مختلفة
• تواصل معنا مباشرة للمساعدة

شكراً لثقتك في هدهد! 🦅
            """.strip()
            
            self.twilio.send_whatsapp(f"whatsapp:{customer_phone}", sorry_msg)
            return {"wave": 0, "count": 0, "status": "no_vendors"}
        
        # Take top 5 (by rating)
        wave_1_vendors = all_vendors[:self.wave_size]
        
        # Check if we have enough for wave 2
        fully_dispatched = (total_count <= self.wave_size)
        
        # Update request with dispatch tracking
        self.db.collection('requests').document(request_id).update({
            'dispatched_vendors': [v['id'] for v in wave_1_vendors],
            'wave_number': 1,
            'fully_dispatched': fully_dispatched,
            'wave_1_sent_at': firestore.SERVER_TIMESTAMP,
            'total_vendors_available': total_count
        })
        
        # Send template messages to Wave 1 vendors
        for vendor in wave_1_vendors:
            self._send_opportunity(vendor, request_id, request_text)
        
        print(f"✅ Wave 1: Dispatched to {len(wave_1_vendors)} vendors")
        
        # Schedule wave 2 (if more vendors available)
        if not fully_dispatched:
            print(f"⏱️ Wave 2 scheduled in {self.wave_2_delay}s")
            asyncio.create_task(
                self._schedule_wave_2(request_id, city, category, request_text)
            )
        else:
            print(f"⚠️ No Wave 2 needed - only {total_count} vendors total")
        
        # Always schedule timeout handler
        asyncio.create_task(
            self._schedule_timeout(request_id)
        )
        
        return {
            "wave": 1,
            "count": len(wave_1_vendors),
            "total_available": total_count,
            "wave_2_needed": not fully_dispatched
        }
    
    async def _schedule_wave_2(self, request_id: str, city: str, category: str, request_text: str):
        """
        Wait 5min then check if wave 2 needed.
        """
        await asyncio.sleep(self.wave_2_delay)
        
        print(f"⏰ Wave 2 Timer: Checking need for {request_id}")
        
        # Get request status
        req_doc = self.db.collection('requests').document(request_id).get()
        if not req_doc.exists:
            print(f"❌ Request {request_id} not found - cancelled")
            return
        
        req_data = req_doc.to_dict()
        
        # Count replies received so far
        offers_count = len(list(
            self.db.collection('offers')
            .where('request_id', '==', request_id)
            .stream()
        ))
        
        print(f"📊 Current offers: {offers_count}")
        
        # Should we send wave 2?
        if offers_count >= 3:
            print(f"✋ Wave 2 CANCELLED: {offers_count} offers already received")
            return
        
        if req_data.get('fully_dispatched'):
            print(f"✋ Wave 2 CANCELLED: no more vendors available")
            return
        
        # Dispatch Wave 2
        print(f"🌊 Wave 2: Dispatching ({offers_count} replies so far)")
        
        all_vendors = self._query_vendors(city, category)
        dispatched_ids = req_data.get('dispatched_vendors', [])
        
        # Get next 5 vendors (not yet contacted)
        wave_2_vendors = [
            v for v in all_vendors 
            if v['id'] not in dispatched_ids
        ][:self.wave_size]
        
        if not wave_2_vendors:
            print("⚠️ No additional vendors for Wave 2")
            return
        
        # Update request
        self.db.collection('requests').document(request_id).update({
            'dispatched_vendors': firestore.ArrayUnion([v['id'] for v in wave_2_vendors]),
            'wave_number': 2,
            'wave_2_sent_at': firestore.SERVER_TIMESTAMP
        })
        
        # Send to Wave 2 vendors
        for vendor in wave_2_vendors:
            self._send_opportunity(vendor, request_id, request_text)
        
        print(f"✅ Wave 2: Dispatched to {len(wave_2_vendors)} vendors")
    
    async def _schedule_timeout(self, request_id: str):
        """
        Wait 10min then apologize if no offers received.
        """
        await asyncio.sleep(self.timeout_delay)
        
        print(f"⏰ Timeout Handler: Checking {request_id}")
        
        # Count final offers
        offers_count = len(list(
            self.db.collection('offers')
            .where('request_id', '==', request_id)
            .stream()
        ))
        
        if offers_count == 0:
            # Get customer phone
            req_doc = self.db.collection('requests').document(request_id).get()
            if not req_doc.exists:
                return
            
            customer_phone = req_doc.to_dict().get('client_phone')
            
            apology_msg = """
عذراً، لم يرد أي مزود على طلبك حتى الآن. 😔

*ماذا تفعل الآن؟*
• انتظر قليلاً - قد يرد مزود متأخر
• أرسل طلب جديد بتفاصيل مختلفة
• تواصل معنا مباشرة للمساعدة

شكراً لصبرك وثقتك في هدهد! 🦅
            """.strip()
            
            self.twilio.send_whatsapp(f"whatsapp:{customer_phone}", apology_msg)
            
            # Update request status
            self.db.collection('requests').document(request_id).update({
                'status': 'NO_RESPONSES',
                'timeout_at': firestore.SERVER_TIMESTAMP
            })
            
            print(f"⏰ Timeout: Sent apology for {request_id} (0 offers)")
        else:
            print(f"✅ Timeout: {request_id} has {offers_count} offers - no apology needed")
    
    def _query_vendors(self, city: str, category: str) -> List[Dict]:
        """
        Get all active vendors for city+category, sorted by rating.
        
        Returns:
            List of vendor dicts with 'id' field added
        """
        vendors = list(
            self.db.collection('vendors')
            .where('city', '==', city)
            .where('category', '==', category)
            .where('status', '==', 'ACTIVE')
            .stream()
        )
        
        # Convert to dicts and add ID
        vendors_data = [
            {**v.to_dict(), 'id': v.id}
            for v in vendors
        ]
        
        # Sort by rating (highest first), then by created_at
        vendors_data.sort(
            key=lambda x: (x.get('rating', 0), x.get('created_at', datetime.min)),
            reverse=True
        )
        
        return vendors_data
    
    def _send_opportunity(self, vendor: Dict, request_id: str, request_text: str):
        """
        Send opportunity notification to vendor.
        
        Args:
            vendor: Vendor data dict
            request_id: Request ID
            request_text: Customer's request description
        """
        msg = f"""
🎯 *فرصة عمل جديدة!*

📋 *الطلب:*
{request_text[:200]}{'...' if len(request_text) > 200 else ''}

💰 *كيف تفوز بهذا العميل؟*
فقط أرسل سعرك بالريال (مثال: 500)

⚡ *كن سريعاً!* أول من يرد له الأفضلية
        """.strip()
        
        vendor_phone = vendor.get('phone')
        if vendor_phone:
            self.twilio.send_whatsapp(f"whatsapp:{vendor_phone}", msg)
            print(f"📤 Opportunity sent to: {vendor.get('name')} ({vendor_phone})")


# Create singleton (will be initialized in main.py)
wave_dispatcher = None

def init_wave_dispatcher(db, twilio_service):
    """Initialize the wave dispatcher singleton."""
    global wave_dispatcher
    wave_dispatcher = WaveDispatcher(db, twilio_service)
    print("✅ Wave Dispatcher initialized")
    return wave_dispatcher
