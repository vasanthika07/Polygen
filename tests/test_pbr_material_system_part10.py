import os
import sys
import unittest
import trimesh
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

# Ensure backend and root are in python path
sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

from app.main import app
from processing.pbr_material_system import pbr_material_system, MaterialClass
from processing.mesh_optimizer import mesh_optimizer
from processing.glb_exporter import glb_exporter
from processing.texture_generator import texture_generator_service
from processing.texture_baker import texture_baker

TEST_OUTPUT_DIR = os.path.abspath("tests/output_part10")

class TestPBRMaterialSystemPart10(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
        cls.client = TestClient(app)

    def test_01_material_classification(self):
        """Feature 1: Verify material classification into standard glTF 2.0 physical taxonomies."""
        test_cases = [
            ("A polished gold royal chalice", MaterialClass.CONDUCTOR_METAL),
            ("A rusted weathered iron sword with pitted steel", MaterialClass.OXIDIZED_METAL),
            ("A rustic carved oak dining table", MaterialClass.DIELECTRIC_ORGANIC),
            ("An ancient granite stone monument with moss", MaterialClass.DIELECTRIC_MINERAL),
            ("A crystal clear glass bottle with refractions", MaterialClass.TRANSLUCENT_GLASS),
            ("A radiant glowing blue sapphire crystal gem", MaterialClass.EMISSIVE_GEMSTONE),
            ("A cybernetic battle robot with metallic armor", MaterialClass.CONDUCTOR_METAL),
        ]

        for prompt, expected_class in test_cases:
            classification = pbr_material_system.classify_material({"raw_prompt": prompt})
            self.assertEqual(
                classification["material_class"],
                expected_class,
                f"Classification failed for: '{prompt}' (got {classification['material_class']}, expected {expected_class})"
            )
            self.assertGreaterEqual(classification["confidence"], 0.70)

        print("\n[PASS] Feature 1: Material Classification verified across 7 physical categories")

    def test_02_material_presets_generation(self):
        """Feature 2: Verify parameter generation for all calibrated PBR physical presets."""
        expected_presets = [
            "rusted_sword",
            "glowing_sapphire",
            "carved_wood",
            "granite_stone",
            "translucent_glass",
            "polished_gold",
        ]

        self.assertEqual(len(pbr_material_system.PRESETS), 6)

        for preset_key in expected_presets:
            preset = pbr_material_system.PRESETS[preset_key]
            self.assertIn("base_color_factor", preset)
            self.assertIn("metallic_factor", preset)
            self.assertIn("roughness_factor", preset)
            self.assertIn("normal_scale", preset)
            self.assertIn("occlusion_strength", preset)
            self.assertIn("emissive_factor", preset)
            self.assertIn("emissive_intensity", preset)
            self.assertIn("alpha_mode", preset)

            # Factors must adhere to [0.0, 1.0]
            self.assertTrue(0.0 <= preset["metallic_factor"] <= 1.0)
            self.assertTrue(0.0 <= preset["roughness_factor"] <= 1.0)
            self.assertEqual(len(preset["base_color_factor"]), 4)
            self.assertEqual(len(preset["emissive_factor"]), 3)
            self.assertIn(preset["alpha_mode"], ["OPAQUE", "MASK", "BLEND"])

        print("[PASS] Feature 2: All 6 calibrated PBR presets conform to glTF 2.0 schema")

    def test_03_tangent_calculation_gram_schmidt(self):
        """Feature 4: Verify mathematically exact Gram-Schmidt orthogonalized tangent calculation."""
        # Create a UV-mapped cylinder or icosphere
        mesh = trimesh.creation.cylinder(radius=1.0, height=2.0, sections=32)
        # Assign cylindrical UVs
        bounds = mesh.bounds
        diff = bounds[1] - bounds[0]
        uvs = (mesh.vertices[:, :2] - bounds[0, :2]) / diff[:2]
        mesh.visual = trimesh.visual.TextureVisuals(uv=uvs)

        tangents_4d = pbr_material_system.compute_tangents(mesh)

        # Check dimensions: N x 4 (Tx, Ty, Tz, Handedness)
        self.assertEqual(tangents_4d.shape, (len(mesh.vertices), 4))

        # Check tangent vectors are orthogonal to vertex normals: |T · N| ≈ 0
        tangents_3d = tangents_4d[:, :3]
        normals = mesh.vertex_normals
        dot_products = np.abs(np.sum(tangents_3d * normals, axis=1))
        max_ortho_error = np.max(dot_products)
        self.assertLess(max_ortho_error, 1e-4, f"Tangents not orthogonal to normals (max dot={max_ortho_error})")

        # Check tangents are unit length
        lengths = np.linalg.norm(tangents_3d, axis=1)
        self.assertTrue(np.allclose(lengths, 1.0, atol=1e-3), "Tangent vectors are not unit length")

        # Check handedness w is +1 or -1
        handedness = tangents_4d[:, 3]
        self.assertTrue(np.all(np.isin(handedness, [1.0, -1.0])), "Handedness must be ±1.0")

        print(f"[PASS] Feature 4: Gram-Schmidt Tangent calculation verified (Orthogonal dot error < {max_ortho_error:.6f})")

    def test_04_gltf_schema_validation(self):
        """Feature 8: Verify glTF 2.0 schema compatibility validation and error detection."""
        # Valid parameters
        valid_params = pbr_material_system.PRESETS["rusted_sword"]
        res = pbr_material_system.validate_gltf_compatibility(valid_params)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["gltf_compliance_score"], 100.0)
        self.assertEqual(len(res["errors"]), 0)

        # Invalid metallic (> 1.0)
        invalid_params = dict(valid_params)
        invalid_params["metallic_factor"] = 1.5
        res_invalid = pbr_material_system.validate_gltf_compatibility(invalid_params)
        self.assertFalse(res_invalid["is_valid"])
        self.assertTrue(any("metallicFactor" in err for err in res_invalid["errors"]))

        # Invalid alphaMode
        invalid_params_alpha = dict(valid_params)
        invalid_params_alpha["alpha_mode"] = "TRANSPARENT_BAD"
        res_alpha = pbr_material_system.validate_gltf_compatibility(invalid_params_alpha)
        self.assertFalse(res_alpha["is_valid"])
        self.assertTrue(any("alphaMode" in err for err in res_alpha["errors"]))

        print("[PASS] Feature 8: glTF 2.0 Material Validator accurately rejects non-compliant values")

    def test_05_rusted_sword_pbr_evaluation(self):
        """Specification Example 1: Verify Rusted Sword PBR properties."""
        prompt = "A rusted medieval broadsword with weathered steel"
        params = pbr_material_system.generate_material_parameters({"raw_prompt": prompt})

        # Must have high metallic factor (conductor steel base)
        self.assertGreaterEqual(params["metallic_factor"], 0.70)
        # Must have moderate-to-high roughness (rust microfacets)
        self.assertGreaterEqual(params["roughness_factor"], 0.40)
        # Must have pronounced normal scale for pitted metal
        self.assertGreaterEqual(params["normal_scale"], 1.2)
        # Must be classified as oxidized metal
        self.assertEqual(params["material_class"], MaterialClass.OXIDIZED_METAL)

        print(f"[PASS] Example 1: Rusted Sword verified (Metallic={params['metallic_factor']}, Roughness={params['roughness_factor']}, NormalScale={params['normal_scale']})")

    def test_06_glowing_sapphire_pbr_evaluation(self):
        """Specification Example 2: Verify Glowing Sapphire PBR properties."""
        prompt = "A radiant glowing blue sapphire crystal gem in the hilt"
        params = pbr_material_system.generate_material_parameters({"raw_prompt": prompt})

        # Base color must be dominated by blue channel: B > R and B > G
        base_color = params["base_color_factor"]
        self.assertGreater(base_color[2], base_color[0], "Sapphire blue channel must exceed red")
        self.assertGreater(base_color[2], base_color[1], "Sapphire blue channel must exceed green")

        # Gemstone must be smooth (low roughness)
        self.assertLessEqual(params["roughness_factor"], 0.15)
        # Gemstone dielectric base (metallic = 0.0)
        self.assertEqual(params["metallic_factor"], 0.0)
        # Emissive must be active
        self.assertGreater(params["emissive_intensity"], 2.0)
        emissive_color = params["emissive_factor"]
        self.assertGreater(emissive_color[2], emissive_color[0], "Emissive color must be blue/cyan")
        # Alpha mode should be BLEND for crystal translucency
        self.assertEqual(params["alpha_mode"], "BLEND")

        print(f"[PASS] Example 2: Glowing Sapphire verified (Blue Albedo={base_color[:3]}, Roughness={params['roughness_factor']}, EmissiveIntensity={params['emissive_intensity']}x)")

    def test_07_material_preservation_across_decimation(self):
        """Requirement: Verify material assignments and UVs are preserved across mesh decimation."""
        # Create a detailed sphere with 1280 faces
        sphere = trimesh.creation.icosphere(subdivisions=3, radius=1.0)
        initial_faces = len(sphere.faces)
        self.assertGreater(initial_faces, 1000)

        # Assign UVs and PBR Material
        bounds = sphere.bounds
        diff = bounds[1] - bounds[0]
        uvs = (sphere.vertices[:, :2] - bounds[0, :2]) / diff[:2]
        pbr_mat = trimesh.visual.material.PBRMaterial(
            name="RustedSteel",
            metallicFactor=0.85,
            roughnessFactor=0.50,
            baseColorFactor=[0.55, 0.48, 0.42, 1.0],
        )
        sphere.visual = trimesh.visual.TextureVisuals(uv=uvs, material=pbr_mat)

        # Optimize mesh down to 300 faces
        target_budget = 300
        decimated, stats = mesh_optimizer.optimize(sphere, target_polygon_budget=target_budget)

        self.assertLessEqual(len(decimated.faces), 350)
        # Check material preservation
        self.assertTrue(hasattr(decimated.visual, "material"))
        self.assertIsNotNone(decimated.visual.material)
        self.assertEqual(decimated.visual.material.name, "RustedSteel")

        # Check UV preservation
        self.assertTrue(hasattr(decimated.visual, "uv"))
        self.assertIsNotNone(decimated.visual.uv)
        self.assertEqual(len(decimated.visual.uv), len(decimated.vertices))
        self.assertTrue(np.all((decimated.visual.uv >= -0.05) & (decimated.visual.uv <= 1.05)))

        print(f"[PASS] Requirement: Material preserved across decimation ({initial_faces} -> {len(decimated.faces)} faces)")

    def test_08_pbr_glb_export_compatibility(self):
        """Feature 3 & Requirement: Export mesh with full PBR ORM maps and verify glTF 2.0 binary structure."""
        mesh = trimesh.creation.box(extents=[1.0, 1.0, 1.0])
        # Generate full texture maps for rusted metal
        textures = texture_generator_service.generate_textures({"material_type": "rusted_metal"}, resolution=512)
        baked = texture_baker.bake_textures_to_mesh(mesh, textures, resolution=512)

        pbr_params = pbr_material_system.PRESETS["rusted_sword"]
        out_glb = os.path.join(TEST_OUTPUT_DIR, "pbr_rusted_box.glb")

        export_stats = glb_exporter.export(
            mesh=baked["mesh"],
            output_path=out_glb,
            texture_paths=baked["texture_paths"],
            material_params=pbr_params,
        )

        self.assertTrue(os.path.exists(out_glb))
        self.assertGreater(os.path.getsize(out_glb), 5000)
        self.assertTrue(export_stats["valid"])

        # Inspect GLB binary magic and header
        with open(out_glb, "rb") as f:
            magic = f.read(4)
            version = int.from_bytes(f.read(4), byteorder="little")
            length = int.from_bytes(f.read(4), byteorder="little")

        self.assertEqual(magic, b"glTF")
        self.assertEqual(version, 2)
        self.assertEqual(length, os.path.getsize(out_glb))

        print(f"[PASS] Feature 3: Full PBR GLB exported with ORM packing ({os.path.getsize(out_glb):,} bytes, glTF 2.0 valid)")

    def test_09_fastapi_materials_endpoints(self):
        """Requirement: Verify REST API endpoints GET /api/materials/presets and POST /api/materials/evaluate."""
        # 1. GET /api/materials/presets
        res_presets = self.client.get("/api/materials/presets")
        self.assertEqual(res_presets.status_code, 200)
        data_presets = res_presets.json()
        self.assertEqual(data_presets["count"], 6)
        self.assertIn("rusted_sword", data_presets["presets"])
        self.assertIn("glowing_sapphire", data_presets["presets"])

        # 2. POST /api/materials/evaluate
        payload = {
            "prompt": "A rusted medieval broadsword with a glowing blue sapphire in the hilt",
            "material_type": "oxidized_metal",
            "details": ["rust", "sapphire", "blue emissive glow"],
        }
        res_eval = self.client.post("/api/materials/evaluate", json=payload)
        self.assertEqual(res_eval.status_code, 200)
        data_eval = res_eval.json()

        self.assertIn("classification", data_eval)
        self.assertIn("gltf_pbr_parameters", data_eval)
        self.assertIn("gltf_validation", data_eval)

        params = data_eval["gltf_pbr_parameters"]
        self.assertIn(params["material_class"], [MaterialClass.OXIDIZED_METAL, MaterialClass.EMISSIVE_GEMSTONE])
        self.assertTrue(data_eval["gltf_validation"]["is_valid"])

        print("[PASS] Requirement: FastAPI Endpoints /api/materials/presets & /api/materials/evaluate verified (HTTP 200)")

    def test_10_dielectric_vs_conductor_fresnel(self):
        """Feature 5 & 6: Verify Cook-Torrance physical distinction between Conductors and Dielectrics."""
        conductor = pbr_material_system.generate_material_parameters({"raw_prompt": "A polished pure gold ingot"})
        dielectric = pbr_material_system.generate_material_parameters({"raw_prompt": "A carved oak wood plank"})

        # Conductor: metallic = 1.0, F0 derived from tinted albedo
        self.assertEqual(conductor["metallic_factor"], 1.0)
        self.assertAlmostEqual(conductor["fresnel_f0"], 1.0)

        # Dielectric: metallic = 0.0, F0 = 0.04 (standard glass/plastic/wood index of refraction ~1.5)
        self.assertEqual(dielectric["metallic_factor"], 0.0)
        self.assertAlmostEqual(dielectric["fresnel_f0"], 0.04)

        print(f"[PASS] Feature 5 & 6: Physical Cook-Torrance F0 verified (Conductor F0={conductor['fresnel_f0']}, Dielectric F0={dielectric['fresnel_f0']})")

if __name__ == "__main__":
    unittest.main()
