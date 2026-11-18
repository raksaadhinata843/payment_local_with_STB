import sys
import os
import unittest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.main import app
from seed_data import seed

class TestSTBAdminBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed()
        cls.client = TestClient(app)
        cls.headers = {
            "X-Device-ID": "STB-KASIR-01"
        }

    def test_01_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_02_customer_lookup_valid(self):
        response = self.client.get(
            "/api/v1/device/customer-by-card?rfid_uid=4B2A8F90",
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertTrue(res_data["success"])
        self.assertEqual(res_data["data"]["name"], "Budi Santoso")
        self.assertEqual(res_data["data"]["balance"], 100000)

    def test_03_customer_lookup_invalid_card(self):
        response = self.client.get(
            "/api/v1/device/customer-by-card?rfid_uid=INVALID_UID",
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertFalse(res_data["success"])

    def test_04_charge_success_fingerprint(self):
        payload = {
            "idempotency_key": "TX-TEST-001",
            "rfid_uid": "4B2A8F90",
            "amount": 15000,
            "stb_device_id": "STB-KASIR-01",
            "auth_method": "FINGERPRINT"
        }
        response = self.client.post(
            "/api/v1/device/charge",
            json=payload,
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertTrue(res_data["success"])
        self.assertEqual(res_data["data"]["balance_before"], 100000)
        self.assertEqual(res_data["data"]["balance_after"], 85000)

    def test_05_idempotency_charge(self):
        # Sending identical idempotency key "TX-TEST-001" again
        payload = {
            "idempotency_key": "TX-TEST-001",
            "rfid_uid": "4B2A8F90",
            "amount": 15000,
            "stb_device_id": "STB-KASIR-01",
            "auth_method": "FINGERPRINT"
        }
        response = self.client.post(
            "/api/v1/device/charge",
            json=payload,
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertTrue(res_data["success"])
        # Balance should remain 85,000 (NOT deducted again!)
        self.assertEqual(res_data["data"]["balance_after"], 85000)

    def test_06_charge_pin_fallback(self):
        payload = {
            "idempotency_key": "TX-TEST-002",
            "rfid_uid": "4B2A8F90",
            "amount": 10000,
            "stb_device_id": "STB-KASIR-01",
            "auth_method": "PIN_FALLBACK",
            "pin": "123456"
        }
        response = self.client.post(
            "/api/v1/device/charge",
            json=payload,
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertTrue(res_data["success"])
        self.assertEqual(res_data["data"]["balance_before"], 85000)
        self.assertEqual(res_data["data"]["balance_after"], 75000)

    def test_07_insufficient_funds(self):
        payload = {
            "idempotency_key": "TX-TEST-003",
            "rfid_uid": "4B2A8F90",
            "amount": 999000, # Too large
            "stb_device_id": "STB-KASIR-01",
            "auth_method": "FINGERPRINT"
        }
        response = self.client.post(
            "/api/v1/device/charge",
            json=payload,
            headers=self.headers
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Insufficient funds", response.json()["detail"])

    def test_08_offline_sync(self):
        payload = {
            "stb_device_id": "STB-KASIR-01",
            "transactions": [
                {
                    "idempotency_key": "TX-TEST-001", # Duplicate, will be skipped
                    "rfid_uid": "4B2A8F90",
                    "amount": 15000,
                    "stb_device_id": "STB-KASIR-01",
                    "auth_method": "FINGERPRINT",
                    "transacted_at": "2026-11-18T10:00:00"
                },
                {
                    "idempotency_key": "OFFLINE-TX-001", # New transaction from Mode 2
                    "rfid_uid": "4B2A8F90",
                    "amount": 25000,
                    "stb_device_id": "STB-KASIR-01",
                    "auth_method": "FINGERPRINT",
                    "transacted_at": "2026-11-18T10:05:00"
                }
            ]
        }
        response = self.client.post(
            "/api/v1/device/sync-offline",
            json=payload,
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertTrue(res_data["success"])
        self.assertEqual(res_data["processed_count"], 1)
        self.assertEqual(res_data["skipped_count"], 1)

    def test_09_admin_topup(self):
        payload = {
            "rfid_uid": "4B2A8F90",
            "amount": 50000,
            "admin_device_id": "STB-ADMIN-01"
        }
        response = self.client.post(
            "/api/v1/admin/topup",
            json=payload
        )
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertTrue(res_data["success"])
        # 75,000 - 25,000 (offline sync) + 50,000 (topup) = 100,000
        self.assertEqual(res_data["balance_after"], 100000)

if __name__ == "__main__":
    unittest.main()
