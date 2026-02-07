#!/usr/bin/env python3
"""
Debug script to check user's requests in Firestore
"""
from google.cloud import firestore
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "d:/ANTI Gravity AGENT/event-match/gateway/eventak-6abd4-firebase-adminsdk-okqpj-0ba13ebfc9.json"

db = firestore.Client()

# Check user's phone
phone = "+966551315886"  # From the screenshot

# Get ALL requests (not just active)
all_requests = db.collection('requests')\
    .where('client_phone', '==', phone)\
    .order_by('created_at', direction=firestore.Query.DESCENDING)\
    .limit(5)\
    .stream()

print(f"\n📊 Last 5 requests for {phone}:\n")
for doc in all_requests:
    data = doc.to_dict()
    print(f"ID: {doc.id}")
    print(f"  Status: {data.get('status')}")
    print(f"  City: {data.get('city')}")
    print(f"  Category: {data.get('category')}")
    print(f"  Created: {data.get('created_at')}")
    print(f"  Details: {data.get('details', 'No details')[:50]}...")
    print()

# Check active requests
active = db.collection('requests')\
    .where('client_phone', '==', phone)\
    .where('status', 'in', ["OPEN", "WAITING_OFFERS", "NEGOTIATING"])\
    .stream()

active_list = list(active)
print(f"\n🔍 Active requests (OPEN/WAITING/NEGOTIATING): {len(active_list)}")
for doc in active_list:
    print(f"  - {doc.id}: {doc.to_dict().get('status')}")
