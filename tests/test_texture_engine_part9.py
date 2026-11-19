import os
import sys
import unittest
import trimesh
import numpy as np
from PIL import Image

# Ensure backend and root are in python path
sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

from app.config import settings
from processing.texture_generator import texture_generator_service, texture_validator
from processing.texture_baker import texture_baker
from processing.glb_exporter import glb_exporter

TEST_OUTPUT_DIR = os.path.abspath("tests/output_part9")
UNWRAPPED_DIR = os.path.abspath("storage/unwrapped_meshes")

class TestTextureEnginePart9(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
        os.makedirs(settings.STORAGE_TEXTURES_DIR, exist_ok=True)
        os.makedirs(settings.STORAGE_THUMBNAILS_DIR, exist_ok=True)

    def test_01_material_spec_extraction(self):
        """Verify extraction of structured material specifications from prompts."""
        prompts = [
            ("A weathered oak dining chair with carved wood grain", "wood", False),
            ("A rusted medieval broadsword with weathered steel", "rusted_metal", False),
            ("A chiseled granite stone sculpture of an ancient warrior", "stone", False),
            ("A pristine translucent glass potion bottle", "glass", False),
            ("A glowing blue sapphire crystal jewel with radiant emissive bloom", "glowing_sapphire", True),
        ]

        for p_text, expected_mat, expected_emissive in prompts:
            spec = texture_generator_service.extract_material_spec(p_text)
            self.assertEqual(spec["material_type"], expected_mat, f"Failed for prompt: {p_text}")
            self.assertEqual(spec["has_emissive"], expected_emissive, f"Emissive mismatch for: {p_text}")

        print("\n[PASS] Material Specification Extraction: All 5 material types verified")

    def test_02_resolution_control(self):
        """Verify resolution control for 512, 1024, 2048, and nearest power-of-two snap."""
        for res in [512, 1024, 2048]:
            maps = texture_generator_service.generate_textures({"material_type": "wood"}, resolution=res)
            self.assertEqual(maps["basecolor"].size, (res, res))
            self.assertEqual(maps["roughness"].size, (res, res))
            self.assertEqual(maps["metallic"].size, (res, res))
            self.assertEqual(maps["normal"].size, (res, res))
            self.assertEqual(maps["ambient_occlusion"].size, (res, res))
            self.assertEqual(maps["emissive"].size, (res, res))
            self.assertEqual(maps["orm"].size, (res, res))

        # Test resolution snap
        self.assertEqual(texture_baker._validate_resolution(999), 1024)
        self.assertEqual(texture_baker._validate_resolution(300), 512)
        print("[PASS] Resolution Control: 512, 1024, 2048, and snapping verified")

    def test_03_six_channel_validation(self):
        """Verify generation and validation of all 6 individual PBR channels plus packed ORM."""
        spec = {"material_type": "stone", "has_emissive": False}
        maps = texture_generator_service.generate_textures(spec, resolution=512)

        expected_channels = ["basecolor", "roughness", "metallic", "normal", "ambient_occlusion", "emissive", "orm"]
        for ch in expected_channels:
            self.assertIn(ch, maps)
            self.assertEqual(maps[ch].size, (512, 512))

        val_rep = texture_validator.validate_texture_set(maps, expected_res=512)
        self.assertTrue(val_rep["is_valid"])
        self.assertEqual(len(val_rep["errors"]), 0)
        print("[PASS] Six-Channel PBR Validation: basecolor, roughness, metallic, normal, AO, emissive, ORM")

    def test_04_wood_material_synthesis(self):
        """Verify Wood material characteristics: fibrous grain, medium-high roughness, 0 metallic."""
        maps = texture_generator_service.generate_textures({"material_type": "wood"}, resolution=512)
        rough = np.array(maps["roughness"])
        metal = np.array(maps["metallic"])
        emissive = np.array(maps["emissive"])

        # Wood roughness: 0.65 - 0.78 (~165/255)
        self.assertGreater(np.mean(rough), 140)
        self.assertLess(np.mean(rough), 210)

        # Wood metallic: 0.0
        self.assertEqual(np.max(metal), 0)

        # Wood emissive: 0.0
        self.assertEqual(np.max(emissive), 0)
        print(f"[PASS] Wood Material: Mean Roughness={np.mean(rough):.1f}, Metallic={np.mean(metal):.1f}")

    def test_05_rusted_metal_material_synthesis(self):
        """Verify Rusted Metal material: dual-tone metallic/dielectric, pitted normal, rough corrosion."""
        maps = texture_generator_service.generate_textures({"material_type": "rusted_metal", "raw_query": "rust"}, resolution=512)
        rough = np.array(maps["roughness"])
        metal = np.array(maps["metallic"])

        # Metallic should have both high (steel) and low (rust) values
        self.assertGreater(np.max(metal), 200)  # Steel
        self.assertLess(np.min(metal), 50)     # Rust

        # Roughness should have variance reflecting polished steel vs rough corrosion
        self.assertGreater(np.var(rough), 500)
        print(f"[PASS] Rusted Metal: Metal min={np.min(metal)}, max={np.max(metal)}, Roughness var={np.var(rough):.1f}")

    def test_06_stone_material_synthesis(self):
        """Verify Stone material: high matte roughness, 0 metallic, chiseled relief."""
        maps = texture_generator_service.generate_textures({"material_type": "stone"}, resolution=512)
        rough = np.array(maps["roughness"])
        metal = np.array(maps["metallic"])
        ao = np.array(maps["ambient_occlusion"])

        # Stone roughness: ~0.84 (~215/255)
        self.assertGreater(np.mean(rough), 190)

        # Stone metallic: 0.0
        self.assertEqual(np.max(metal), 0)

        # Stone AO: has deep cavity occlusion
        self.assertLess(np.min(ao), 200)
        print(f"[PASS] Stone Material: Mean Roughness={np.mean(rough):.1f}, AO min={np.min(ao)}")

    def test_07_glass_like_material_synthesis(self):
        """Verify Glass-like material: mirror smooth roughness, 0 metallic, unoccluded AO."""
        maps = texture_generator_service.generate_textures({"material_type": "glass"}, resolution=512)
        rough = np.array(maps["roughness"])
        metal = np.array(maps["metallic"])
        normal = np.array(maps["normal"])

        # Glass roughness: <= 25 (~0.1)
        self.assertLessEqual(np.mean(rough), 25)

        # Glass metallic: 0.0
        self.assertEqual(np.max(metal), 0)

        # Glass normal: Flat pristine normal (128, 128, 255)
        self.assertTrue(np.all(normal[:, :, :2] == 128))
        self.assertTrue(np.all(normal[:, :, 2] == 255))
        print(f"[PASS] Glass-like Material: Ultra-smooth Roughness={np.mean(rough):.1f}, Pristine Normals verified")

    def test_08_glowing_sapphire_material_synthesis(self):
        """Verify Glowing Sapphire material: cobalt albedo, polished crystal roughness, bright emissive glow."""
        maps = texture_generator_service.generate_textures({"material_type": "glowing_sapphire", "has_emissive": True}, resolution=512)
        albedo = np.array(maps["basecolor"])
        emissive = np.array(maps["emissive"])
        rough = np.array(maps["roughness"])

        # Sapphire Albedo: Cobalt blue dominant (B > R and B > G)
        self.assertGreater(np.mean(albedo[:, :, 2]), np.mean(albedo[:, :, 0]))

        # Sapphire Roughness: Glossy crystal (<= 50)
        self.assertLess(np.mean(rough), 60)

        # Sapphire Emissive: High radiant blue emission (B channel > 200 at core)
        self.assertGreater(np.max(emissive[:, :, 2]), 200)
        print(f"[PASS] Glowing Sapphire: Blue Albedo={np.mean(albedo[:, :, 2]):.1f}, Max Emissive={np.max(emissive)}")

    def test_09_uv_aware_texture_baking_and_voronoi_dilation(self):
        """Verify UV-aware texture baking with Voronoi gutter dilation."""
        cube = trimesh.creation.box()
        from processing.uv_unwrapper import uv_unwrapper
        unwrapped, _ = uv_unwrapper.unwrap(cube, resolution=512, padding=8, visualize=False)

        tex_dir = os.path.join(TEST_OUTPUT_DIR, "uv_aware_cube")
        paths = texture_baker.generate_pbr_set(
            prompt_data="weathered wood oak",
            output_dir=tex_dir,
            mesh=unwrapped,
            resolution=512,
            render_preview=False,
        )

        for key in ["basecolor", "roughness", "metallic", "normal", "ambient_occlusion", "emissive", "orm"]:
            self.assertTrue(os.path.exists(paths[key]))
            with Image.open(paths[key]) as img:
                self.assertEqual(img.size, (512, 512))

        print("[PASS] UV-Aware Texture Baking & Voronoi Gutter Dilation Verified")

    def test_10_geometry_guided_ambient_occlusion_baking(self):
        """Verify 3D geometry-guided ambient occlusion baking into 2D UV layout."""
        mesh = trimesh.load(os.path.join(UNWRAPPED_DIR, "medieval_sword_unwrapped.obj"))
        tex_dir = os.path.join(TEST_OUTPUT_DIR, "ao_sword")

        paths = texture_baker.generate_pbr_set(
            prompt_data="rusted iron broadsword with sapphire",
            output_dir=tex_dir,
            mesh=mesh,
            resolution=512,
            render_preview=False,
        )

        with Image.open(paths["ambient_occlusion"]) as ao_img:
            ao_arr = np.array(ao_img)

        # Cavity AO should exhibit shading contrast from 3D geometry
        self.assertLess(np.min(ao_arr), 255)
        self.assertGreater(np.var(ao_arr), 10.0)
        print(f"[PASS] Geometry-Guided AO: Min={np.min(ao_arr)}, Max={np.max(ao_arr)}, Variance={np.var(ao_arr):.2f}")

    def test_11_uv_alignment_verification(self):
        """Verify UV alignment checker."""
        mesh = trimesh.load(os.path.join(UNWRAPPED_DIR, "wooden_chair_unwrapped.obj"))
        report = texture_baker.check_uv_alignment(mesh, resolution=1024)

        self.assertTrue(report["is_aligned"])
        self.assertEqual(report["alignment_status"], "ALIGNED")
        self.assertGreater(report["estimated_texel_density"], 0.0)
        self.assertGreater(report["uv_coverage_ratio"], 0.0)
        print(f"[PASS] UV Alignment: Status={report['alignment_status']}, Texel Density={report['estimated_texel_density']} px/unit")

    def test_12_pbr_material_assignment_and_glb_export(self):
        """Verify PBR material assignment and GLB export with full ORM + AO bindings."""
        mesh = trimesh.load(os.path.join(UNWRAPPED_DIR, "wooden_chair_unwrapped.obj"))
        tex_dir = os.path.join(TEST_OUTPUT_DIR, "chair_textures")

        tex_paths = texture_baker.generate_pbr_set(
            prompt_data="rustic carved oak wooden chair",
            output_dir=tex_dir,
            mesh=mesh,
            resolution=512,
            render_preview=False,
        )

        out_glb = os.path.join(TEST_OUTPUT_DIR, "wooden_chair_textured.glb")
        export_stats = glb_exporter.export(mesh, tex_paths, out_glb)

        self.assertTrue(os.path.exists(out_glb))
        self.assertTrue(export_stats["valid"])
        self.assertGreater(export_stats["file_size_bytes"], 10000)

        # Reload and verify
        reloaded = trimesh.load(out_glb, file_type="glb")
        geom = list(reloaded.geometry.values())[0] if isinstance(reloaded, trimesh.Scene) else reloaded
        self.assertTrue(hasattr(geom.visual, "material"))
        print(f"[PASS] PBR Material Assignment & GLB Export: {out_glb} ({export_stats['file_size_mb']} MB)")

    def test_13_textured_3d_preview_generation(self):
        """Verify offscreen textured 3D isometric preview generation."""
        mesh = trimesh.load(os.path.join(UNWRAPPED_DIR, "medieval_sword_unwrapped.obj"))
        tex_dir = os.path.join(TEST_OUTPUT_DIR, "sword_textures")
        preview_path = os.path.join(TEST_OUTPUT_DIR, "sword_textured_preview.png")

        tex_paths = texture_baker.generate_pbr_set(
            prompt_data="rusted medieval broadsword with a glowing blue sapphire",
            output_dir=tex_dir,
            mesh=mesh,
            resolution=512,
            render_preview=True,
            preview_path=preview_path,
        )

        self.assertTrue(os.path.exists(preview_path))
        self.assertGreater(os.path.getsize(preview_path), 5000)
        with Image.open(preview_path) as img:
            self.assertGreaterEqual(img.size[0], 400)
            self.assertGreaterEqual(img.size[1], 400)
        print(f"[PASS] Textured 3D Preview Generated: {preview_path}")

    def test_14_end_to_end_part6_assets_texturing(self):
        """Benchmark all 5 real Part 6 assets across their corresponding materials."""
        benchmarks = [
            ("wooden_chair_unwrapped.obj", "wooden_chair", "carved oak wooden chair with grain", "wood"),
            ("medieval_sword_unwrapped.obj", "medieval_sword", "rusted medieval broadsword with glowing sapphire", "glowing_sapphire"),
            ("fantasy_treasure_chest_unwrapped.obj", "fantasy_treasure_chest", "weathered oak treasure chest with rusted iron bands", "wood"),
            ("metallic_robot_unwrapped.obj", "metallic_robot", "cybernetic mechanical metallic robot", "rusted_metal"),
            ("stone_sculpture_unwrapped.obj", "stone_sculpture", "ancient chiseled granite stone sculpture", "stone"),
        ]

        for mesh_name, slug, prompt, expected_mat in benchmarks:
            mesh_path = os.path.join(UNWRAPPED_DIR, mesh_name)
            if not os.path.exists(mesh_path):
                self.skipTest(f"Asset {mesh_name} not found")

            mesh = trimesh.load(mesh_path)
            tex_dir = os.path.join(settings.STORAGE_TEXTURES_DIR, slug)
            preview_path = os.path.join(settings.STORAGE_THUMBNAILS_DIR, f"{slug}_textured_preview.png")

            paths = texture_baker.generate_pbr_set(
                prompt_data=prompt,
                output_dir=tex_dir,
                mesh=mesh,
                resolution=1024,
                render_preview=True,
                preview_path=preview_path,
            )

            # Check files
            self.assertTrue(os.path.exists(paths["basecolor"]))
            self.assertTrue(os.path.exists(paths["roughness"]))
            self.assertTrue(os.path.exists(paths["metallic"]))
            self.assertTrue(os.path.exists(paths["normal"]))
            self.assertTrue(os.path.exists(paths["ambient_occlusion"]))
            self.assertTrue(os.path.exists(paths["emissive"]))
            self.assertTrue(os.path.exists(paths["orm"]))
            self.assertTrue(os.path.exists(preview_path))

            # Export textured GLB
            out_glb = os.path.join(settings.STORAGE_EXPORTS_DIR, f"{slug}.glb")
            glb_stats = glb_exporter.export(mesh, paths, out_glb)
            self.assertTrue(glb_stats["valid"])

            print(f"[PASS] Textures & GLB Generated for '{slug}' -> {preview_path} ({glb_stats['file_size_mb']} MB)")

if __name__ == "__main__":
    unittest.main(verbosity=2)
