import unittest
from unittest.mock import MagicMock, patch
import asyncio
from fastapi import HTTPException

# We need to ensure we can import from gateway.main
try:
    from gateway.main import get_track_data, accept_offer_api
except ImportError:
    # Fallback for different execution contexts
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from gateway.main import get_track_data, accept_offer_api

class TestSecurityFix(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    @patch('gateway.main.store_service')
    def test_get_track_data_default_token_blocked(self, mock_store):
        """
        Verify that 'default_token' is now BLOCKED.
        """
        mock_store.get_request.return_value = {
            "id": "req_123",
            "security_token": "secure_random_token_xyz",
            "category_name": "Test Cat",
            "status": "OPEN",
            "created_at": "now"
        }

        with self.assertRaises(HTTPException) as cm:
            self.loop.run_until_complete(
                get_track_data(request_id="req_123", token="default_token")
            )
        self.assertEqual(cm.exception.status_code, 403)

    @patch('gateway.main.store_service')
    def test_get_track_data_valid_token(self, mock_store):
        """
        Verify that VALID token works.
        """
        valid_token = "secure_random_token_xyz"
        mock_store.get_request.return_value = {
            "id": "req_123",
            "security_token": valid_token,
            "category_name": "Test Cat",
            "status": "OPEN",
            "created_at": "now"
        }
        mock_store.get_request_offers.return_value = []

        result = self.loop.run_until_complete(
            get_track_data(request_id="req_123", token=valid_token)
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["request"]["id"], "req_123")

    @patch('gateway.main.store_service')
    @patch('gateway.main.twilio_service')
    def test_accept_offer_default_token_blocked(self, mock_twilio, mock_store):
        """
        Verify that 'default_token' CANNOT accept offers.
        """
        mock_store.get_offer.return_value = {
            "id": "off_123",
            "request_id": "req_123",
            "vendor_id": "ven_1",
            "price": "100"
        }
        mock_store.get_request.return_value = {
            "id": "req_123",
            "security_token": "secure_random_token_xyz",
            "client_phone": "123",
            "status": "OPEN"
        }

        with self.assertRaises(HTTPException) as cm:
            self.loop.run_until_complete(
                accept_offer_api(offer_id="off_123", token="default_token")
            )
        self.assertEqual(cm.exception.status_code, 403)

if __name__ == '__main__':
    unittest.main()
