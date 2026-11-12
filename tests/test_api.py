import sys
import os
import asyncio
import uuid
from datetime import datetime

# Set backend in test mode with procedural volumetric AI generator for instant execution
os.environ["AI_BACKEND"] = "procedural"
os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config import settings
settings.AI_BACKEND = "procedural"
settings.CELERY_TASK_ALWAYS_EAGER = True
from app.core.database import init_db
from app.services.storage import storage_service

async def run_api_tests():
    print("=" * 60)
    print("POLYGEN PART 3: BACKEND, DATABASE, WORKER & STORAGE TESTS")
    print("=" * 60)

    # 1. Ensure database schema is created
    await init_db()
    print("✓ Database tables initialized successfully")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 2. Test GET /api/health
        res = await client.get("/api/health")
        assert res.status_code == 200, f"Health check failed: {res.text}"
        data = res.json()
        assert data["status"] == "online"
        assert "storage_backend" in data
        print("✓ GET /api/health passed")

        # 3. Test POST /api/auth/register
        unique_suffix = uuid.uuid4().hex[:6]
        user_email = f"creator_{unique_suffix}@polygen.ai"
        user_password = "SecurePassword2026!"
        reg_payload = {
            "name": f"Creator {unique_suffix}",
            "username": f"creator_{unique_suffix}",
            "email": user_email,
            "password": user_password
        }
        res = await client.post("/api/auth/register", json=reg_payload)
        assert res.status_code == 201, f"Registration failed: {res.text}"
        token_data = res.json()
        assert "access_token" in token_data
        assert token_data["user"]["email"] == user_email
        print(f"✓ POST /api/auth/register passed (User: {user_email})")

        # 4. Test POST /api/auth/login
        login_payload = {
            "username_or_email": user_email,
            "password": user_password
        }
        res = await client.post("/api/auth/login", json=login_payload)
        assert res.status_code == 200, f"Login failed: {res.text}"
        login_data = res.json()
        assert "access_token" in login_data
        token = login_data["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        print("✓ POST /api/auth/login passed (JWT token issued)")

        # 5. Test GET /api/auth/me
        res = await client.get("/api/auth/me", headers=auth_headers)
        assert res.status_code == 200, f"Get me failed: {res.text}"
        me_data = res.json()
        assert me_data["email"] == user_email
        print("✓ GET /api/auth/me passed")

        # 6. Test POST /api/auth/logout
        res = await client.post("/api/auth/logout", headers=auth_headers)
        assert res.status_code == 200, f"Logout failed: {res.text}"
        print("✓ POST /api/auth/logout passed")

        # 7. Test POST /api/generate (Asynchronous 3D generation request)
        gen_payload = {
            "prompt": "A rusted medieval broadsword with a glowing blue sapphire in the hilt.",
            "style": "fantasy",
            "quality": "high",
            "polygon_budget": 5000,
            "target_format": "glb"
        }
        res = await client.post("/api/generate", json=gen_payload, headers=auth_headers)
        assert res.status_code == 202, f"Generation trigger failed: {res.text}"
        job_data = res.json()
        job_id = job_data["id"]
        assert job_id.startswith("job_")
        assert job_data["status"] in ["queued", "processing", "pending"]
        print(f"✓ POST /api/generate passed (Job ID: {job_id})")

        # 8. Test GET /api/jobs/{job_id}
        res = await client.get(f"/api/jobs/{job_id}", headers=auth_headers)
        assert res.status_code == 200, f"Get job failed: {res.text}"
        status_data = res.json()
        assert status_data["id"] == job_id
        print(f"✓ GET /api/jobs/{job_id} passed (Initial status: {status_data['status']})")

        # 9. Wait for pipeline background completion
        print("  Awaiting 3D pipeline execution completion...")
        max_retries = 30
        completed = False
        final_job_data = None
        for _ in range(max_retries):
            await asyncio.sleep(1.0)
            res = await client.get(f"/api/jobs/{job_id}", headers=auth_headers)
            final_job_data = res.json()
            if final_job_data["status"] == "completed":
                completed = True
                break
            elif final_job_data["status"] == "failed":
                raise RuntimeError(f"Pipeline job failed: {final_job_data.get('error_message')}")

        assert completed, f"Job did not complete within {max_retries}s: {final_job_data}"
        asset_id = final_job_data.get("asset_id")
        assert asset_id is not None, "Completed job does not reference an asset_id"
        print(f"✓ Generation pipeline completed successfully (Asset ID: {asset_id})")

        # 10. Test GET /api/jobs (List jobs)
        res = await client.get("/api/jobs", headers=auth_headers)
        assert res.status_code == 200, f"List jobs failed: {res.text}"
        jobs_list = res.json()
        assert isinstance(jobs_list, list)
        assert any(j["id"] == job_id for j in jobs_list)
        print(f"✓ GET /api/jobs passed ({len(jobs_list)} jobs retrieved)")

        # 11. Test GET /api/assets
        res = await client.get("/api/assets", headers=auth_headers)
        assert res.status_code == 200, f"List assets failed: {res.text}"
        assets_list = res.json()
        assert "items" in assets_list
        assert any(a["id"] == asset_id for a in assets_list["items"])
        print(f"✓ GET /api/assets passed ({assets_list['total']} total assets)")

        # 12. Test GET /api/assets/{asset_id}
        res = await client.get(f"/api/assets/{asset_id}", headers=auth_headers)
        assert res.status_code == 200, f"Get asset details failed: {res.text}"
        asset_detail = res.json()
        assert asset_detail["id"] == asset_id
        assert asset_detail["polygon_count"] > 0
        assert asset_detail["file_size"] > 0
        assert asset_detail["glb_url"].startswith("/api/assets/")
        print(f"✓ GET /api/assets/{asset_id} passed (Polygons: {asset_detail['polygon_count']}, Size: {asset_detail['file_size']} bytes)")

        # 13. Test GET /api/assets/{asset_id}/download
        res = await client.get(f"/api/assets/{asset_id}/download")
        assert res.status_code == 200, f"Download failed: {res.text}"
        assert res.headers.get("content-type") == "model/gltf-binary"
        # Validate binary header
        assert res.content[:4] == b"glTF", "Downloaded file does not start with glTF binary magic bytes"
        print(f"✓ GET /api/assets/{asset_id}/download passed ({len(res.content):,} bytes verified with glTF header)")

        # 14. Test DELETE /api/assets/{asset_id}
        res = await client.delete(f"/api/assets/{asset_id}", headers=auth_headers)
        assert res.status_code == 204, f"Delete asset failed: {res.status_code}"
        
        # Verify asset is gone
        res = await client.get(f"/api/assets/{asset_id}", headers=auth_headers)
        assert res.status_code == 404, "Asset was not deleted"
        print(f"✓ DELETE /api/assets/{asset_id} passed (Cleaned up from database and storage)")

    # 15. Test WebSocket endpoint
    from starlette.testclient import TestClient
    with TestClient(app) as test_client:
        with test_client.websocket_connect(f"/ws/jobs/{job_id}") as websocket:
            websocket.send_text("ping")
            pong = websocket.receive_json()
            assert pong == {"type": "pong"}, f"Unexpected WS response: {pong}"
            print("✓ WS /ws/jobs/{job_id} WebSocket bidirectional communication verified")

    # 16. Test Storage Service Abstraction
    print("\n--- Testing Storage Service Abstraction ---")
    test_content = b"glTF\x02\x00\x00\x00\x50\x00\x00\x00PolyGenTestGLB"
    saved_path = storage_service.save_file("exports", "test_mock.glb", test_content)
    assert os.path.exists(saved_path), f"File was not written to: {saved_path}"
    assert storage_service.exists("exports", "test_mock.glb")
    read_bytes = storage_service.get_file_bytes("exports", "test_mock.glb")
    assert read_bytes == test_content
    del_ok = storage_service.delete_file("exports", "test_mock.glb")
    assert del_ok and not storage_service.exists("exports", "test_mock.glb")
    print("✓ LocalStorageService verified (Save, Exists, Read, Delete across categories)")

    print("\n" + "=" * 60)
    print("ALL PART 3 BACKEND & DATABASE TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_api_tests())
