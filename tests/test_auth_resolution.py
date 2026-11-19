import os
import sys
import uuid
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import init_db
import asyncio

class TestAuthResolution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        asyncio.run(init_db())
        cls.client = TestClient(app)

    def test_01_demo_account_login(self):
        """Verify demo account works with email or username."""
        # 1. Login with demo email
        res1 = self.client.post("/api/auth/login", json={
            "username_or_email": "demo_creator@polygen.ai",
            "password": "PolyGen2026Secure!",
        })
        self.assertEqual(res1.status_code, 200)
        self.assertIn("access_token", res1.json())

        # 2. Login sending 'email' field instead of 'username_or_email'
        res2 = self.client.post("/api/auth/login", json={
            "email": "demo_creator@polygen.ai",
            "password": "PolyGen2026Secure!",
        })
        self.assertEqual(res2.status_code, 200)
        self.assertIn("access_token", res2.json())

        # 3. Login sending 'username' field
        res3 = self.client.post("/api/auth/login", json={
            "username": "demo_creator",
            "password": "PolyGen2026Secure!",
        })
        self.assertEqual(res3.status_code, 200)
        self.assertIn("access_token", res3.json())

    def test_02_register_with_and_without_username(self):
        """Verify registration both with explicit username and auto-derived username."""
        # A. Explicit username
        uid1 = str(uuid.uuid4())[:8]
        res_a = self.client.post("/api/auth/register", json={
            "name": "Explicit User",
            "username": f"user_{uid1}",
            "email": f"explicit_{uid1}@example.com",
            "password": "Password123!A",
        })
        self.assertEqual(res_a.status_code, 201)
        self.assertEqual(res_a.json()["user"]["username"], f"user_{uid1}")

        # B. Omitted username (auto-derived from email handle)
        uid2 = str(uuid.uuid4())[:8]
        res_b = self.client.post("/api/auth/register", json={
            "email": f"autoname_{uid2}@example.com",
            "password": "Password123!B",
        })
        self.assertEqual(res_b.status_code, 201)
        self.assertIn(f"autoname_{uid2}", res_b.json()["user"]["username"])

    def test_03_duplicate_checks_with_clean_messages(self):
        """Verify duplicate email and duplicate username return 400 with clean, non-crashing detail."""
        uid = str(uuid.uuid4())[:8]
        email = f"dup_{uid}@example.com"
        username = f"dup_{uid}"
        password = "Password123!C"

        # Register initial user
        r1 = self.client.post("/api/auth/register", json={
            "username": username,
            "email": email,
            "password": password,
        })
        self.assertEqual(r1.status_code, 201)

        # Duplicate email
        r2 = self.client.post("/api/auth/register", json={
            "username": f"other_{uid}",
            "email": email,
            "password": password,
        })
        self.assertEqual(r2.status_code, 400)
        self.assertIn("already registered", r2.json()["detail"])

        # Duplicate username
        r3 = self.client.post("/api/auth/register", json={
            "username": username,
            "email": f"other_{uid}@example.com",
            "password": password,
        })
        self.assertEqual(r3.status_code, 400)
        self.assertIn("already taken", r3.json()["detail"])

    def test_04_invalid_credentials_handling(self):
        """Verify incorrect password gives 401 with standard message."""
        res = self.client.post("/api/auth/login", json={
            "username_or_email": "demo_creator@polygen.ai",
            "password": "WrongPassword999!",
        })
        self.assertEqual(res.status_code, 401)
        self.assertIn("Incorrect email/username or password", res.json()["detail"])

if __name__ == "__main__":
    unittest.main()
