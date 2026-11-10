import sys
import os
import asyncio
os.environ["AI_BACKEND"] = "procedural"
sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config import settings
settings.AI_BACKEND = "procedural"
from app.core.database import init_db

async def run_api_tests():
    # Ensure database schema is created
    await init_db()
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        res = await client.get("/api/health")
        assert res.status_code == 200, f"Health check failed: {res.text}"
        data = res.json()
        assert data["status"] == "online"
        print("✓ /api/health passed")

        # 2. User registration
        reg_payload = {
            "username": "testdeveloper",
            "email": "testdev@polygen.io",
            "password": "Password123!"
        }
        res = await client.post("/api/auth/register", json=reg_payload)
        if res.status_code == 400: # Already registered
            print("  User already exists, proceeding to login...")
        else:
            assert res.status_code == 201, f"Registration failed: {res.text}"
            token_data = res.json()
            assert "access_token" in token_data
            print("✓ /api/auth/register passed")

        # 3. User login
        login_payload = {
            "username_or_email": "testdeveloper",
            "password": "Password123!"
        }
        res = await client.post("/api/auth/login", json=login_payload)
        assert res.status_code == 200, f"Login failed: {res.text}"
        login_data = res.json()
        assert "access_token" in login_data
        token = login_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✓ /api/auth/login passed")

        # 4. Trigger 3D generation job
        gen_payload = {
            "prompt": "A rusted medieval broadsword with a glowing blue sapphire in the hilt.",
            "style": "fantasy",
            "quality": "high",
            "polygon_budget": 10000,
            "target_format": "glb"
        }
        res = await client.post("/api/generate", json=gen_payload, headers=headers)
        assert res.status_code == 202, f"Generation trigger failed: {res.text}"
        job_data = res.json()
        job_id = job_data["job_id"]
        assert job_id.startswith("job_")
        print(f"✓ /api/generate triggered job: {job_id}")

        # 5. Query job status
        res = await client.get(f"/api/jobs/{job_id}", headers=headers)
        assert res.status_code == 200, f"Get job failed: {res.text}"
        status_data = res.json()
        assert status_data["job_id"] == job_id
        print(f"✓ /api/jobs/{job_id} query passed (status={status_data['status']})")

        # 6. List assets
        res = await client.get("/api/assets", headers=headers)
        assert res.status_code == 200, f"List assets failed: {res.text}"
        print("✓ /api/assets passed")

    print("\nAll Backend API integration tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(run_api_tests())
