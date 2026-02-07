"""
Offer Collection Service for Hudhud v2.0
Manages conversational vendor bidding flow.
"""

import os
from typing import Dict, Optional
from firebase_admin import firestore
from datetime import datetime

class OfferCollectorService:
    """Handles vendor offer submission via conversational flow."""
    
    def __init__(self):
        self.db = firestore.client()
        # Track conversation state per vendor phone
        self.conversations: Dict[str, dict] = {}
    
    def start_offer(self, vendor_phone: str, request_id: str, vendor_data: dict):
        """
        Initialize offer collection for a vendor.
        
        Args:
            vendor_phone: Vendor's WhatsApp number
            request_id: The request ID being quoted
            vendor_data: Vendor profile data from database
        """
        self.conversations[vendor_phone] = {
            'request_id': request_id,
            'vendor_id': vendor_data.get('id'),
            'vendor_name': vendor_data.get('name'),
            'portfolio_image': vendor_data.get('portfolio_image'),
            'state': 'AWAITING_PRICE',
            'price': None,
            'notes': None,
            'started_at': datetime.now()
        }
        return "💰 *رائع! كم السعر اللي تقدر تقدمه؟*\n(اكتب المبلغ بالريال فقط)"
    
    def handle_vendor_message(self, vendor_phone: str, message: str) -> dict:
        """
        Process vendor message in the conversation flow.
        
        Returns:
            {
                'reply': str,  # Message to send back
                'completed': bool,  # Whether offer is complete
                'offer_data': dict | None  # Final offer data if completed
            }
        """
        if vendor_phone not in self.conversations:
            return {
                'reply': "عذراً، ما فيه طلب مفتوح حالياً. انتظر دعوة جديدة! 📬",
                'completed': False,
                'offer_data': None
            }
        
        conv = self.conversations[vendor_phone]
        
        # BACKWARD COMPATIBILITY: Add vendor_phone if missing (for old conversations)
        if 'vendor_phone' not in conv:
            conv['vendor_phone'] = vendor_phone
            print(f"⚠️ Patched old conversation state for {vendor_phone}")
        
        state = conv['state']
        
        # State 1: Collecting Price
        if state == 'AWAITING_PRICE':
            # Extract number from message
            price = self._extract_price(message)
            if price is None:
                return {
                    'reply': "❌ ماقدرت أفهم السعر. جرب تكتب رقم واضح (مثال: 500)",
                    'completed': False,
                    'offer_data': None
                }
            
            conv['price'] = price
            conv['state'] = 'AWAITING_NOTES'
            
            return {
                'reply': f"✅ تمام! السعر: {price} ريال\n\n💬 *عندك ملاحظات أو تفاصيل إضافية�*\n(أو اكتب 'لا' للتخطي)",
                'completed': False,
                'offer_data': None
            }
        
        # State 2: Collecting Notes
        elif state == 'AWAITING_NOTES':
            notes = message.strip() if message.lower() not in ['لا', 'no', 'skip'] else ''
            conv['notes'] = notes
            
            # Build final offer
            offer_data = self._finalize_offer(conv)
            
            # Clean up conversation
            del self.conversations[vendor_phone]
            
            return {
                'reply': "🎉 *تم استلام عرضك بنجاح!*\nبنبلغ العميل وبنخبرك إذا اختار عرضك.",
                'completed': True,
                'offer_data': offer_data
            }
        
        return {
            'reply': "حدث خطأ. جرب من جديد.",
            'completed': False,
            'offer_data': None
        }
    
    def save_offer(self, offer_data: dict):
        """Save offer to Firestore top-level collection."""
        try:
            request_id = offer_data['request_id']
            
            # FIXED: Save to top-level 'offers' collection (not subcollection)
            # This matches the query in send_instant_offer_notification()
            offers_ref = self.db.collection('offers')
            
            offers_ref.add({
                **offer_data,
                'created_at': firestore.SERVER_TIMESTAMP,
                'status': 'PENDING'  # Uppercase to match other parts
            })
            
            print(f"✅ Offer saved: {offer_data['vendor_id']} → {request_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save offer: {e}")
            return False
    
    def _extract_price(self, text: str) -> Optional[float]:
        """Extract number from Arabic/English text."""
        import re
        
        # Convert Eastern Arabic numerals
        table = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
        text = text.translate(table)
        
        # Extract first number
        match = re.search(r'\d+(?:\.\d+)?', text)
        if match:
            return float(match.group())
        return None
    
    def _finalize_offer(self, conv: dict) -> dict:
        """Build final offer data object."""
        return {
            'request_id': conv['request_id'],
            'vendor_id': conv['vendor_id'],
            'vendor_name': conv['vendor_name'],
            'vendor_phone': conv['vendor_phone'],  # CRITICAL: Include for instant notifications
            'price': conv['price'],
            'notes': conv['notes'],
            'portfolio_image': conv['portfolio_image'],  # AUTO-FETCHED
            'submitted_at': datetime.now().isoformat()
        }
    
    def cancel_offer(self, vendor_phone: str):
        """Cancel ongoing offer collection."""
        if vendor_phone in self.conversations:
            del self.conversations[vendor_phone]
            return "❌ تم إلغاء العرض"
        return "ما فيه عرض مفتوح"

# Singleton instance
offer_collector = OfferCollectorService()
