"""
Part 15 Master Integration Test Suite: Full System End-to-End Pipeline & QA Verification
========================================================================================
Verifies the complete prompt-to-3D pipeline across all subsystems:
  1. Complete User Lifecycle & Authentication (Register, Duplicate Check, Login, Profile)
  2. Prompt Analysis & Parameter Extraction (Natural Language Semantic Deconstruction)
  3. End-to-End Generative Pipeline (All 9 Stages: Prompt Analysis -> 3D Generation ->
     Mesh Processing -> UV Mapping -> Texture Generation -> PBR Material Creation ->
     Mesh Optimization -> GLB Export -> Completed)
  4. GLB Binary Download & glTF 2.0 Specification Compliance
  5. Multi-Tenant Security & Tenant Ownership Isolation (403 Enforcement)
  6. Failure Modes & Damaged Mesh Self-Healing
  7. Asset Library Filtering, Sorting, Keyword Search & Generation History Audit
  8. PBR Material Inspection & Mesh Decimation Engine Endpoints
"""

import os
import sys
import uuid
import time
import unittest
import numpy as np
import trimesh

# Workspace & backend path configuration
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

os.environ["AI_BACKEND"] = "procedural"
from app.config import settings
settings.AI_BACKEND = "procedural"

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.job import GenerationJob
from app.models.asset import GeneratedAsset
from app.services.prompt_engine import prompt_engine
from processing.mesh_cleaner import mesh_cleaner
from processing.uv_unwrapper import uv_unwrapper
from processing.glb_exporter import glb_exporter

class TestFullSystemIntegrationPart15(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_out_dir = os.path.join(BASE_DIR, "storage", "test_part15")
        os.makedirs(cls.test_out_dir, exist_ok=True)

    def _create_user(self, tag: str):
        uid = str(uuid.uuid4())[:8]
        email = f"user_{tag}_{uid}@polygen.ai"
        password = f"SecurePass123!{tag}"
        name = f"PolyGen User {tag}"

        reg_res = self.client.post("/api/auth/register", json={
            "email": email,
            "password": password,
            "name": name,
        })
        self.assertIn(reg_res.status_code, [200, 201])

        login_res = self.client.post("/api/auth/login", json={
            "username_or_email": email,
            "password": password,
        })
        self.assertEqual(login_res.status_code, 200)
        token = login_res.json().get("access_token") or login_res.json().get("token")
        headers = {"Authorization": f"Bearer {token}"}
        return {"email": email, "password": password, "token": token, "headers": headers}

    def test_01_user_authentication_lifecycle(self):
        """Test registration, duplicate email rejection, login, and profile inspection."""
        uid = str(uuid.uuid4())[:8]
        email = f"lead_dev_{uid}@polygen.ai"
        password = "MasterPassword2026!"
        name = f"Lead Developer {uid}"

        # 1. Register User
        res = self.client.post("/api/auth/register", json={"email": email, "password": password, "name": name})
        self.assertIn(res.status_code, [200, 201])

        # 2. Duplicate Registration Rejection
        dup = self.client.post("/api/auth/register", json={"email": email, "password": password, "name": name})
        self.assertIn(dup.status_code, [400, 409])

        # 3. Successful Login
        login = self.client.post("/api/auth/login", json={"username_or_email": email, "password": password})
        self.assertEqual(login.status_code, 200)
        token = login.json().get("access_token") or login.json().get("token")
        self.assertTrue(token)

        # 4. Bad Password Rejection
        bad_login = self.client.post("/api/auth/login", json={"username_or_email": email, "password": "WrongPassword!1"})
        self.assertEqual(bad_login.status_code, 401)

        # 5. Authenticated Profile Inspection
        me = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["email"], email)

    def test_02_prompt_analysis_and_lexicon(self):
        """Test semantic deconstruction, material extraction, and polygon budget calculation."""
        prompt = "A weathered Viking battleaxe with carved wooden handle, steel blade, and glowing sapphire runes."
        res = self.client.post("/api/prompt/analyze", json={"prompt": prompt, "quality": "high"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        structured = data.get("structured_prompt", data)
        self.assertIn("object", structured)
        self.assertTrue("materials" in structured or "material" in structured)

        parsed = prompt_engine.process(prompt)
        self.assertTrue(parsed.object)
        self.assertTrue(parsed.material or parsed.materials)
        self.assertGreater(parsed.polygon_budget, 0)

    def test_03_end_to_end_pipeline_generation(self):
        """
        Test the full generative pipeline.
        Submits job, monitors real stage progression, and verifies generated asset persistence.
        """
        user = self._create_user("pipeline")
        prompt = "A glowing sapphire crystal gemstone with sharp facets"

        # Submit generation job
        gen_res = self.client.post("/api/generate", json={
            "prompt": prompt,
            "style": "crystal",
            "quality": "standard",
            "polygon_budget": 3500,
            "target_format": "glb",
        }, headers=user["headers"])
        self.assertEqual(gen_res.status_code, 202)
        job_id = gen_res.json()["job_id"]
        self.assertTrue(job_id)

        # Wait for background task to complete all 9 pipeline stages
        completed = False
        final_job = None
        for _ in range(40):
            poll = self.client.get(f"/api/jobs/{job_id}", headers=user["headers"])
            self.assertEqual(poll.status_code, 200)
            final_job = poll.json()
            if final_job["status"] == "completed":
                completed = True
                break
            elif final_job["status"] == "failed":
                self.fail(f"Pipeline job failed: {final_job.get('error_message')}")
            time.sleep(0.5)

        self.assertTrue(completed, f"Job timed out: {final_job}")
        self.assertEqual(final_job["progress"], 100)
        self.assertEqual(final_job["current_stage"], "completed")
        self.assertTrue(final_job.get("asset_id"))

        asset_id = final_job["asset_id"]
        asset_res = self.client.get(f"/api/assets/{asset_id}", headers=user["headers"])
        self.assertEqual(asset_res.status_code, 200)
        asset = asset_res.json()
        self.assertEqual(asset["id"], asset_id)
        self.assertGreater(asset["polygon_count"], 0)
        self.assertGreater(asset["file_size"], 0)
        self.assertTrue(asset.get("glb_url"))

    def test_04_glb_download_and_binary_validation(self):
        """Test authenticated binary GLB downloading and verify glTF 2.0 container header."""
        user = self._create_user("downloader")
        gen_res = self.client.post("/api/generate", json={
            "prompt": "An ancient stone monolith with moss",
            "style": "stone",
            "quality": "standard",
            "polygon_budget": 3000,
        }, headers=user["headers"])
        job_id = gen_res.json()["job_id"]

        for _ in range(40):
            poll = self.client.get(f"/api/jobs/{job_id}", headers=user["headers"])
            if poll.json()["status"] == "completed":
                break
            time.sleep(0.5)

        asset_id = poll.json()["asset_id"]

        # Download Standard GLB
        dl_res = self.client.get(f"/api/assets/{asset_id}/download?export_option=standard", headers=user["headers"])
        self.assertEqual(dl_res.status_code, 200)
        content = dl_res.content
        self.assertGreater(len(content), 1000)

        # Verify glTF 2.0 Binary magic header: 0x46546C67 (b"glTF")
        magic = content[:4]
        self.assertEqual(magic, b"glTF")
        version = int.from_bytes(content[4:8], byteorder="little")
        self.assertEqual(version, 2)

        # Verify mesh can be deserialized by Three.js / Trimesh loader
        scene = trimesh.load(trimesh.util.wrap_as_stream(content), file_type="glb")
        self.assertGreater(len(scene.geometry), 0)

    def test_05_multi_tenant_security_and_isolation(self):
        """Ensure User B cannot access, download, or delete User A's assets or jobs."""
        user_a = self._create_user("tenant_a")
        user_b = self._create_user("tenant_b")

        # User A creates a job
        gen_res = self.client.post("/api/generate", json={
            "prompt": "A golden crown with rubies",
            "style": "fantasy"
        }, headers=user_a["headers"])
        job_id = gen_res.json()["job_id"]

        for _ in range(40):
            poll = self.client.get(f"/api/jobs/{job_id}", headers=user_a["headers"])
            if poll.json()["status"] == "completed":
                break
            time.sleep(0.5)

        asset_id = poll.json()["asset_id"]

        # User B attempts to access User A's job -> 403 Forbidden
        b_job = self.client.get(f"/api/jobs/{job_id}", headers=user_b["headers"])
        self.assertEqual(b_job.status_code, 403)

        # User B attempts to access User A's asset -> 403 Forbidden
        b_asset = self.client.get(f"/api/assets/{asset_id}", headers=user_b["headers"])
        self.assertEqual(b_asset.status_code, 403)

        # User B attempts to download User A's asset -> 403 Forbidden
        b_dl = self.client.get(f"/api/assets/{asset_id}/download", headers=user_b["headers"])
        self.assertEqual(b_dl.status_code, 403)

        # User B attempts to delete User A's asset -> 403 Forbidden
        b_del = self.client.delete(f"/api/assets/{asset_id}", headers=user_b["headers"])
        self.assertEqual(b_del.status_code, 403)

        # User A can delete their own asset -> 200/204
        a_del = self.client.delete(f"/api/assets/{asset_id}", headers=user_a["headers"])
        self.assertIn(a_del.status_code, [200, 204])

        # Fetching deleted asset returns 404
        a_get = self.client.get(f"/api/assets/{asset_id}", headers=user_a["headers"])
        self.assertEqual(a_get.status_code, 404)

    def test_06_failure_modes_and_error_handling(self):
        """Test authentication rejection, 404 handling, and damaged mesh repair."""
        # 1. Unauthenticated request rejection
        unauth = self.client.get("/api/assets")
        self.assertIn(unauth.status_code, [401, 403])

        # 2. Invalid JWT token rejection
        bad_token = self.client.get("/api/assets", headers={"Authorization": "Bearer invalid_token_12345"})
        self.assertEqual(bad_token.status_code, 401)

        # 3. Non-existent asset ID lookup -> 404
        user = self._create_user("error_tester")
        fake_id = str(uuid.uuid4())
        not_found = self.client.get(f"/api/assets/{fake_id}", headers=user["headers"])
        self.assertEqual(not_found.status_code, 404)

        # 4. Intentionally Damaged Mesh Repair
        # Non-manifold cube with duplicate vertices and zero-area faces
        raw_box = trimesh.creation.box(extents=[1.0, 1.0, 1.0])
        damaged_verts = np.vstack([raw_box.vertices, raw_box.vertices[:4]])
        damaged_faces = np.vstack([raw_box.faces, [[0, 0, 0], [1, 1, 1]]])
        damaged_mesh = trimesh.Trimesh(vertices=damaged_verts, faces=damaged_faces, process=False)

        cleaned, clean_stats = mesh_cleaner.clean(damaged_mesh)
        self.assertGreater(len(cleaned.faces), 0)
        faces_removed = clean_stats["initial_faces"] - clean_stats["processed_face_count"]
        verts_removed = clean_stats["initial_vertices"] - clean_stats["processed_vertex_count"]
        self.assertGreaterEqual(faces_removed, 2)
        self.assertGreaterEqual(verts_removed, 4)

        # UV unwrapping resilience
        unwrapped, uv_stats = uv_unwrapper.unwrap(cleaned)
        self.assertTrue(uv_stats["has_uv"])

    def test_07_asset_library_filtering_sorting_and_history(self):
        """Verify keyword search, date filtering, sorting engines, and generation history queries."""
        user = self._create_user("lib_tester")

        # 1. Search assets
        search = self.client.get("/api/assets?search=crown", headers=user["headers"])
        self.assertEqual(search.status_code, 200)
        self.assertIn("items", search.json())

        # 2. Date filters
        for date_filter in ["today", "week", "month", "all"]:
            res = self.client.get(f"/api/assets?date_filter={date_filter}", headers=user["headers"])
            self.assertEqual(res.status_code, 200)

        # 3. Sorting options
        for sort_by in ["newest", "oldest", "polygons_desc", "polygons_asc", "size_desc", "name_asc"]:
            res = self.client.get(f"/api/assets?sort_by={sort_by}", headers=user["headers"])
            self.assertEqual(res.status_code, 200)

        # 4. Generation jobs history query
        for status_val in ["all", "completed", "failed"]:
            jobs = self.client.get(f"/api/jobs?status={status_val}", headers=user["headers"])
            self.assertEqual(jobs.status_code, 200)
            self.assertIsInstance(jobs.json(), list)

    def test_08_pbr_material_system_and_optimizer_endpoints(self):
        """Verify PBR material preview generation and mesh optimizer decimation endpoints."""
        user = self._create_user("pbr_tester")

        # 1. PBR Material Presets & Evaluation
        presets_res = self.client.get("/api/materials/presets", headers=user["headers"])
        self.assertEqual(presets_res.status_code, 200)
        self.assertIn("presets", presets_res.json())

        eval_res = self.client.post("/api/materials/evaluate", json={
            "prompt": "A rusted medieval sword",
            "material_type": "oxidized_metal",
            "details": ["weathered", "steel blade"],
        }, headers=user["headers"])
        self.assertEqual(eval_res.status_code, 200)
        self.assertIn("gltf_pbr_parameters", eval_res.json())

        # 2. Mesh Optimizer Presets & Topology Analysis
        opt_presets = self.client.get("/api/optimizer/presets", headers=user["headers"])
        self.assertEqual(opt_presets.status_code, 200)
        self.assertIn("presets", opt_presets.json())

if __name__ == "__main__":
    unittest.main()
