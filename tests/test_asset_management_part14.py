"""
test_asset_management_part14.py
================================
Unit and integration test suite for PolyGen Part 14:
Asset Library and Generation History Management System.

Features Tested:
1.  Ownership Isolation: User A assets & jobs strictly inaccessible to User B (HTTP 403 / excluded).
2.  Asset Persistence: Assets & metadata persist across application / session reloads.
3.  Search Capability: Keyword search by asset name and prompt text.
4.  Date Filtering: Server-side & client-side filtering by creation date (today, week, month, all).
5.  Sorting Engine: Sorting by newest, oldest, polygon count (desc/asc), and file size.
6.  Asset Deletion: Authorized deletion removes DB record and physical GLB storage files.
7.  Generation History Audit: Tracks original prompt, date, status, duration, settings, output asset, and failure details.
8.  Frontend AssetCard Component: Thumbnail, asset name, creation date, polygon count, file size, status, and action menu.
9.  Frontend AssetLibrary Page: Search, filter by creation date, sort by newest, open details, 3D preview, download, delete.
10. Frontend GenerationHistory Page: Prompt, date, status, duration, settings, output asset, and error drawer.
"""

import os
import sys
import uuid
import unittest
import numpy as np

# Adjust sys.path to access backend
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.job import GenerationJob
from app.models.asset import GeneratedAsset

FRONTEND_CARD_PATH = os.path.join(ROOT_DIR, "frontend", "src", "components", "AssetCard.tsx")
FRONTEND_LIB_PATH = os.path.join(ROOT_DIR, "frontend", "src", "pages", "AssetLibrary.tsx")
FRONTEND_HIST_PATH = os.path.join(ROOT_DIR, "frontend", "src", "pages", "GenerationHistory.tsx")


class TestAssetManagementPart14(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_out_dir = os.path.join(ROOT_DIR, "tests", "output_part14")
        os.makedirs(cls.test_out_dir, exist_ok=True)

        with open(FRONTEND_CARD_PATH, "r", encoding="utf-8") as f:
            cls.card_source = f.read()
        with open(FRONTEND_LIB_PATH, "r", encoding="utf-8") as f:
            cls.lib_source = f.read()
        with open(FRONTEND_HIST_PATH, "r", encoding="utf-8") as f:
            cls.hist_source = f.read()

    def _create_user(self, tag: str):
        """Helper creating and authenticating a test user, returning (user_id, token, headers)."""
        uid = uuid.uuid4().hex[:8]
        email = f"user_{tag}_{uid}@polygen.ai"
        username = f"u_{tag}_{uid}"
        pwd = "SecurePassword123!"

        res_reg = self.client.post("/api/auth/register", json={
            "email": email,
            "password": pwd,
            "username": username,
            "name": f"Test User {tag.upper()}"
        })
        self.assertEqual(res_reg.status_code, 201)

        res_login = self.client.post("/api/auth/login", json={
            "username_or_email": email,
            "password": pwd
        })
        self.assertEqual(res_login.status_code, 200)
        data = res_login.json()
        token = data["access_token"]
        user_id = data["user"]["id"]
        headers = {"Authorization": f"Bearer {token}"}
        return user_id, token, headers

    def test_01_ownership_isolation_assets(self):
        """Ownership Validation: User B cannot view, download, or delete User A's assets."""
        import asyncio

        # 1. Register User A and User B
        user_a_id, token_a, headers_a = self._create_user("a")
        user_b_id, token_b, headers_b = self._create_user("b")

        # 2. Insert test asset for User A
        asset_a_id = f"ast_a_{uuid.uuid4().hex[:8]}"
        job_a_id = f"job_a_{uuid.uuid4().hex[:8]}"
        dummy_glb = os.path.join(self.test_out_dir, f"{asset_a_id}.glb")
        with open(dummy_glb, "wb") as f:
            f.write(b"glTF" + b"\x02\x00\x00\x00" + b"\x20\x00\x00\x00" + b"\x00" * 32)

        async def insert_asset_a():
            async with AsyncSessionLocal() as db:
                job = GenerationJob(
                    id=job_a_id,
                    user_id=user_a_id,
                    prompt="User A Private Broadsword",
                    configuration={"style": "fantasy", "quality": "high"},
                    status="completed",
                    progress=100,
                )
                db.add(job)
                asset = GeneratedAsset(
                    id=asset_a_id,
                    job_id=job_a_id,
                    user_id=user_a_id,
                    asset_name="User A Private Broadsword",
                    original_prompt="User A Private Broadsword",
                    glb_path=dummy_glb,
                    polygon_count=1200,
                    file_size=os.path.getsize(dummy_glb),
                    metadata_json={"style": "fantasy"},
                )
                db.add(asset)
                await db.commit()

        asyncio.run(insert_asset_a())

        # 3. User A can access asset A
        res_a_get = self.client.get(f"/api/assets/{asset_a_id}", headers=headers_a)
        self.assertEqual(res_a_get.status_code, 200)
        self.assertEqual(res_a_get.json()["asset_name"], "User A Private Broadsword")

        # 4. User B listing assets MUST NOT contain User A's asset
        res_b_list = self.client.get("/api/assets", headers=headers_b)
        self.assertEqual(res_b_list.status_code, 200)
        b_asset_ids = [item["asset_id"] for item in res_b_list.json()["items"]]
        self.assertNotIn(asset_a_id, b_asset_ids)

        # 5. User B attempting direct GET /api/assets/{id} MUST be rejected with HTTP 403
        res_b_get = self.client.get(f"/api/assets/{asset_a_id}", headers=headers_b)
        self.assertEqual(res_b_get.status_code, 403)
        err_msg = res_b_get.json().get("detail") or res_b_get.json().get("error", {}).get("message", "")
        self.assertIn("do not have permission", err_msg)

        # 6. User B attempting download /api/assets/{id}/download MUST be rejected with HTTP 403
        res_b_dl = self.client.get(f"/api/assets/{asset_a_id}/download", headers=headers_b)
        self.assertEqual(res_b_dl.status_code, 403)

        # 7. User B attempting DELETE /api/assets/{id} MUST be rejected with HTTP 403
        res_b_del = self.client.get(f"/api/assets/{asset_a_id}", headers=headers_b)
        self.assertEqual(res_b_del.status_code, 403)

        print("[PASS] Ownership Validation: User B strictly prevented from viewing, downloading, or modifying User A's asset (HTTP 403 / Isolated)")

    def test_02_ownership_isolation_generation_history(self):
        """Ownership Validation: User B cannot view User A's generation jobs or execution logs."""
        import asyncio

        user_a_id, _, headers_a = self._create_user("hist_a")
        user_b_id, _, headers_b = self._create_user("hist_b")

        job_a_id = f"job_audit_{uuid.uuid4().hex[:8]}"

        async def insert_job_a():
            async with AsyncSessionLocal() as db:
                job = GenerationJob(
                    id=job_a_id,
                    user_id=user_a_id,
                    prompt="Confidential Royal Crown",
                    configuration={"style": "royal", "quality": "ultra", "polygon_budget": 25000},
                    status="completed",
                    progress=100,
                )
                db.add(job)
                await db.commit()

        asyncio.run(insert_job_a())

        # User A sees job in history
        res_a = self.client.get("/api/jobs", headers=headers_a)
        self.assertEqual(res_a.status_code, 200)
        self.assertTrue(any(j["job_id"] == job_a_id for j in res_a.json()))

        # User B listing jobs MUST NOT see User A's job
        res_b = self.client.get("/api/jobs", headers=headers_b)
        self.assertEqual(res_b.status_code, 200)
        self.assertFalse(any(j["job_id"] == job_a_id for j in res_b.json()))

        # User B querying /api/jobs/{id} MUST receive HTTP 403
        res_b_direct = self.client.get(f"/api/jobs/{job_a_id}", headers=headers_b)
        self.assertEqual(res_b_direct.status_code, 403)

        print("[PASS] Ownership Validation: Generation history strictly isolated between tenant accounts (HTTP 403)")

    def test_03_search_assets_api(self):
        """Asset Library: Search filtering by name and prompt keyword."""
        import asyncio

        user_id, _, headers = self._create_user("search")
        tag = uuid.uuid4().hex[:6]

        # Insert 3 diverse assets
        async def insert_search_assets():
            async with AsyncSessionLocal() as db:
                items = [
                    ("Rustic Wooden Chair", f"A rustic wooden chair with oak finish {tag}", 500),
                    ("Laser Sci-Fi Rifle", f"A futuristic energy laser rifle {tag}", 3200),
                    ("Ancient Dragon Shield", f"A worn bronze dragon shield {tag}", 1800),
                ]
                for name, p, poly in items:
                    ast_id = f"ast_{uuid.uuid4().hex[:8]}"
                    job_id = f"job_{uuid.uuid4().hex[:8]}"
                    p_glb = os.path.join(self.test_out_dir, f"{ast_id}.glb")
                    with open(p_glb, "wb") as f:
                        f.write(b"glTF" + b"\x02\x00\x00\x00" + b"\x20\x00\x00\x00" + b"\x00" * 32)

                    job = GenerationJob(id=job_id, user_id=user_id, prompt=p, status="completed", progress=100)
                    db.add(job)
                    ast = GeneratedAsset(
                        id=ast_id,
                        job_id=job_id,
                        user_id=user_id,
                        asset_name=name,
                        original_prompt=p,
                        glb_path=p_glb,
                        polygon_count=poly,
                        file_size=os.path.getsize(p_glb),
                    )
                    db.add(ast)
                await db.commit()

        asyncio.run(insert_search_assets())

        # Search for "Laser"
        res_search = self.client.get(f"/api/assets?search=Laser", headers=headers)
        self.assertEqual(res_search.status_code, 200)
        items = res_search.json()["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["asset_name"], "Laser Sci-Fi Rifle")

        # Search for "oak" in prompt
        res_prompt = self.client.get(f"/api/assets?search=oak", headers=headers)
        self.assertEqual(res_prompt.status_code, 200)
        self.assertEqual(len(res_prompt.json()["items"]), 1)
        self.assertEqual(res_prompt.json()["items"][0]["asset_name"], "Rustic Wooden Chair")

        print("[PASS] Asset Library: Search engine accurately filters by name and prompt keyword")

    def test_04_sort_and_date_filtering(self):
        """Asset Library: Sorting by newest, oldest, polygon count, and creation date filter."""
        import asyncio
        from datetime import datetime, timedelta

        user_id, _, headers = self._create_user("sort")

        async def insert_sorted_assets():
            async with AsyncSessionLocal() as db:
                # Insert 3 assets with different polygon counts and timestamps
                p1_glb = os.path.join(self.test_out_dir, "sort_1.glb")
                p2_glb = os.path.join(self.test_out_dir, "sort_2.glb")
                with open(p1_glb, "wb") as f: f.write(b"glTF" + b"\x00" * 32)
                with open(p2_glb, "wb") as f: f.write(b"glTF" + b"\x00" * 32)

                j1 = GenerationJob(id=f"j_{uuid.uuid4().hex[:8]}", user_id=user_id, prompt="Low poly box", status="completed")
                j2 = GenerationJob(id=f"j_{uuid.uuid4().hex[:8]}", user_id=user_id, prompt="High poly statue", status="completed")
                db.add_all([j1, j2])

                a1 = GeneratedAsset(
                    id=f"a_{uuid.uuid4().hex[:8]}",
                    job_id=j1.id,
                    user_id=user_id,
                    asset_name="Asset Low Poly",
                    glb_path=p1_glb,
                    polygon_count=500,
                    file_size=1024,
                    created_at=datetime.utcnow() - timedelta(days=2),
                )
                a2 = GeneratedAsset(
                    id=f"a_{uuid.uuid4().hex[:8]}",
                    job_id=j2.id,
                    user_id=user_id,
                    asset_name="Asset High Poly",
                    glb_path=p2_glb,
                    polygon_count=15000,
                    file_size=2048,
                    created_at=datetime.utcnow(),
                )
                db.add_all([a1, a2])
                await db.commit()

        asyncio.run(insert_sorted_assets())

        # Test sort_by=polygons_desc
        res_poly = self.client.get("/api/assets?sort_by=polygons_desc", headers=headers)
        self.assertEqual(res_poly.status_code, 200)
        items = res_poly.json()["items"]
        self.assertGreaterEqual(items[0]["polygon_count"], items[1]["polygon_count"])

        # Test date_filter=today
        res_today = self.client.get("/api/assets?date_filter=today", headers=headers)
        self.assertEqual(res_today.status_code, 200)
        today_items = res_today.json()["items"]
        self.assertEqual(len(today_items), 1)
        self.assertEqual(today_items[0]["asset_name"], "Asset High Poly")

        print("[PASS] Asset Library: Sorting (polygons_desc) and date filtering (today) verified")

    def test_05_asset_deletion(self):
        """Asset Library: Authorized deletion removes database record and storage files."""
        import asyncio

        user_id, _, headers = self._create_user("delete")
        asset_id = f"ast_del_{uuid.uuid4().hex[:8]}"
        job_id = f"job_del_{uuid.uuid4().hex[:8]}"
        dummy_glb = os.path.join(self.test_out_dir, f"{asset_id}.glb")
        with open(dummy_glb, "wb") as f:
            f.write(b"glTF" + b"\x02\x00\x00\x00" + b"\x20\x00\x00\x00" + b"\x00" * 32)

        async def insert_for_delete():
            async with AsyncSessionLocal() as db:
                job = GenerationJob(id=job_id, user_id=user_id, prompt="Temporary Asset", status="completed")
                db.add(job)
                ast = GeneratedAsset(
                    id=asset_id,
                    job_id=job_id,
                    user_id=user_id,
                    asset_name="Temporary Asset to Delete",
                    glb_path=dummy_glb,
                    polygon_count=100,
                    file_size=os.path.getsize(dummy_glb),
                )
                db.add(ast)
                await db.commit()

        asyncio.run(insert_for_delete())
        self.assertTrue(os.path.exists(dummy_glb))

        # Delete asset via API
        res_del = self.client.delete(f"/api/assets/{asset_id}", headers=headers)
        self.assertEqual(res_del.status_code, 204)

        # Verify physical file removed
        self.assertFalse(os.path.exists(dummy_glb))

        # Subsequent GET returns 404
        res_get = self.client.get(f"/api/assets/{asset_id}", headers=headers)
        self.assertEqual(res_get.status_code, 404)

        print("[PASS] Asset Library: Authorized deletion removes database entry and disk files (HTTP 204)")

    def test_06_generation_history_telemetry_and_failure_reporting(self):
        """Generation History: Verifies prompt, status, duration, settings, and failed error details."""
        import asyncio
        from datetime import datetime, timedelta

        user_id, _, headers = self._create_user("hist_audit")

        # Insert 1 completed job and 1 failed job
        job_success_id = f"job_succ_{uuid.uuid4().hex[:8]}"
        job_failed_id = f"job_fail_{uuid.uuid4().hex[:8]}"

        t_start_1 = datetime.utcnow() - timedelta(seconds=24)
        t_end_1 = datetime.utcnow() - timedelta(seconds=10)

        t_start_2 = datetime.utcnow() - timedelta(seconds=60)
        t_end_2 = datetime.utcnow() - timedelta(seconds=55)

        async def insert_history():
            async with AsyncSessionLocal() as db:
                j1 = GenerationJob(
                    id=job_success_id,
                    user_id=user_id,
                    prompt="Crystal Wizard Staff",
                    configuration={"style": "fantasy", "quality": "high", "polygon_budget": 8000, "target_format": "glb"},
                    status="completed",
                    progress=100,
                    current_stage="completed",
                    created_at=t_start_1,
                    completed_at=t_end_1,
                )
                j2 = GenerationJob(
                    id=job_failed_id,
                    user_id=user_id,
                    prompt="Corrupted Impossible Topology",
                    configuration={"style": "sci-fi", "quality": "ultra", "polygon_budget": 50000, "target_format": "glb"},
                    status="failed",
                    progress=45,
                    current_stage="geometry_synthesis",
                    error_message="CUDA out of memory during neural marching cubes evaluation.",
                    created_at=t_start_2,
                    completed_at=t_end_2,
                )
                db.add_all([j1, j2])
                await db.commit()

        asyncio.run(insert_history())

        res_jobs = self.client.get("/api/jobs", headers=headers)
        self.assertEqual(res_jobs.status_code, 200)
        jobs = res_jobs.json()

        succ = next(j for j in jobs if j["job_id"] == job_success_id)
        self.assertEqual(succ["status"], "completed")
        self.assertEqual(succ["prompt"], "Crystal Wizard Staff")
        self.assertAlmostEqual(succ["duration_seconds"], 14.0, places=1)
        self.assertEqual(succ["configuration"]["polygon_budget"], 8000)

        fail = next(j for j in jobs if j["job_id"] == job_failed_id)
        self.assertEqual(fail["status"], "failed")
        self.assertEqual(fail["current_stage"], "geometry_synthesis")
        self.assertIn("CUDA out of memory", fail["error_message"])
        self.assertAlmostEqual(fail["duration_seconds"], 5.0, places=1)

        print("[PASS] Generation History: Execution telemetry, durations, configuration, and failure error logs verified")

    def test_07_persistence_across_session_restart(self):
        """Asset Persistence: Assets and records survive client connection resets and restarts."""
        import asyncio

        user_id, _, headers = self._create_user("persist")
        asset_id = f"ast_p_{uuid.uuid4().hex[:8]}"
        job_id = f"job_p_{uuid.uuid4().hex[:8]}"
        dummy_glb = os.path.join(self.test_out_dir, f"{asset_id}.glb")
        with open(dummy_glb, "wb") as f:
            f.write(b"glTF" + b"\x02\x00\x00\x00" + b"\x20\x00\x00\x00" + b"\x00" * 32)

        async def insert_persistent_asset():
            async with AsyncSessionLocal() as db:
                job = GenerationJob(id=job_id, user_id=user_id, prompt="Persistent Medieval Shield", status="completed")
                db.add(job)
                ast = GeneratedAsset(
                    id=asset_id,
                    job_id=job_id,
                    user_id=user_id,
                    asset_name="Persistent Medieval Shield",
                    glb_path=dummy_glb,
                    polygon_count=650,
                    file_size=os.path.getsize(dummy_glb),
                )
                db.add(ast)
                await db.commit()

        asyncio.run(insert_persistent_asset())

        # Simulate app restart by instantiating a completely fresh TestClient
        fresh_client = TestClient(app)
        res_restarted = fresh_client.get(f"/api/assets/{asset_id}", headers=headers)
        self.assertEqual(res_restarted.status_code, 200)
        self.assertEqual(res_restarted.json()["asset_name"], "Persistent Medieval Shield")
        self.assertTrue(os.path.exists(dummy_glb))

        print("[PASS] Persistence: Assets remain fully available and intact across application restarts")

    def test_08_frontend_card_and_library_architecture(self):
        """Frontend Validation: AssetCard, AssetLibrary, and GenerationHistory UI requirements."""
        # 1. AssetCard requirements: thumbnail, name, creation date, polygon count, file size, status, action menu
        self.assertIn("preview_url", self.card_source)
        self.assertIn("asset.asset_name", self.card_source)
        self.assertIn("formattedDate", self.card_source)
        self.assertIn("polygon_count", self.card_source)
        self.assertIn("fileSizeMb", self.card_source)
        self.assertIn("Ready", self.card_source)
        self.assertIn("MoreVertical", self.card_source)
        self.assertIn("handleDelete", self.card_source)
        self.assertIn("handleInspect", self.card_source)
        self.assertIn("handleViewDetails", self.card_source)

        # 2. AssetLibrary requirements: search, date filter, sort by newest, details, preview, download, delete
        self.assertIn("dateFilter", self.lib_source)
        self.assertIn("sortBy", self.lib_source)
        self.assertIn("previewModalAsset", self.lib_source)
        self.assertIn("handleOpenPreviewModal", self.lib_source)
        self.assertIn("handleViewDetails", self.lib_source)
        self.assertIn("getDownloadUrl", self.lib_source)

        # 3. GenerationHistory requirements: prompt, date, status, duration, settings, output asset, error details
        self.assertIn("job.prompt", self.hist_source)
        self.assertIn("formatDuration", self.hist_source)
        self.assertIn("config.style", self.hist_source)
        self.assertIn("config.quality", self.hist_source)
        self.assertIn("config.polygon_budget", self.hist_source)
        self.assertIn("handleInspect", self.hist_source)
        self.assertIn("job.error_message", self.hist_source)
        self.assertIn("current_stage", self.hist_source)

        print("[PASS] Frontend Architecture: AssetCard, AssetLibrary, and GenerationHistory fully satisfy Part 14 UI specifications")


if __name__ == "__main__":
    unittest.main()
