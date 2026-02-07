"""
Smart Batching Engine for Hudhud v2.0
Aggregates vendor offers and triggers notifications based on:
- MAX_OFFERS reached (6 offers), OR
- TIMEOUT elapsed (5 minutes since first offer)
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
from firebase_admin import firestore

class AggregationEngine:
    """Manages offer batching and notification triggers."""
    
    # Configuration
    MAX_OFFERS = 3  # Changed from 6 to 3
    TIMEOUT_MINUTES = 2  # Changed from 5 to 2 minutes
    CHECK_INTERVAL_SECONDS = 30  # How often to check for timeouts
    
    def __init__(self):
        self.db = firestore.client()
        self.batch_states: Dict[str, dict] = {}  # Track batching state per request
        self._running = False
    
    async def start_monitoring(self):
        """Start background task to monitor timeouts."""
        self._running = True
        while self._running:
            await self._check_timeouts()
            await asyncio.sleep(self.CHECK_INTERVAL_SECONDS)
    
    def stop_monitoring(self):
        """Stop background monitoring."""
        self._running = False
    
    async def on_offer_received(self, request_id: str, offer_data: dict):
        """
        DISABLED - Using instant offers now.
        This function is no longer called.
        """
        print("⚠️ Aggregation disabled - using instant offers")
        return False
        
        # Get current offer count
        offers_ref = self.db.collection('requests').document(request_id).collection('offers')
        offers = list(offers_ref.stream())
        offer_count = len(offers)
        
        # Initialize batch state if first offer
        if request_id not in self.batch_states:
            self.batch_states[request_id] = {
                'first_offer_at': datetime.now(),
                'notified': False
            }
        
        batch_state = self.batch_states[request_id]
        
        # Check if already notified
        if batch_state['notified']:
            # Notify about late offer
            await self._notify_late_offer(request_id, offer_data)
            return False
        
        # TRIGGER 1: Max offers reached
        if offer_count >= self.MAX_OFFERS:
            print(f"🎯 Trigger 1 (Max Offers): {request_id} has {offer_count} offers")
            await self._send_notification(request_id, offers)
            batch_state['notified'] = True
            return True
        
        # TRIGGER 2: Timeout will be checked by background task
        print(f"⏳ Offer {offer_count}/{self.MAX_OFFERS} received for {request_id}")
        return False
    
    async def _check_timeouts(self):
        """Background task to check for timeout-triggered notifications."""
        now = datetime.now()
        
        for request_id, state in list(self.batch_states.items()):
            if state['notified']:
                continue
            
            first_offer_time = state['first_offer_at']
            elapsed = now - first_offer_time
            
            # TRIGGER 2: Timeout elapsed
            if elapsed >= timedelta(minutes=self.TIMEOUT_MINUTES):
                print(f"⏰ Trigger 2 (Timeout): {request_id} after {self.TIMEOUT_MINUTES} min")
                
                # Get current offers
                offers_ref = self.db.collection('requests').document(request_id).collection('offers')
                offers = list(offers_ref.stream())
                
                if len(offers) > 0:
                    await self._send_notification(request_id, offers)
                    state['notified'] = True
    
    async def _send_notification(self, request_id: str, offers: List):
        """
        Send batched offers notification to customer.
        In Phase 4, this will send WhatsApp Interactive List.
        For now, it's a placeholder.
        """
        offer_count = len(offers)
        print(f"📬 NOTIFICATION TRIGGERED: {request_id} → {offer_count} offers")
        
        # Get request data
        request_ref = self.db.collection('requests').document(request_id)
        request_doc = request_ref.get()
        
        if not request_doc.exists:
            print(f"❌ Request {request_id} not found")
            return
        
        request_data = request_doc.to_dict()
        customer_phone = request_data.get('client_phone')  # Fixed: was 'customer_phone'
        
        # Ensure WhatsApp prefix for Twilio
        if customer_phone and not customer_phone.startswith('whatsapp:'):
            customer_phone = f'whatsapp:{customer_phone}'
        
        if not customer_phone:
            print(f"❌ No customer phone for {request_id}")
            return
        
        # Build offers summary
        offers_list = []
        for offer_doc in offers:
            offer = offer_doc.to_dict()
            offers_list.append({
                'id': offer_doc.id,
                'vendor_name': offer.get('vendor_name'),
                'price': offer.get('price'),
                'notes': offer.get('notes'),
                'portfolio_image': offer.get('portfolio_image')
            })
        
        
        
        # Get frontend URL from environment or use default
        import os
        frontend_url = os.getenv('FRONTEND_URL', 'https://eventak-head-production.up.railway.app')
        
        # Use Interactive List (Phase 4 - NOW!)
        from services.twilio import twilio_service
        
        print(f"🔧 DEBUG: Sending Interactive List to {customer_phone}")
        try:
            # Try Interactive List first
            result = twilio_service.send_offer_list(customer_phone, request_id, offers_list)
            
            if result.get('status') == 'sent':
                print(f"✅ Interactive List sent to {customer_phone}")
            else:
                # Interactive List failed - fallback to text
                print(f"⚠️ Interactive List failed, using text fallback")
                message = f"""
🎉 *وصلتك {offer_count} عروض لطلبك!*
📋 *رقم الطلب:* {request_id}

{self._format_offers_text(offers_list, frontend_url)}

━━━━━━━━━━━━━━━━━
✅ *للقبول:* أرسل رقم العرض (مثال: 1)
❌ *للرفض:* أرسل "رفض الكل"
📊 *للانتظار:* سأخبرك إذا وصلت عروض إضافية!

⏳ بانتظار ردك...
                """.strip()
                twilio_service.send_whatsapp(customer_phone, message)
                print(f"✅ Text fallback sent to {customer_phone}")
        except Exception as e:
            print(f"❌ FATAL: Notification failed - {e}")
            import traceback
            traceback.print_exc()
        
        # Mark request as "offers_sent"
        request_ref.update({'offers_sent': True, 'offers_sent_at': firestore.SERVER_TIMESTAMP})
    
    async def _notify_late_offer(self, request_id: str, offer_data: dict):
        """Notify customer about a late offer after initial batch was sent."""
        print(f"🔔 Late offer for {request_id}: {offer_data.get('vendor_name')}")
        
        # Get request data
        request_ref = self.db.collection('requests').document(request_id)
        request_doc = request_ref.get()
        
        if not request_doc.exists:
            return
        
        request_data = request_doc.to_dict()
        customer_phone = request_data.get('client_phone')  # FIX: Use 'client_phone'
        
        # Ensure WhatsApp prefix for Twilio
        if customer_phone and not customer_phone.startswith('whatsapp:'):
            customer_phone = f'whatsapp:{customer_phone}'
        
        
        if customer_phone:
            from services.twilio import twilio_service
            import os
            
            # Get total vendors count and current offer number
            offers_ref = self.db.collection('requests').document(request_id).collection('offers')
            total_offers = len(list(offers_ref.stream()))
            vendors_notified = request_data.get('vendors_notified', 3)  # Default from matching
            
            # Build enhanced message (profile link removed until frontend ready)
            message = f"""
🔔 *عرض إضافي وصل!* (العرض {total_offers} من {vendors_notified})
📋 *رقم الطلب:* {request_id}

من: *{offer_data.get('vendor_name')}*
السعر: {offer_data.get('price')} ريال

━━━━━━━━━━━━━━━━━
✅ *للقبول:* أرسل "{total_offers}"
❌ *للرفض:* أرسل "رفض"
📊 *مراجعة كل العروض:* أرسل "عروض"

💡 جميع العروض وصلت ({total_offers} من {vendors_notified})
            """.strip()
            
            twilio_service.send_whatsapp(customer_phone, message)
    
    def _format_offers_text(self, offers_list: List[dict], frontend_url: str = None) -> str:
        """Format offers with numbering (profile links removed temporarily)."""
        lines = []
        for i, offer in enumerate(offers_list, 1):
            vendor_name = offer.get('vendor_name', 'مزود خدمة')
            price = offer.get('price', 0)
            
            # Format: number, name, price
            # TODO: Add profile links when frontend /vendor/:id route is ready
            line = f"{i}️⃣ *{vendor_name}* - {price} ر.س"
            lines.append(line)
        
        return "\n\n".join(lines)
    
    def get_stats(self, request_id: str) -> dict:
        """Get batching stats for a request."""
        if request_id not in self.batch_states:
            return {'status': 'no_offers'}
        
        state = self.batch_states[request_id]
        elapsed = datetime.now() - state['first_offer_at']
        
        return {
            'first_offer_at': state['first_offer_at'].isoformat(),
            'elapsed_seconds': elapsed.total_seconds(),
            'notified': state['notified'],
            'timeout_in_seconds': (self.TIMEOUT_MINUTES * 60) - elapsed.total_seconds()
        }

# Singleton instance
aggregation_engine = AggregationEngine()

# Auto-start monitoring on import
import asyncio
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.ensure_future(aggregation_engine.start_monitoring())
        print("🚀 Aggregation Engine: Auto-started (2min/3 offers)")
except Exception as e:
    print(f"⚠️ Aggregation Engine: Will start on first use - {e}")
