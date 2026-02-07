import requests
import os
import json

class NodeBackendService:
    def __init__(self):
        # Render provides BACKEND_HOST (host:port) via blueprint
        backend_host = os.getenv("BACKEND_HOST")
        if backend_host:
            # Handle user sometimes pasting full URL with https://
            if backend_host.startswith("http"):
                self.base_url = f"{backend_host}/api/v1"
            else:
                self.base_url = f"http://{backend_host}/api/v1"
        else:
            self.base_url = os.getenv("BACKEND_URL", "http://localhost:8080/api/v1")
            
        print(f"[NodeBackendService] Connected to Body at {self.base_url}")

    def create_request(self, customer_phone, category, city, text):
        """
        Creates a new service request in the Node.js backend.
        """
        payload = {
            "customerPhone": customer_phone,
            "category": category,
            "city": city,
            "details": text,
            "budget": "Unknown", # Default
            "eventDate": "Flexible" # Default
        }
        
        try:
            print(f"👉 POST {self.base_url}/requests | {json.dumps(payload)}")
            response = requests.post(f"{self.base_url}/requests", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to create request: {e}")
            # Fallback for Demo/Mock
            import random
            return {"requestId": str(random.randint(100000, 999999))}

    def search_vendors(self, category, city):
        """
        Finds matching vendors for a request.
        """
        try:
            params = {"category": category, "city": city}
            response = requests.get(f"{self.base_url}/vendors", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to search vendors: {e}")
            return []

backend_service = NodeBackendService()
