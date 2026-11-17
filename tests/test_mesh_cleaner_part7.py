import os
import sys
import unittest
import trimesh
import numpy as np

# Ensure backend and root are in python path
sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

from app.config import settings
from processing.mesh_cleaner import mesh_cleaner
from processing.mesh_statistics import mesh_statistics_extractor
from processing.external_adapters import external_adapters

TEST_OUTPUT_DIR = os.path.abspath("tests/output_part7")
PART6_DIR = os.path.abspath("tests/output_part6")

class TestMeshCleanerPart7(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

    def test_01_external_adapters_status(self):
        """Verify external adapter detection and status reporting."""
        status = external_adapters.get_adapter_status()
        self.assertTrue(status["trimesh_available"])
        self.assertIn("trimesh", status["active_backends"])
        self.assertIn("open3d_available", status)
        self.assertIn("pymeshlab_available", status)
        print(f"\n[PASS] External Adapters Status: {status['active_backends']}")

    def test_02_mesh_statistics_extractor(self):
        """Verify comprehensive mesh statistics extraction on canonical geometry."""
        box = trimesh.creation.box(extents=[1.0, 2.0, 3.0])
        stats = mesh_statistics_extractor.extract(box)

        self.assertEqual(stats["vertex_count"], 8)
        self.assertEqual(stats["face_count"], 12)
        self.assertTrue(stats["is_watertight"])
        self.assertTrue(stats["is_manifold"])
        self.assertEqual(stats["non_manifold_edges_count"], 0)
        self.assertEqual(stats["connected_components"], 1)
        self.assertAlmostEqual(stats["bounding_box_volume"], 6.0, places=2)
        self.assertAlmostEqual(stats["surface_area"], 22.0, places=2)
        self.assertAlmostEqual(stats["volume"], 6.0, places=2)
        print(f"[PASS] Statistics Extractor: Area={stats['surface_area']}, Vol={stats['volume']}, Euler={stats['euler_characteristic']}")

    def test_03_damaged_mesh_duplicate_vertices(self):
        """Verify removal of coincident duplicate vertices."""
        # Create box with duplicated vertices
        box = trimesh.creation.box()
        # Append duplicate copies of vertices and duplicate faces
        dup_verts = np.vstack([box.vertices, box.vertices + 1e-8])
        dup_faces = np.vstack([box.faces, box.faces + len(box.vertices)])
        damaged = trimesh.Trimesh(vertices=dup_verts, faces=dup_faces, process=False)
        self.assertEqual(len(damaged.vertices), 16)
        self.assertEqual(len(damaged.faces), 24)

        out_path = os.path.join(TEST_OUTPUT_DIR, "repaired_duplicates.obj")
        cleaned, report = mesh_cleaner.clean(damaged, output_path=out_path)

        self.assertEqual(report["original_vertex_count"], 16)
        self.assertLess(report["processed_vertex_count"], 16)
        self.assertEqual(report["processed_vertex_count"], 8)
        self.assertTrue(os.path.exists(out_path))
        print(f"[PASS] Duplicate Vertices Repaired: {report['original_vertex_count']} -> {report['processed_vertex_count']} verts")

    def test_04_damaged_mesh_degenerate_faces(self):
        """Verify removal of degenerate zero-area and collapsed faces."""
        box = trimesh.creation.box()
        # Add collapsed face [0, 0, 1] and zero-area face [0, 1, 0]
        bad_faces = np.vstack([
            box.faces,
            [[0, 0, 1]],
            [[2, 3, 2]],
            [[1, 1, 1]],
        ])
        damaged = trimesh.Trimesh(vertices=box.vertices, faces=bad_faces, process=False)
        self.assertEqual(len(damaged.faces), 15)

        out_path = os.path.join(TEST_OUTPUT_DIR, "repaired_degenerate.obj")
        cleaned, report = mesh_cleaner.clean(damaged, output_path=out_path)

        self.assertEqual(report["processed_face_count"], 12)
        self.assertGreater(report["original_face_count"], report["processed_face_count"])
        print(f"[PASS] Degenerate Faces Removed: {report['original_face_count']} -> {report['processed_face_count']} faces")

    def test_05_damaged_mesh_winding_and_normals(self):
        """Verify winding consistency check and surface normal repair."""
        box = trimesh.creation.box()
        # Invert half of the faces (reverse triangle vertex order)
        inverted_faces = box.faces.copy()
        inverted_faces[:6] = inverted_faces[:6, ::-1]
        damaged = trimesh.Trimesh(vertices=box.vertices, faces=inverted_faces, process=False)

        out_path = os.path.join(TEST_OUTPUT_DIR, "repaired_winding.obj")
        cleaned, report = mesh_cleaner.clean(damaged, output_path=out_path)

        self.assertTrue(report["is_winding_consistent"])
        self.assertTrue(report["watertight_after"])
        print(f"[PASS] Winding & Normals Unified: Winding Consistent={report['is_winding_consistent']}")

    def test_06_damaged_mesh_nan_and_inf_vertices(self):
        """Verify removal of non-finite NaN / Inf vertices and corrupted faces."""
        box = trimesh.creation.box()
        corrupt_verts = np.vstack([box.vertices, [[np.nan, 0.0, 1.0]], [[np.inf, np.inf, 0.0]]])
        corrupt_faces = np.vstack([box.faces, [[8, 0, 1]], [[9, 2, 3]]])
        damaged = trimesh.Trimesh(vertices=corrupt_verts, faces=corrupt_faces, process=False)

        out_path = os.path.join(TEST_OUTPUT_DIR, "repaired_nan_inf.obj")
        cleaned, report = mesh_cleaner.clean(damaged, output_path=out_path)

        self.assertTrue(np.isfinite(cleaned.vertices).all())
        self.assertEqual(report["processed_vertex_count"], 8)
        self.assertEqual(report["processed_face_count"], 12)
        print(f"[PASS] NaN/Inf Stripped: Cleaned Vertices={report['processed_vertex_count']}")

    def test_07_damaged_mesh_floating_debris_filtering(self):
        """Verify connected component analysis and floating debris pruning."""
        # Create chair or main body
        main_mesh = trimesh.creation.cylinder(radius=1.0, height=2.0)
        # Add tiny detached floating triangle artifact far away
        debris_verts = np.array([
            [10.0, 10.0, 10.0],
            [10.1, 10.0, 10.0],
            [10.0, 10.1, 10.0],
        ])
        debris_faces = np.array([[0, 1, 2]])
        combined = trimesh.util.concatenate([main_mesh, trimesh.Trimesh(vertices=debris_verts, faces=debris_faces)])

        out_path = os.path.join(TEST_OUTPUT_DIR, "repaired_debris.obj")
        cleaned, report = mesh_cleaner.clean(combined, output_path=out_path, filter_debris=True)

        self.assertEqual(report["connected_components"], 1)
        # Ensure bounding box does not include the far debris at 10.0
        extents = report["bounding_box_extents"]
        self.assertLess(extents[0], 5.0)
        print(f"[PASS] Debris Pruned: Connected Components={report['connected_components']}, Bounds Extents={extents}")

    def test_08_damaged_mesh_hole_filling(self):
        """Verify watertightness analysis and boundary hole closing."""
        box = trimesh.creation.box()
        # Delete one face to create an open hole
        open_box = trimesh.Trimesh(vertices=box.vertices, faces=box.faces[1:], process=False)
        self.assertFalse(open_box.is_watertight)

        out_path = os.path.join(TEST_OUTPUT_DIR, "repaired_hole.obj")
        cleaned, report = mesh_cleaner.clean(open_box, output_path=out_path, attempt_hole_filling=True)

        self.assertFalse(report["watertight_before"])
        self.assertTrue(report["watertight_after"])
        self.assertTrue(cleaned.is_watertight)
        print(f"[PASS] Watertightness Repaired: Before={report['watertight_before']}, After={report['watertight_after']}")

    def test_09_non_manifold_detection(self):
        """Verify non-manifold edge detection."""
        # Create 3 triangles sharing a single central edge (non-manifold T-junction)
        verts = np.array([
            [0.0, 0.0, 0.0], # 0
            [0.0, 0.0, 1.0], # 1 (edge 0-1 is shared)
            [1.0, 0.0, 0.0], # 2 (face 0, 1, 2)
            [-1.0, 0.0, 0.0],# 3 (face 0, 1, 3)
            [0.0, 1.0, 0.0], # 4 (face 0, 1, 4) - 3rd face on edge 0-1!
        ])
        faces = np.array([
            [0, 1, 2],
            [0, 1, 3],
            [0, 1, 4],
        ])
        non_manifold_mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
        out_path = os.path.join(TEST_OUTPUT_DIR, "non_manifold_test.obj")
        cleaned, report = mesh_cleaner.clean(non_manifold_mesh, output_path=out_path)

        self.assertFalse(report["is_manifold"])
        self.assertGreater(report["non_manifold_edges_count"], 0)
        print(f"[PASS] Non-Manifold Detected: Non-manifold edges={report['non_manifold_edges_count']}")

    def _verify_clean_pipeline_on_part6_asset(self, filename: str, slug: str):
        """Helper to run the cleaning pipeline on genuine generated models from Part 6."""
        raw_path = os.path.join(PART6_DIR, filename)
        if not os.path.exists(raw_path):
            self.skipTest(f"Part 6 raw asset {filename} not found at {raw_path}")

        cleaned_path = os.path.join(TEST_OUTPUT_DIR, f"{slug}_cleaned.obj")
        cleaned_mesh, report = mesh_cleaner.clean(raw_path, output_path=cleaned_path)

        # 1. Output file saved separately
        self.assertTrue(os.path.exists(cleaned_path), f"Cleaned output file missing: {cleaned_path}")
        self.assertNotEqual(os.path.abspath(raw_path), os.path.abspath(cleaned_path))

        # 2. Geometry preserved and valid
        self.assertGreater(report["processed_vertex_count"], 0)
        self.assertGreater(report["processed_face_count"], 0)
        self.assertGreater(len(cleaned_mesh.vertices), 0)
        self.assertGreater(len(cleaned_mesh.faces), 0)

        # 3. Report fields verified
        self.assertIn("original_vertex_count", report)
        self.assertIn("original_face_count", report)
        self.assertIn("processed_vertex_count", report)
        self.assertIn("processed_face_count", report)
        self.assertIn("connected_components", report)
        self.assertIn("watertight_after", report)
        self.assertIn("processing_duration_ms", report)
        self.assertGreater(report["processing_duration_ms"], 0)

        # 4. Cleaned mesh reloadable
        reloaded = trimesh.load(cleaned_path)
        self.assertEqual(len(reloaded.faces), len(cleaned_mesh.faces))

        print(
            f"[PASS] Cleaned Asset '{filename}': {report['original_vertex_count']} -> {report['processed_vertex_count']} verts, "
            f"{report['original_face_count']} -> {report['processed_face_count']} faces, "
            f"Components: {report['connected_components']}, Watertight: {report['watertight_after']}, "
            f"Time: {report['processing_duration_ms']} ms"
        )
        return cleaned_mesh, report

    def test_10_clean_generated_wooden_chair(self):
        """Test mesh cleaning on generated wooden chair asset."""
        self._verify_clean_pipeline_on_part6_asset("wooden_chair_raw.obj", "wooden_chair")

    def test_11_clean_generated_medieval_sword(self):
        """Test mesh cleaning on generated medieval sword asset."""
        self._verify_clean_pipeline_on_part6_asset("medieval_sword_raw.obj", "medieval_sword")

    def test_12_clean_generated_fantasy_treasure_chest(self):
        """Test mesh cleaning on generated fantasy treasure chest asset."""
        self._verify_clean_pipeline_on_part6_asset("fantasy_treasure_chest_raw.obj", "fantasy_treasure_chest")

    def test_13_clean_generated_metallic_robot(self):
        """Test mesh cleaning on generated metallic robot asset."""
        self._verify_clean_pipeline_on_part6_asset("metallic_robot_raw.obj", "metallic_robot")

    def test_14_clean_generated_stone_sculpture(self):
        """Test mesh cleaning on generated stone sculpture asset."""
        self._verify_clean_pipeline_on_part6_asset("stone_sculpture_raw.obj", "stone_sculpture")

if __name__ == "__main__":
    unittest.main(verbosity=2)
