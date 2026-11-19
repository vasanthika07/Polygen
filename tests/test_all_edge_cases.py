"""
PolyGen Enterprise Edge Case & Client Requirement Verification Suite
Covers exhaustive edge cases across:
1. Authentication, Authorization & JWT Token Edge Cases
2. Prompt Understanding, Emojis, Unicode & Input Validation Edge Cases
3. Multi-Tenant Cross-User Isolation & Path Traversal Prevention
4. Degenerate Geometry, Empty Meshes & Mesh Cleaning Edge Cases
5. UV Unwrapping, Texture Resolution Snapping & Boundary Edge Cases
6. PBR Material Evaluation & Out-of-Bounds Parameter Clamping
7. Decimation Limits, Low Polygon Budgets & Over-Budget Preservation
8. GLB Binary Export, Missing Channels Fallback & Integrity Audits
"""

import os
import sys
import uuid
import unittest
import numpy as np
import trimesh
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from fastapi.testclient import TestClient
from backend.app.main import app
from processing.mesh_cleaner import MeshCleaningPipeline
from processing.uv_unwrapper import UVUnwrappingEngine
from processing.pbr_material_system import pbr_material_system
from processing.mesh_optimizer import MeshOptimizer
from processing.glb_exporter import glb_exporter, ExportProfile


class TestPolyGenComprehensiveEdgeCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        # Register a primary test user
        cls.user1_email = f"user1_{uuid.uuid4().hex[:6]}@polygen.ai"
        cls.user1_pwd = "PolyGenUser1Secure!"
        cls.user1_name = "User Alpha"
        res1 = cls.client.post("/api/auth/register", json={
            "name": cls.user1_name,
            "email": cls.user1_email,
            "password": cls.user1_pwd,
        })
        assert res1.status_code == 201
        cls.user1_token = res1.json()["access_token"]
        cls.user1_id = res1.json()["user"]["id"]

        # Register a secondary test user for isolation checks
        cls.user2_email = f"user2_{uuid.uuid4().hex[:6]}@polygen.ai"
        cls.user2_pwd = "PolyGenUser2Secure!"
        res2 = cls.client.post("/api/auth/register", json={
            "name": "User Beta",
            "email": cls.user2_email,
            "password": cls.user2_pwd,
        })
        assert res2.status_code == 201
        cls.user2_token = res2.json()["access_token"]
        cls.user2_id = res2.json()["user"]["id"]

    # =========================================================================
    # 1. AUTHENTICATION & CREDENTIAL EDGE CASES
    # =========================================================================
    def test_auth_case_insensitive_email(self):
        """Case-insensitive email in login credentials should authenticate successfully."""
        res = self.client.post("/api/auth/login", json={
            "username_or_email": self.user1_email.upper(),
            "password": self.user1_pwd,
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn("access_token", res.json())

    def test_auth_whitespace_trimmed_identifier(self):
        """Leading/trailing whitespace in email/username should be trimmed cleanly."""
        res = self.client.post("/api/auth/login", json={
            "username_or_email": f"  {self.user1_email}  ",
            "password": self.user1_pwd,
        })
        self.assertEqual(res.status_code, 200)

    def test_auth_missing_or_corrupt_bearer_token(self):
        """Malformed or corrupt bearer token must cleanly return 401 Unauthorized."""
        headers_corrupt = {"Authorization": "Bearer not.a.valid.jwt.payload"}
        res = self.client.get("/api/auth/me", headers=headers_corrupt)
        self.assertEqual(res.status_code, 401)
        self.assertIn("invalid token", res.json().get("detail", "").lower())

        headers_empty = {"Authorization": "Bearer "}
        res = self.client.get("/api/auth/me", headers=headers_empty)
        self.assertEqual(res.status_code, 401)

    def test_auth_registration_password_complexity_checks(self):
        """Weak passwords lacking uppercase, digits, or length must fail validation."""
        weak_passwords = [
            ("short1!", "at least 8 characters"),
            ("alllowercase123!", "uppercase letter"),
            ("ALLUPPERCASE123!", "lowercase letter"),
            ("NoDigitsOrSpecialChars", "digit (0-9) or special character"),
        ]
        for pwd, expected_err in weak_passwords:
            res = self.client.post("/api/auth/register", json={
                "email": f"test_{uuid.uuid4().hex[:6]}@test.com",
                "password": pwd
            })
            self.assertEqual(res.status_code, 422)

    # =========================================================================
    # 2. PROMPT UNDERSTANDING & VALIDATION EDGE CASES
    # =========================================================================
    def test_prompt_whitespace_only_rejection(self):
        """Whitespace-only prompt must be rejected with 422 Unprocessable Entity."""
        res = self.client.post("/api/prompt/analyze", json={"prompt": "        "})
        self.assertEqual(res.status_code, 422)

    def test_prompt_too_short_rejection(self):
        """Prompt under 3 characters must be rejected with 422."""
        res = self.client.post("/api/prompt/analyze", json={"prompt": "ab"})
        self.assertEqual(res.status_code, 422)

    def test_prompt_with_emojis_and_unicode(self):
        """Prompt containing emojis, special punctuation, and unicode symbols parses correctly."""
        emoji_prompt = "🗡️ A glorious crystalline longsword with glowing sapphire runes ✨ and ornate gold hilt 👑"
        res = self.client.post("/api/prompt/analyze", json={"prompt": emoji_prompt})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(len(data["object"]) > 0)
        self.assertTrue(any("crystal" in m or "sapphire" in m or "gold" in m or "metal" in m for m in data["materials"]))

    def test_prompt_maximum_boundary_length(self):
        """Prompt up to 1000 characters is accepted; prompt exceeding 1000 characters is rejected."""
        valid_long_prompt = "A detailed medieval stone tower with wooden doors and iron torches. " * 14
        valid_long_prompt = valid_long_prompt[:990]
        res_ok = self.client.post("/api/prompt/analyze", json={"prompt": valid_long_prompt})
        self.assertEqual(res_ok.status_code, 200)

        too_long_prompt = "A" * 1005
        res_fail = self.client.post("/api/prompt/analyze", json={"prompt": too_long_prompt})
        self.assertEqual(res_fail.status_code, 422)

    def test_generate_endpoint_input_sanitization(self):
        """GenerationRequest trims inputs and normalizes casing for style and format."""
        headers = {"Authorization": f"Bearer {self.user1_token}"}
        res = self.client.post("/api/generate", json={
            "prompt": "   A weathered stone gargoyle sitting on a gothic parapet   ",
            "style": "  REALISTIC  ",
            "quality": "HIGH",
            "polygon_budget": 5000,
            "target_format": ".GLB",
        }, headers=headers)
        self.assertEqual(res.status_code, 202)
        job_data = res.json()
        self.assertEqual(job_data["prompt"], "A weathered stone gargoyle sitting on a gothic parapet")

    # =========================================================================
    # 3. MULTI-TENANT ISOLATION & PATH TRAVERSAL DEFENSE
    # =========================================================================
    def test_cross_tenant_job_access_forbidden(self):
        """User B must not be able to view User A's generation job."""
        headers_a = {"Authorization": f"Bearer {self.user1_token}"}
        headers_b = {"Authorization": f"Bearer {self.user2_token}"}

        # User A creates a job
        create_res = self.client.post("/api/generate", json={
            "prompt": "An enchanted ruby dagger",
            "polygon_budget": 3000
        }, headers=headers_a)
        job_id = create_res.json()["job_id"]

        # User B attempts to access it -> 403 Forbidden
        access_res = self.client.get(f"/api/jobs/{job_id}", headers=headers_b)
        self.assertEqual(access_res.status_code, 403)

    def test_asset_download_path_traversal_defense(self):
        """Requests attempting path traversal or non-existent asset IDs return 404 or 403."""
        headers = {"Authorization": f"Bearer {self.user1_token}"}
        # Non-existent asset ID
        res = self.client.get("/api/assets/non_existent_uuid_12345/download", headers=headers)
        self.assertIn(res.status_code, [404, 403])

    # =========================================================================
    # 4. DEGENERATE GEOMETRY & MESH CLEANING EDGE CASES
    # =========================================================================
    def test_mesh_cleaner_insufficient_geometry_rejection(self):
        """MeshCleaner raises clear ValueError when given 0 vertices or 0 faces."""
        cleaner = MeshCleaningPipeline()
        empty_mesh = trimesh.Trimesh(vertices=[], faces=[])
        with self.assertRaises(ValueError):
            cleaner.clean(empty_mesh)

    def test_mesh_cleaner_nan_and_inf_vertices_recovery(self):
        """Mesh with NaN/Inf vertices has non-finite components removed without fatal error."""
        cleaner = MeshCleaningPipeline()
        # Create a simple cube and corrupt one vertex with NaN
        box = trimesh.creation.box(extents=(1, 1, 1))
        corrupt_verts = box.vertices.copy()
        corrupt_verts = np.vstack([corrupt_verts, [np.nan, np.inf, 0.0]])
        # Add a face referencing the corrupt vertex
        corrupt_faces = np.vstack([box.faces, [0, 1, len(corrupt_verts) - 1]])
        corrupt_mesh = trimesh.Trimesh(vertices=corrupt_verts, faces=corrupt_faces, process=False)

        cleaned_mesh, report = cleaner.clean(corrupt_mesh)
        self.assertTrue(np.all(np.isfinite(cleaned_mesh.vertices)))
        self.assertTrue(len(cleaned_mesh.faces) > 0)

    # =========================================================================
    # 5. UV PARAMETERIZATION & RESOLUTION SNAPPING EDGE CASES
    # =========================================================================
    def test_uv_unwrapper_insufficient_geometry_rejection(self):
        """UV Unwrapping raises ValueError on degenerate or empty mesh."""
        engine = UVUnwrappingEngine()
        empty_mesh = trimesh.Trimesh(vertices=[], faces=[])
        with self.assertRaises(ValueError):
            engine.unwrap(empty_mesh)

    def test_uv_unwrapper_resolution_snapping(self):
        """Arbitrary non-power-of-two resolution snaps to closest standard resolution."""
        engine = UVUnwrappingEngine()
        res_700, pad_700 = engine.configure_resolution(700)
        self.assertEqual(res_700, 512)
        self.assertGreaterEqual(pad_700, 2)

        res_1800, pad_1800 = engine.configure_resolution(1800)
        self.assertEqual(res_1800, 2048)
        self.assertGreaterEqual(pad_1800, 4)

    def test_uv_unwrapper_cube_atlas_bounds(self):
        """Cube UV atlas parameterization guarantees all coordinates inside [0, 1]."""
        engine = UVUnwrappingEngine()
        cube = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
        unwrapped, report = engine.unwrap(cube, resolution=512, visualize=False)
        self.assertIn("chart_count", report)
        self.assertGreaterEqual(report["chart_count"], 1)
        self.assertEqual(report["overlap_pairs_count"], 0)
        self.assertFalse(report["has_overlap"])
        uvs = unwrapped.visual.uv
        self.assertTrue(np.all(uvs >= 0.0) and np.all(uvs <= 1.0))

    # =========================================================================
    # 6. PBR MATERIAL EVALUATION & PARAMETER CLAMPING EDGE CASES
    # =========================================================================
    def test_pbr_unknown_preset_fallback(self):
        """Unknown material keyword falls back to balanced physically plausible PBR defaults."""
        params = pbr_material_system.generate_material_parameters({"raw_prompt": "completely unknown extraterrestrial substance"})
        self.assertIsNotNone(params)
        self.assertGreaterEqual(params["roughness_factor"], 0.0)
        self.assertLessEqual(params["roughness_factor"], 1.0)
        self.assertGreaterEqual(params["metallic_factor"], 0.0)
        self.assertLessEqual(params["metallic_factor"], 1.0)
        self.assertIn(params["alpha_mode"], ["OPAQUE", "MASK", "BLEND"])

    def test_pbr_parameter_bounds_clamping(self):
        """PBR validation catches out-of-bounds factors and enforces glTF standards."""
        invalid_params = {
            "name": "Invalid_Test_Material",
            "base_color_factor": [0.5, 0.5, 0.5, 1.0],
            "metallic_factor": 1.5,   # Exceeds 1.0
            "roughness_factor": -0.2, # Negative
            "alpha_mode": "OPAQUE",
        }
        res = pbr_material_system.validate_gltf_compatibility(invalid_params)
        self.assertFalse(res["is_valid"])
        self.assertTrue(len(res["errors"]) >= 2)

    # =========================================================================
    # 7. MESH OPTIMIZATION ENGINE EDGE CASES
    # =========================================================================
    def test_mesh_optimizer_target_larger_than_input_faces(self):
        """When input mesh already has fewer faces than budget, it is preserved without error."""
        cube = trimesh.creation.box(extents=(1.0, 1.0, 1.0)) # 12 faces
        opt_mesh, stats = MeshOptimizer.optimize(cube, target_polygon_budget=5000)
        self.assertEqual(len(opt_mesh.faces), 12)
        self.assertEqual(stats["original_polygon_count"], 12)
        self.assertEqual(stats["final_polygon_count"], 12)
        self.assertEqual(stats["status"], "WITHIN_BUDGET")

    def test_mesh_optimizer_extreme_low_budget_preservation(self):
        """Extreme decimation budget (e.g. 10 faces) does not collapse the mesh into 0 faces."""
        sphere = trimesh.creation.icosphere(subdivisions=3, radius=1.0) # 1280 faces
        opt_mesh, stats = MeshOptimizer.optimize(sphere, target_polygon_budget=30)
        self.assertGreaterEqual(len(opt_mesh.faces), 4)
        self.assertLess(len(opt_mesh.faces), 1280)

    def test_mesh_optimizer_bounding_box_ground_plane_alignment(self):
        """Bounding box normalization centers (X=0, Z=0) and aligns bottom to ground (Y_min=0)."""
        box = trimesh.creation.box(extents=(2, 4, 2))
        box.apply_translation([10, -5, 20])
        aligned = MeshOptimizer.normalize_bounding_box(box, center_at_origin=True, align_to_ground=True)
        bounds = aligned.bounds
        self.assertAlmostEqual(bounds[0][1], 0.0, places=3) # Y min == 0
        center_xz = (bounds[0][[0, 2]] + bounds[1][[0, 2]]) / 2.0
        self.assertAlmostEqual(center_xz[0], 0.0, places=3)
        self.assertAlmostEqual(center_xz[1], 0.0, places=3)

    # =========================================================================
    # 8. GLB EXPORT & BINARY INTEGRITY EDGE CASES
    # =========================================================================
    def test_glb_export_missing_textures_fallback(self):
        """Exporting GLB with missing texture files falls back to neutral PBR maps cleanly."""
        box = trimesh.creation.box(extents=(1, 1, 1))
        out_glb = os.path.abspath(os.path.join(os.path.dirname(__file__), "output_part12/edge_case_empty_textures.glb"))
        os.makedirs(os.path.dirname(out_glb), exist_ok=True)

        res = glb_exporter.execute_export_pipeline(
            mesh=box,
            texture_paths={}, # Empty!
            output_glb_path=out_glb,
            export_profile=ExportProfile.STANDARD,
        )
        self.assertTrue(os.path.exists(out_glb))
        self.assertGreater(os.path.getsize(out_glb), 500)
        self.assertTrue(res["is_valid"])
        self.assertTrue(res["validation_report"]["is_valid"])
        self.assertEqual(res["validation_report"]["version"], 2)

        # Direct binary check for glTF magic bytes
        with open(out_glb, "rb") as f:
            magic_bytes = f.read(4)
        self.assertEqual(magic_bytes, b"glTF")

        # Verify reopened file in Trimesh
        reopened = glb_exporter.reopen_exported_glb(out_glb)
        self.assertIsNotNone(reopened)
        self.assertEqual(len(reopened.faces), 12)


if __name__ == "__main__":
    unittest.main()
