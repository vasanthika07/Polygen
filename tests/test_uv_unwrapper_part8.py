import os
import sys
import unittest
import trimesh
import numpy as np

# Ensure backend and root are in python path
sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

from app.config import settings
from processing.uv_unwrapper import uv_unwrapper
from processing.uv_overlap_detector import uv_quality_auditor
from processing.uv_visualizer import uv_visualizer
from processing.blender_evaluator import blender_evaluator

TEST_OUTPUT_DIR = os.path.abspath("tests/output_part8")
PROCESSED_MESH_DIR = os.path.abspath("storage/processed_meshes")

class TestUVUnwrapperPart8(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
        os.makedirs(settings.STORAGE_UNWRAPPED_DIR, exist_ok=True)
        os.makedirs(settings.STORAGE_THUMBNAILS_DIR, exist_ok=True)

    def test_01_technology_evaluation_and_blender_bridge(self):
        """Verify technology evaluation matrix and standalone Blender verification script generation."""
        comp = blender_evaluator.get_technology_comparison()
        self.assertIn("technologies_evaluated", comp)
        self.assertIn("selection_verdict", comp)
        tech_names = [t["name"] for t in comp["technologies_evaluated"]]
        self.assertTrue(any("xatlas" in t for t in tech_names))
        self.assertTrue(any("Blender" in t for t in tech_names))

        # Verify standalone script generation
        script_path = blender_evaluator.ensure_blender_script()
        self.assertTrue(os.path.exists(script_path))
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("import bpy", content)
        self.assertIn("bmesh", content)
        self.assertIn("uv_layers", content)
        print(f"\n[PASS] Technology Evaluation & Standalone Blender Script: {script_path}")

    def test_02_simple_model_cube_unwrapping(self):
        """Verify UV unwrapping on canonical cube mesh."""
        box = trimesh.creation.box()
        out_mesh = os.path.join(TEST_OUTPUT_DIR, "cube_unwrapped.obj")
        out_preview = os.path.join(TEST_OUTPUT_DIR, "cube_uv_layout.png")

        unwrapped, report = uv_unwrapper.unwrap(
            box,
            output_path=out_mesh,
            preview_path=out_preview,
            resolution=1024,
            padding=4,
        )

        # 1. Output files exist
        self.assertTrue(os.path.exists(out_mesh))
        self.assertTrue(os.path.exists(out_preview))

        # 2. Charts and topology
        self.assertEqual(report["chart_count"], 6)  # 6 cube faces
        self.assertEqual(report["faces"], 12)
        self.assertTrue(report["is_valid_coordinates"])
        self.assertTrue(report["normalized_unit_space"])

        # 3. Quality & Overlaps
        self.assertFalse(report["has_overlap"])
        self.assertEqual(report["overlap_pairs_count"], 0)
        self.assertEqual(report["overlap_ratio"], 0.0)
        self.assertEqual(report["inverted_faces_count"], 0)

        # 4. OBJ format contains vt coordinates
        with open(out_mesh, "r") as f:
            obj_text = f.read()
        self.assertIn("vt ", obj_text)
        print(f"[PASS] Cube Unwrapped: 6 charts, 0 overlaps, Preview: {out_preview}")

    def test_03_simple_model_cylinder_and_sphere(self):
        """Verify UV unwrapping on curved canonical shapes (cylinder & sphere)."""
        cylinder = trimesh.creation.cylinder(radius=1.0, height=2.0, sections=16)
        out_cyl = os.path.join(TEST_OUTPUT_DIR, "cylinder_unwrapped.obj")
        out_preview = os.path.join(TEST_OUTPUT_DIR, "cylinder_uv_layout.png")

        unwrapped_cyl, rep_cyl = uv_unwrapper.unwrap(
            cylinder,
            output_path=out_cyl,
            preview_path=out_preview,
            resolution=1024,
        )

        self.assertTrue(rep_cyl["is_valid_coordinates"])
        self.assertEqual(rep_cyl["overlap_pairs_count"], 0)
        self.assertGreaterEqual(rep_cyl["chart_count"], 2)  # Caps + body

        sphere = trimesh.creation.icosphere(subdivisions=2)
        unwrapped_sph, rep_sph = uv_unwrapper.unwrap(sphere, resolution=1024)
        self.assertTrue(rep_sph["is_valid_coordinates"])
        self.assertEqual(rep_sph["overlap_pairs_count"], 0)
        print(f"[PASS] Cylinder ({rep_cyl['chart_count']} charts) & Sphere ({rep_sph['chart_count']} charts) 0 overlaps")

    def test_04_resolution_and_texel_padding_scaling(self):
        """Verify resolution scaling and adaptive gutter padding (512, 1024, 2048, 4096)."""
        res_512, pad_512 = uv_unwrapper.configure_resolution(512)
        self.assertEqual(res_512, 512)
        self.assertEqual(pad_512, 2)

        res_1024, pad_1024 = uv_unwrapper.configure_resolution(1024)
        self.assertEqual(res_1024, 1024)
        self.assertEqual(pad_1024, 4)

        res_2048, pad_2048 = uv_unwrapper.configure_resolution(2048)
        self.assertEqual(res_2048, 2048)
        self.assertEqual(pad_2048, 8)

        res_4096, pad_4096 = uv_unwrapper.configure_resolution(4096)
        self.assertEqual(res_4096, 4096)
        self.assertEqual(pad_4096, 16)

        # Non-standard snaps to nearest valid resolution
        res_custom, pad_custom = uv_unwrapper.configure_resolution(999)
        self.assertEqual(res_custom, 1024)
        print(f"[PASS] Adaptive Padding Scaled: 512->{pad_512}px, 1024->{pad_1024}px, 2048->{pad_2048}px, 4096->{pad_4096}px")

    def test_05_seam_weight_parameterization(self):
        """Verify seam weighting options in ChartOptions."""
        box = trimesh.creation.box()
        unwrapped_low, rep_low = uv_unwrapper.unwrap(
            box,
            normal_deviation_weight=0.5,
            normal_seam_weight=1.0,
            visualize=False,
        )
        unwrapped_high, rep_high = uv_unwrapper.unwrap(
            box,
            normal_deviation_weight=4.0,
            normal_seam_weight=8.0,
            visualize=False,
        )
        self.assertTrue(rep_low["is_valid_coordinates"])
        self.assertTrue(rep_high["is_valid_coordinates"])
        print(f"[PASS] Seam Weight Customization Verified")

    def test_06_overlap_detector_on_damaged_uvs(self):
        """Verify UV quality auditor on intentionally damaged UV coordinates."""
        # 1. Coordinate validity checks
        nan_uvs = np.array([[0.1, 0.2], [np.nan, 0.5], [0.3, 0.4]])
        audit_nan = uv_quality_auditor.validate_coordinates(nan_uvs)
        self.assertFalse(audit_nan["is_valid"])
        self.assertTrue(audit_nan["has_nan"])

        oob_uvs = np.array([[0.1, 0.2], [1.5, 0.5], [-0.2, 0.4]])
        audit_oob = uv_quality_auditor.validate_coordinates(oob_uvs)
        self.assertFalse(audit_oob["is_valid"])
        self.assertEqual(audit_oob["out_of_bounds_count"], 2)

        # 2. Inverted face check (1 CCW face and 1 flipped CW face)
        faces_uvs = np.array([
            [0.0, 0.0], [1.0, 0.0], [0.0, 1.0],  # Tri 0 (CCW -> positive signed area)
            [0.5, 0.0], [0.5, 1.0], [1.0, 0.0],  # Tri 1 (CW -> flipped negative signed area)
        ])
        indices = np.array([[0, 1, 2], [3, 4, 5]])
        audit_inv = uv_quality_auditor.detect_overlaps(indices, faces_uvs)
        self.assertEqual(audit_inv["inverted_faces_count"], 1)

        # 3. Intentional triangle overlap detection
        # Create 2 triangles overlapping in area
        tri_uvs = np.array([
            [0.1, 0.1], [0.5, 0.1], [0.1, 0.5],  # Tri 0
            [0.2, 0.2], [0.6, 0.2], [0.2, 0.6],  # Tri 1 (overlaps Tri 0)
        ])
        tri_faces = np.array([[0, 1, 2], [3, 4, 5]])
        audit_overlap = uv_quality_auditor.detect_overlaps(tri_faces, tri_uvs)
        self.assertTrue(audit_overlap["has_overlap"])
        self.assertGreater(audit_overlap["overlap_pairs_count"], 0)
        self.assertGreater(audit_overlap["total_overlap_area"], 0.0)
        print(f"[PASS] Quality Auditor: Caught NaN, Out-Of-Bounds, Inversion, and Overlaps")

    def test_07_blender_compatibility_and_verification(self):
        """Verify Blender compatibility audit and format compliance."""
        box = trimesh.creation.box()
        out_mesh = os.path.join(TEST_OUTPUT_DIR, "blender_test.obj")
        unwrapped, rep = uv_unwrapper.unwrap(box, output_path=out_mesh)

        blender_eval = blender_evaluator.verify_mesh_uv(out_mesh)
        self.assertTrue(blender_eval["blender_evaluated"])
        self.assertTrue(blender_eval["has_active_uv_layer"])
        self.assertTrue(blender_eval["is_within_0_1_bounds"])
        self.assertTrue(blender_eval["blender_import_ready"])
        self.assertEqual(blender_eval["overlapping_pairs"], 0)
        print(f"[PASS] Blender Compatibility Audit: {blender_eval['status']}")

    def _verify_part6_asset_unwrap(self, filename: str, slug: str):
        """Helper to verify complete UV unwrap on real Part 6 assets."""
        mesh_path = os.path.join(PROCESSED_MESH_DIR, filename)
        if not os.path.exists(mesh_path):
            self.skipTest(f"Asset {filename} not found at {mesh_path}")

        out_mesh = os.path.join(settings.STORAGE_UNWRAPPED_DIR, f"{slug}_unwrapped.obj")
        out_preview = os.path.join(settings.STORAGE_THUMBNAILS_DIR, f"{slug}_uv_layout.png")

        unwrapped_mesh, rep = uv_unwrapper.unwrap(
            mesh_path,
            output_path=out_mesh,
            preview_path=out_preview,
            resolution=1024,
            padding=4,
        )

        # 1. Output file persistence
        self.assertTrue(os.path.exists(out_mesh))
        self.assertTrue(os.path.exists(out_preview))

        # 2. Coordinates validity & unit bounds
        self.assertTrue(rep["is_valid_coordinates"])
        self.assertTrue(rep["normalized_unit_space"])
        self.assertGreaterEqual(rep["uv_min"][0], 0.0)
        self.assertLessEqual(rep["uv_max"][0], 1.0)
        self.assertGreaterEqual(rep["uv_min"][1], 0.0)
        self.assertLessEqual(rep["uv_max"][1], 1.0)

        # 3. Zero Overlaps
        self.assertFalse(rep["has_overlap"])
        self.assertEqual(rep["overlap_pairs_count"], 0)
        self.assertEqual(rep["overlap_ratio"], 0.0)

        # 4. Islands and utilization
        self.assertGreater(rep["chart_count"], 0)
        self.assertGreater(rep["atlas_utilization"], 0.0)
        self.assertGreater(len(rep["islands"]), 0)

        # 5. Reload and verify vt coordinates
        reloaded = trimesh.load(out_mesh, process=False)
        self.assertEqual(len(reloaded.faces), rep["faces"])
        self.assertTrue(hasattr(reloaded.visual, "uv"))

        print(
            f"[PASS] Unwrapped '{slug}': {rep['chart_count']} charts, "
            f"Util: {rep['atlas_utilization_percent']}%, Overlaps: {rep['overlap_pairs_count']}, "
            f"Time: {rep['processing_duration_ms']} ms -> {out_preview}"
        )
        return unwrapped_mesh, rep

    def test_08_complex_model_wooden_chair(self):
        """Test UV unwrapping on generated wooden chair asset."""
        self._verify_part6_asset_unwrap("wooden_chair_cleaned.obj", "wooden_chair")

    def test_09_complex_model_medieval_sword(self):
        """Test UV unwrapping on generated medieval sword asset."""
        self._verify_part6_asset_unwrap("medieval_sword_cleaned.obj", "medieval_sword")

    def test_10_complex_model_fantasy_treasure_chest(self):
        """Test UV unwrapping on generated fantasy treasure chest asset."""
        self._verify_part6_asset_unwrap("fantasy_treasure_chest_cleaned.obj", "fantasy_treasure_chest")

    def test_11_complex_model_metallic_robot(self):
        """Test UV unwrapping on generated metallic robot asset."""
        self._verify_part6_asset_unwrap("metallic_robot_cleaned.obj", "metallic_robot")

    def test_12_complex_model_stone_sculpture(self):
        """Test UV unwrapping on generated stone sculpture asset."""
        self._verify_part6_asset_unwrap("stone_sculpture_cleaned.obj", "stone_sculpture")

    def test_13_glb_export_with_texcoord0(self):
        """Verify GLB export with TEXCOORD_0 attribute."""
        box = trimesh.creation.box()
        out_glb = os.path.join(TEST_OUTPUT_DIR, "box_unwrapped.glb")
        unwrapped, rep = uv_unwrapper.unwrap(box, output_path=out_glb, output_format="glb")

        self.assertTrue(os.path.exists(out_glb))
        reloaded = trimesh.load(out_glb, file_type="glb")
        geom = list(reloaded.geometry.values())[0] if isinstance(reloaded, trimesh.Scene) else reloaded
        self.assertTrue(hasattr(geom.visual, "uv"))
        self.assertIsNotNone(geom.visual.uv)
        self.assertEqual(len(geom.visual.uv), rep["unwrapped_vertices"])
        print(f"[PASS] GLB Export Verified with TEXCOORD_0: {out_glb}")

    def test_14_geometry_preservation_check(self):
        """Verify that UV unwrapping strictly preserves 3D surface geometry without distortion."""
        box = trimesh.creation.box(extents=[1.5, 2.5, 3.5])
        orig_bounds = box.bounds.copy()
        orig_volume = box.volume

        unwrapped, rep = uv_unwrapper.unwrap(box, visualize=False)
        new_bounds = unwrapped.bounds
        new_volume = unwrapped.volume

        np.testing.assert_allclose(orig_bounds, new_bounds, atol=1e-5)
        self.assertAlmostEqual(orig_volume, new_volume, places=4)
        print(f"[PASS] Geometry Preservation: 3D Bounds & Volume Preserved Exactly")

if __name__ == "__main__":
    unittest.main(verbosity=2)
