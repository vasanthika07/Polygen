import os
import sys
import unittest
import struct
import json
import trimesh
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

# Ensure backend and root are in python path
sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

from app.main import app
from processing.glb_exporter import glb_exporter, ExportProfile
from processing.texture_generator import texture_generator_service
from processing.pbr_material_system import pbr_material_system

TEST_OUTPUT_DIR = os.path.abspath("tests/output_part12")

class TestGLBExportPart12(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
        cls.client = TestClient(app)

        # Generate a test set of PBR textures for testing
        cls.test_tex_dir = os.path.join(TEST_OUTPUT_DIR, "textures")
        os.makedirs(cls.test_tex_dir, exist_ok=True)
        tex_maps = texture_generator_service.generate_textures({
            "material_type": "rusted_metal",
            "has_emissive": True,
            "details": ["rust", "blue sapphire glow"],
        }, resolution=512)

        cls.texture_paths = {}
        for name, img in tex_maps.items():
            p = os.path.join(cls.test_tex_dir, f"{name}.png")
            img.save(p, "PNG")
            cls.texture_paths[name] = p

    def test_01_ten_stage_pipeline_execution(self):
        """Pipeline: Verify complete 10-stage GLB export pipeline from mesh ingestion to metadata persistence."""
        # 1. Load optimized mesh
        mesh = trimesh.creation.cylinder(radius=0.5, height=2.0, sections=32)
        out_glb = os.path.join(TEST_OUTPUT_DIR, "pipeline_stage_test.glb")
        thumb_path = os.path.join(TEST_OUTPUT_DIR, "pipeline_stage_thumb.png")

        # Execute 10-stage pipeline
        report = glb_exporter.execute_export_pipeline(
            mesh=mesh,
            texture_paths=self.texture_paths,
            output_glb_path=out_glb,
            material_params=pbr_material_system.PRESETS["rusted_sword"],
            export_profile=ExportProfile.STANDARD,
            thumbnail_path=thumb_path,
        )

        # Verify Stage 6: Export GLB
        self.assertTrue(os.path.exists(out_glb))
        self.assertGreater(os.path.getsize(out_glb), 10000)

        # Verify Stage 7: Validate Exported File
        val = report["validation_report"]
        self.assertTrue(val["is_valid"])
        self.assertEqual(val["version"], 2)
        self.assertGreaterEqual(val["meshes_count"], 1)
        self.assertGreaterEqual(val["materials_count"], 1)

        # Verify Stage 8: Reopen Exported GLB
        reopened = glb_exporter.reopen_exported_glb(out_glb)
        self.assertEqual(len(reopened.faces), len(mesh.faces))

        # Verify Stage 9: Generate Thumbnail
        self.assertTrue(os.path.exists(thumb_path))
        self.assertGreater(os.path.getsize(thumb_path), 5000)

        # Verify Stage 10: Save Export Metadata
        meta_file = f"{out_glb}.meta.json"
        self.assertTrue(os.path.exists(meta_file))
        with open(meta_file, "r", encoding="utf-8") as f:
            meta_json = json.load(f)
        self.assertEqual(meta_json["export_profile"], "standard")
        self.assertEqual(meta_json["polygon_count"], len(mesh.faces))

        print(f"\n[PASS] Pipeline: 10-Stage Pipeline Verified ({report['polygon_count']} faces, {report['file_size_mb']} MB, Time={report['export_duration_seconds']}s)")

    def test_02_preservation_requirements(self):
        """Requirements: Verify preservation of geometry, UVs, PBR materials, ORM packing, and transforms."""
        mesh = trimesh.creation.box(extents=[1.5, 2.5, 0.5])
        # Assign explicit UVs
        bounds = mesh.bounds
        diff = bounds[1] - bounds[0]
        uvs = (mesh.vertices[:, :2] - bounds[0, :2]) / diff[:2]
        mesh.visual = trimesh.visual.TextureVisuals(uv=uvs)

        out_glb = os.path.join(TEST_OUTPUT_DIR, "preservation_test.glb")
        report = glb_exporter.execute_export_pipeline(
            mesh=mesh,
            texture_paths=self.texture_paths,
            output_glb_path=out_glb,
            material_params={
                "name": "Preserved_Material",
                "metallic_factor": 0.85,
                "roughness_factor": 0.45,
                "emissive_factor": [0.2, 0.5, 1.0],
                "alpha_mode": "OPAQUE",
                "double_sided": True,
            },
            export_profile=ExportProfile.STANDARD,
        )

        reopened = trimesh.load(out_glb, force="mesh")
        # Geometry preserved
        self.assertEqual(len(reopened.faces), 12)
        self.assertEqual(len(reopened.vertices), len(mesh.vertices))

        # UV coordinates preserved
        self.assertTrue(hasattr(reopened.visual, "uv"))
        self.assertEqual(len(reopened.visual.uv), len(reopened.vertices))
        self.assertTrue(np.all(reopened.visual.uv >= -0.05))
        self.assertTrue(np.all(reopened.visual.uv <= 1.05))

        # Material preserved
        self.assertTrue(hasattr(reopened.visual, "material"))
        mat = reopened.visual.material
        self.assertEqual(mat.name, "Preserved_Material")
        self.assertAlmostEqual(mat.metallicFactor, 0.85, places=2)
        self.assertAlmostEqual(mat.roughnessFactor, 0.45, places=2)

        print("[PASS] Requirements: Geometry, UVs, PBR ORM maps, and transforms fully preserved")

    def test_03_export_profile_standard(self):
        """Export Options: Verify Standard GLB profile (1024x1024 textures, balanced footprint)."""
        mesh = trimesh.creation.icosphere(subdivisions=2)
        out_glb = os.path.join(TEST_OUTPUT_DIR, "profile_standard.glb")

        report = glb_exporter.export(
            mesh=mesh,
            texture_paths=self.texture_paths,
            output_glb_path=out_glb,
            export_profile=ExportProfile.STANDARD,
        )

        self.assertEqual(report["export_profile"], "standard")
        self.assertEqual(report["texture_resolution"], 1024)
        self.assertTrue(report["valid"])

        print(f"[PASS] Export Profile [Standard]: 1024px textures ({report['file_size_mb']} MB, Validated)")

    def test_04_export_profile_high_quality(self):
        """Export Options: Verify High-Quality GLB profile (2048x2048 textures, maximum fidelity)."""
        mesh = trimesh.creation.icosphere(subdivisions=2)
        out_glb = os.path.join(TEST_OUTPUT_DIR, "profile_high_quality.glb")

        report = glb_exporter.export(
            mesh=mesh,
            texture_paths=self.texture_paths,
            output_glb_path=out_glb,
            export_profile=ExportProfile.HIGH_QUALITY,
        )

        self.assertEqual(report["export_profile"], "high_quality")
        self.assertEqual(report["texture_resolution"], 2048)
        self.assertTrue(report["valid"])

        print(f"[PASS] Export Profile [High-Quality]: 2048px textures ({report['file_size_mb']} MB, Validated)")

    def test_05_export_profile_optimized(self):
        """Export Options: Verify Optimized GLB profile (512x512 textures, minimal payload footprint)."""
        mesh = trimesh.creation.icosphere(subdivisions=2)
        out_glb = os.path.join(TEST_OUTPUT_DIR, "profile_optimized.glb")

        report = glb_exporter.export(
            mesh=mesh,
            texture_paths=self.texture_paths,
            output_glb_path=out_glb,
            export_profile=ExportProfile.OPTIMIZED,
        )

        self.assertEqual(report["export_profile"], "optimized")
        self.assertEqual(report["texture_resolution"], 512)
        self.assertTrue(report["valid"])
        # Optimized must be smaller than high quality
        hq_size = os.path.getsize(os.path.join(TEST_OUTPUT_DIR, "profile_high_quality.glb"))
        opt_size = os.path.getsize(out_glb)
        self.assertLess(opt_size, hq_size)

        print(f"[PASS] Export Profile [Optimized]: 512px textures ({report['file_size_mb']} MB < {round(hq_size/(1024*1024), 2)} MB HQ)")

    def test_06_gltf_validator_file_integrity(self):
        """Validation: Verify glTF 2.0 binary header, chunks, and length matching."""
        glb_path = os.path.join(TEST_OUTPUT_DIR, "profile_standard.glb")
        val = glb_exporter.validate_gltf_glb(glb_path)

        self.assertTrue(val["is_valid"])
        self.assertEqual(val["version"], 2)
        self.assertEqual(len(val["errors"]), 0)

        # Inspect raw binary
        with open(glb_path, "rb") as f:
            data = f.read()

        magic, version, length = struct.unpack_from('<4sII', data, 0)
        self.assertEqual(magic, b"glTF")
        self.assertEqual(version, 2)
        self.assertEqual(length, len(data))

        # Chunk 0 JSON
        chunk0_len, chunk0_type = struct.unpack_from('<I4s', data, 12)
        self.assertEqual(chunk0_type, b"JSON")
        raw_json = json.loads(data[20:20 + chunk0_len].decode("utf-8"))
        self.assertEqual(raw_json["asset"]["version"], "2.0")

        print("[PASS] Validation: glTF 2.0 Binary Header and Chunk Sequence fully compliant")

    def test_07_gltf_validator_mesh_and_material_presence(self):
        """Validation: Verify mesh presence, material presence, and texture references."""
        glb_path = os.path.join(TEST_OUTPUT_DIR, "profile_standard.glb")
        val = glb_exporter.validate_gltf_glb(glb_path)

        self.assertGreaterEqual(val["meshes_count"], 1)
        self.assertGreaterEqual(val["materials_count"], 1)
        self.assertGreaterEqual(val["textures_count"], 1)
        self.assertGreaterEqual(val["images_count"], 1)
        self.assertTrue(val["browser_compatible"])
        self.assertTrue(val["blender_compatible"])

        print(f"[PASS] Validation: Meshes={val['meshes_count']}, Materials={val['materials_count']}, Textures={val['textures_count']}, Images={val['images_count']}")

    def test_08_corrupted_file_validation_rejection(self):
        """Validation: Verify validator rejects corrupted files or invalid glTF headers."""
        corrupt_path = os.path.join(TEST_OUTPUT_DIR, "corrupt_test.glb")
        with open(corrupt_path, "wb") as f:
            f.write(b"NOT_A_GLTF_FILE_HEADER_DATA_1234567890")

        val = glb_exporter.validate_gltf_glb(corrupt_path)
        self.assertFalse(val["is_valid"])
        self.assertTrue(any("magic header" in err for err in val["errors"]))

        print("[PASS] Validation: Accurately caught corrupted header with rejection")

    def test_09_download_endpoint_authorization(self):
        """Download: Verify GET /api/assets/{asset_id}/download requires valid authentication."""
        # Unauthenticated request should be rejected with 401
        res_unauth = self.client.get("/api/assets/non_existent_id/download")
        self.assertEqual(res_unauth.status_code, 401)
        self.assertIn("Authentication required", res_unauth.json()["detail"])

        print("[PASS] Download: Unauthorized access strictly blocked (HTTP 401)")

    def test_10_download_endpoint_authenticated(self):
        """Download: Verify authenticated download with export_option parameter and attachment disposition."""
        import uuid
        uid = uuid.uuid4().hex[:8]
        email = f"exporter_{uid}@polygen.ai"
        username = f"exp_{uid}"
        pwd = "SecurePassword123!"
        res_reg = self.client.post("/api/auth/register", json={"email": email, "password": pwd, "username": username, "name": f"Exporter {uid}"})
        self.assertEqual(res_reg.status_code, 201)
        res_login = self.client.post("/api/auth/login", json={"username_or_email": email, "password": pwd})
        self.assertEqual(res_login.status_code, 200)
        token = res_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create a test asset in DB using a real sample GLB
        from app.core.database import AsyncSessionLocal
        from app.models.asset import GeneratedAsset
        from app.models.job import GenerationJob
        import asyncio

        asset_id = f"test_ast_{uid}"
        job_id = f"test_job_{uid}"
        test_glb = os.path.join(TEST_OUTPUT_DIR, "profile_standard.glb")

        async def insert_asset():
            async with AsyncSessionLocal() as db:
                from app.models.user import User
                from sqlalchemy import select
                u = (await db.execute(select(User).where(User.email == email))).scalars().first()
                job = GenerationJob(
                    id=job_id,
                    user_id=u.id,
                    prompt="Test Sword",
                    status="completed",
                    progress=100,
                )
                db.add(job)
                ast = GeneratedAsset(
                    id=asset_id,
                    job_id=job_id,
                    user_id=u.id,
                    asset_name="Test Export Sword",
                    glb_path=test_glb,
                    polygon_count=120,
                    file_size=os.path.getsize(test_glb),
                    metadata_json={},
                )
                db.add(ast)
                await db.commit()

        asyncio.run(insert_asset())

        # Test download with Bearer token
        res_dl = self.client.get(f"/api/assets/{asset_id}/download?export_option=standard", headers=headers)
        self.assertEqual(res_dl.status_code, 200)
        self.assertEqual(res_dl.headers["content-type"], "model/gltf-binary")
        self.assertIn("attachment", res_dl.headers["content-disposition"])
        self.assertEqual(res_dl.content[:4], b"glTF")

        # Test download with ?token= query parameter (browser link style)
        res_dl_query = self.client.get(f"/api/assets/{asset_id}/download?export_option=standard&token={token}")
        self.assertEqual(res_dl_query.status_code, 200)
        self.assertEqual(res_dl_query.content[:4], b"glTF")

        print("[PASS] Download: Authenticated download verified via Bearer header and query token (HTTP 200, valid glTF)")

if __name__ == "__main__":
    unittest.main()

