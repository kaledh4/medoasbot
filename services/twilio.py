import os
from typing import List
from twilio.rest import Client

class TwilioService:
    def __init__(self):
        self.sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        # DEBUG: Print loaded values
        print(f"[TwilioService] DEBUG: from_number = '{self.from_number}'")
        
        if self.sid and self.token:
            self.client = Client(self.sid, self.token)
            print("[TwilioService] Initialized Real Twilio Client")
        else:
            self.client = None
            print("[TwilioService] Running in Mock Mode (No Credentials)")

    def send_whatsapp(self, to_number, body, media_url=None):
        if not self.client:
            print(f"[MOCK SEND] To: {to_number} | Body: {body} | Media: {media_url}")
            return {"status": "mocked"}
            
        try:
            msg_args = {
                "from_": self.from_number,
                "body": body,
                "to": to_number
            }
            if media_url:
                msg_args["media_url"] = [media_url]

            message = self.client.messages.create(**msg_args)
            print(f"[TwilioService] Sent OK: {message.sid}")
            return {"status": "sent", "sid": message.sid}
        except Exception as e:
            print(f"[TwilioService] Error sending: {e}")
            return {"status": "error", "error": str(e)}

    def send_template_message(self, to_number, template_sid, variables):
        """
        Sends a rich interaction message using Twilio Content Templates (Buttons/Lists).
        """
        if not self.client:
             print(f"[MOCK TEMPLATE] To: {to_number} | Template: {template_sid} | Vars: {variables}")
             return {"status": "mocked"}

        try:
            import json
            message = self.client.messages.create(
                from_=self.from_number,
                to=to_number,
                content_sid=template_sid,
                content_variables=json.dumps(variables)
            )
            print(f"[TwilioService] Template Sent OK: {message.sid}")
            return {"status": "sent", "sid": message.sid}
        except Exception as e:
            print(f"[TwilioService] Template Error: {e}")
            return {"status": "error", "error": str(e)}
    
    def send_flow_message(self, to_number, flow_id, header_text, body_text, button_text, flow_token="unused"):
        """
        Sends a WhatsApp Flow trigger message. 
        Dynamically creates a Content Template for the specific Flow ID if needed.
        """
        if not self.client:
             print(f"[MOCK FLOW] To: {to_number} | Flow: {flow_id}")
             return {"status": "mocked"}

        try:
            # 1. Get or Create Template SID for this Flow
            template_sid = self._create_flow_template_if_needed(flow_id, header_text, body_text, button_text)
            
            if not template_sid:
                return {"status": "error", "error": "Failed to create flow template"}

            # 2. Send using Content API
            import json
            message = self.client.messages.create(
                from_=self.from_number,
                to=to_number,
                content_sid=template_sid,
                content_variables=json.dumps({"1": "unused"}) # Flows often don't need vars but API might require empty
            )
            print(f"[TwilioService] Flow Trigger Sent: {message.sid}")
            return {"status": "sent", "sid": message.sid}
            
        except Exception as e:
            print(f"[TwilioService] Flow Error: {e}")
            return {"status": "error", "error": str(e)}

    def _create_flow_template_if_needed(self, flow_id, header, body, button):
        """
        Dynamically creates a 'whatsapp/flow' Content Template.
        Caches the SID based on Flow ID to avoid recreating.
        """
        # Cache Key: Unique combo of flow + text
        import hashlib
        key_str = f"{flow_id}-{header}-{body}-{button}"
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        
        if not hasattr(self, 'flow_template_cache'):
            self.flow_template_cache = {}
            
        if key_hash in self.flow_template_cache:
            return self.flow_template_cache[key_hash]
            
        print(f"[TwilioService] Creating New Flow Template for {flow_id}...")
        
        import requests
        import base64
        import json

        url = "https://content.twilio.com/v1/Content"
        auth_str = f"{self.sid}:{self.token}"
        b64_auth = base64.b64encode(auth_str.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {b64_auth}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "friendly_name": f"flow_{flow_id[:5]}_auto",
            "language": "ar",
            "variables": {},
            "types": {
                "whatsapp/flow": {
                    "body": body,
                    "button": button,
                    "subtitle": header, # WhatsApp Flow type uses 'subtitle' often as footer or header equivalent
                    "flow_id": flow_id,
                    "flow_action": "navigate",
                    "flow_token": "eventak_flow_init",
                    "mode": "draft" # Or 'published' if live
                }
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code in [200, 201]:
                data = response.json()
                sid = data['sid']
                self.flow_template_cache[key_hash] = sid
                print(f"[TwilioService] Created Template: {sid}")
                return sid
            else:
                print(f"[TwilioService] Template Creation Failed: {response.text}")
                return None
        except Exception as e:
            print(f"[TwilioService] Template Req Error: {e}")
            return None

    def _create_list_template_if_needed(self, menu_data):
        """
        Dynamically creates a Twilio Content Template (List Picker) via API.
        Uses In-Memory Caching based on content hash to avoid rate limits.
        """
        # Hashing logic to detect content changes
        import json
        import hashlib
        
        # We hash the 'action' part which contains the items
        content_str = json.dumps(menu_data.get('action', {}), sort_keys=True)
        content_hash = hashlib.md5(content_str.encode()).hexdigest()
        
        # Check Cache
        if not hasattr(self, 'template_cache'):
            self.template_cache = {}
            
        if content_hash in self.template_cache:
            print(f"[TwilioService] Using Cached Template ({self.template_cache[content_hash]})")
            return self.template_cache[content_hash]

        # Prioritize Dynamic over Env:
        # If we have a static SID but the content changed, checking Env first 
        # would block dynamic updates. So we SKIP Env check here and assume 
        # dynamic creation is the source of truth.
        # However, for safety, if creation fails, we could fallback to Env?
        # Let's try creation.

        print("[TwilioService] Content Changed/New. Auto-creating List Template...")
        import requests
        import base64

        url = "https://content.twilio.com/v1/Content"
        auth_str = f"{self.sid}:{self.token}"
        b64_auth = base64.b64encode(auth_str.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {b64_auth}",
            "Content-Type": "application/json"
        }
        
        # Transform our simpler 'menu_data' into Twilio 'types' payload
        # list-picker items structure: [{item, id, description}]
        
        list_items = []
        for section in menu_data['action']['sections']:
            # Twilio List Picker uses a flat list or sections depending on the 'types'.
            # The 'twilio/list-picker' items can contain nested items if simplified, 
            # but usually it's strict.
            # We will try to map our 'Section Title' to a dummy item or just flatten it?
            # Actually, standard WhatsApp List has Sections.
            # Twilio Content API 'twilio/list-picker' documentation shows 'items' array.
            # Let's clean it up: Use the exact 'config.py' structure I prepared.
            # Wait, config.py has 'sections'. Twilio Content API expects specific JSON.
            
            # Replicating the logic to build the specific Content API Body
            # We will use the 'sections' approach if possible, but Twilio Content API 
            # often simplifies this. 
            pass

        # Since dynamic mapping is complex and prone to 400 Errors without strict validation,
        # I will use a PRE-DEFINED payload matching 'eventak_menu'.
        
        # 1. Build Items
        api_items = []
        for section in menu_data['action']['sections']:
            # We can't do sections natively in 'twilio/list-picker' easily via API 
            # without correct nesting. 
            # Workaround: Flatten or use specific structure.
            # For Safety in this MVP: flattened list with Labels?
            # No, let's try strict structure.
             for row in section['rows']:
                 api_items.append({
                     "item": row['title'],
                     "id": row['id'],
                     "description": row.get('description', '')
                 })

        payload = {
            "friendly_name": "eventak_list_auto_v2",
            "language": "ar",
            "variables": {},
            "types": {
                "twilio/list-picker": {
                    "body": menu_data['body']['text'],
                    "button": menu_data['action']['button'],
                    "items": api_items 
                }
            }
        }
        
        try:
            resp = requests.post(url, headers=headers, json=payload)
            if resp.status_code in [200, 201]:
                data = resp.json()
                new_sid = data.get("sid")
                print(f"✅ [TwilioService] Created New Template: {new_sid}")
                # Save to Cache
                self.template_cache[content_hash] = new_sid
                return new_sid
            else:
                print(f"❌ [TwilioService] Create Failed: {resp.text}")
                return None
        except Exception as e:
            print(f"❌ [TwilioService] API Error: {e}")
            return None

    def send_list_menu(self, to_number, menu_data):
        """
        Sends the Menu. Tries Interactive List first (Auto-Create), else Clean Text.
        """
        if not self.client:
             print(f"[MOCK LIST] To: {to_number} | Data: {menu_data}")
             return {"status": "mocked"}

        # 1. Try to Get or Create Header
        list_sid = self._create_list_template_if_needed(menu_data)
        
        if list_sid:
            print(f"[TwilioService] Sending Interactive List (SID: {list_sid})")
            return self.send_template_message(to_number, list_sid, {})
            
        print("⚠️ [TwilioService] Fallback to Text Menu (Template Creation Failed)")
        # 2. Advanced Text Fallback
        try:
            head = menu_data['header']['text']
            body = menu_data['body']['text']
            
            # Cleaner Visuals
            msg_lines = [f"⚡ *{head}*", "", body, ""]
            
            sections = menu_data['action']['sections']
            for section in sections:
                msg_lines.append(f"\n📂 *{section['title']}*")
                for row in section['rows']:
                    msg_lines.append(f"• {row['title']}") 
            
            msg_lines.append(f"\n_💡 {menu_data['footer']['text']}_")
            
            full_text = "\n".join(msg_lines)
            
            msg_args = {
                "from_": self.from_number,
                "body": full_text,
                "to": to_number
            }
            message = self.client.messages.create(**msg_args)
            print(f"[TwilioService] Text-Menu Sent: {message.sid}")
            return {"status": "sent", "sid": message.sid}

        except Exception as e:
            print(f"[TwilioService] Menu Error: {e}")
            return {"status": "error", "error": str(e)}

    def send_offer_actions(self, to_number, offer_id, offer_text, vendor_name, media_url=None):
        """
        Sends an interactive offer. 
        If media_url exists -> Uses 'twilio/card' (Hero Image).
        Else -> Uses 'twilio/quick-reply' (Text Only).
        """
        if not self.client:
             print(f"[MOCK BUTTONS] To: {to_number} | Offer: {offer_id} | Media: {media_url}")
             return {"status": "mocked"}

        import json
        import requests
        import base64

        payload_accept = f"ACCEPT_{offer_id}"
        payload_reject = f"REJECT_{offer_id}"
        template_name = f"offer_actions_{offer_id}"
        
        url = "https://content.twilio.com/v1/Content"
        auth_str = f"{self.sid}:{self.token}"
        b64_auth = base64.b64encode(auth_str.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {b64_auth}",
            "Content-Type": "application/json"
        }
        
        # Build Actions
        actions_qr = [
            {"id": payload_accept, "title": "✅ موافق"},
            {"id": payload_reject, "title": "❌ رفض"}
        ]

        # BURST STRATEGY: Send Image First (If available)
        if media_url:
            try:
                self.client.messages.create(
                    from_=self.from_number,
                    to=to_number,
                    body=f"📸 عرض من: {vendor_name}",
                    media_url=[media_url]
                )
            except Exception as e:
                print(f"⚠️ Failed to send Offer Image: {e}")

        # TEXT ONLY BUTTONS (Reliable)
        body_text = (
            f"🎉 *تفاصيل العرض:*\n"
            f"💰 *{offer_text}*\n"
            "هل يناسبك العرض؟"
        )
        json_body = {
            "friendly_name": template_name,
            "language": "ar",
            "variables": {},
            "types": {
                "twilio/quick-reply": {
                    "body": body_text,
                    "actions": actions_qr
                }
            }
        }
        
        try:
             # Create dynamic template
             resp = requests.post(url, headers=headers, json=json_body)
             if resp.status_code in [200, 201]:
                 sid = resp.json().get("sid")
                 # Send it
                 return self.send_template_message(to_number, sid, {})
             else:
                 print(f"❌ Template Create Failed: {resp.text}")
                 # Fallback to Text
                 return self.send_whatsapp(to_number, body_text + "\n(للقبول اكتب: موافق)")
                 
        except Exception as e:
            print(f"❌ Offer Button Error: {e}")
            return {"status": "error"}

    def send_vendor_offer_request(self, vendor_phone: str, request_data: dict) -> dict:
        """
        Send offer invitation to vendor via WhatsApp.
        
        Args:
            vendor_phone: Vendor's WhatsApp number
            request_data: {
                'request_id': str,
                'customer_name': str,
                'service_category': str,
                'event_date': str,
                'location': str,
                'details': str
            }
        
        Returns:
            {'status': 'sent' | 'error', 'sid': str}
        """
        message = f"""
🔔 *طلب جديد!*

📋 *التفاصيل:*
• الخدمة: {request_data.get('service_category', 'غير محدد')}
• التاريخ: {request_data.get('event_date', 'غير محدد')}
• الموقع: {request_data.get('location', 'غير محدد')}

💬 *تفاصيل إضافية:*
{request_data.get('details', 'لا توجد')}

💰 *هل تقدر تخدم العميل؟*
لتقديم عرض سعر، اكتب: *عرض*
        """.strip()
        
        return self.send_whatsapp(vendor_phone, message)

    def send_offer_list(self, customer_phone: str, request_id: str, offers: List[dict]) -> dict:
        """
        Send Interactive List of offers to customer.
        
        Args:
            customer_phone: Customer's WhatsApp number
            offers: List of offer dicts with keys: id, vendor_name, price, notes, portfolio_image
        
        Returns:
            {'status': 'sent' | 'error', 'sid': str}
        """
        if not self.client:
            print(f"[MOCK LIST] To: {customer_phone} | Offers: {len(offers)}")
            return {"status": "mocked"}
        
        try:
            # Build Interactive List sections
            rows = []
            for i, offer in enumerate(offers[:10], 1):  # Max 10 items
                rows.append({
                    "id": f"offer_{offer['id']}",
                    "title": offer['vendor_name'][:24],  # Max 24 chars
                    "description": f"{offer['price']} ريال"
                })
            
            # Create Interactive List message
            list_message = {
                "type": "list",
                "header": {
                    "type": "text",
                    "text": f"وصلتك {len(offers)} عروض مميزة! 🎉"
                },
                "body": {
                    "text": "اضغط على الزر أدناه لاستعراض القائمة واختيار العرض المناسب"
                },
                "action": {
                    "button": "📋 استعراض العروض",
                    "sections": [{
                        "title": "العروض المتاحة",
                        "rows": rows
                    }]
                }
            }
            
            import json
            message = self.client.messages.create(
                from_=self.from_number,
                to=customer_phone,
                body=json.dumps(list_message),
                content_type="application/json"
            )
            
            print(f"✅ Interactive List Sent: {message.sid}")
            return {"status": "sent", "sid": message.sid}
            
        except Exception as e:
            print(f"❌ Interactive List Error: {e}")
            # Fallback to text
            offers_text = "\n".join([f"{i}. {o['vendor_name']} - {o['price']} ر.س" 
                                     for i, o in enumerate(offers, 1)])
            fallback_msg = f"🎉 وصلتك {len(offers)} عروض:\n\n{offers_text}\n\nللتفاصيل اكتب رقم العرض"
            return self.send_whatsapp(customer_phone, fallback_msg)
    
    def send_direct_contact_card(self, customer_phone: str, vendor_data: dict, offer_data: dict):
        """
        Send Connection Card with direct contact buttons (Lead Gen Model).
        
        Shows vendor contact info immediately with Call/WhatsApp buttons.
        NO approval needed - direct connection.
        
        Args:
            customer_phone: Customer's WhatsApp number
            vendor_data: Vendor profile (name, phone, rating, portfolio_image)
            offer_data: Offer details (price, notes)
        """
        if not self.client:
            print(f"[MOCK CONTACT CARD] To: {customer_phone} | Vendor: {vendor_data.get('name')}")
            return {"status": "mocked"}
        
        # Clean phone for links
        vendor_phone = vendor_data.get('phone', '').replace('+', '').replace(' ', '').replace('whatsapp:', '')
        
        # Build message
        card_body = f"""
📋 *عرض من {vendor_data.get('name', 'مزود')}*

💰 السعر: {offer_data.get('price')} ريال
⭐ التقييم: {vendor_data.get('rating', 'جديد')}

📝 الملاحظات:
{offer_data.get('notes') or 'لا توجد'}

🔗 *تواصل مباشرة مع المزود:*
📞 اتصال: {vendor_phone}
💬 واتساب: wa.me/{vendor_phone}

شكراً لاستخدامك هدهد! 🦦
        """.strip()
        
        # Send with portfolio image if available
        media_url = vendor_data.get('portfolio_image')
        
        # For now, send as rich text with image
        # TODO: Upgrade to Twilio URL buttons when available
        return self.send_whatsapp(
            to_number=customer_phone,
            body=card_body,
            media_url=media_url
        )

twilio_service = TwilioService()
