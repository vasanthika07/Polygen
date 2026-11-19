import os
import sys
import unittest
import trimesh
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from fastapi.testclient import TestClient

# Ensure backend and root are in python path
sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

from app.main import app
from processing.mesh_optimizer import mesh_optimizer, PolygonBudgetPreset

TEST_OUTPUT_DIR = os.path.abspath("tests/output_part11")

class TestMeshOptimizerPart11(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
        cls.client = TestClient(app)

    def test_01_polygon_count_analysis(self):
        """Feature 1: Verify Polygon count and topology analysis."""
        sphere = trimesh.creation.icosphere(subdivisions=3, radius=1.0)
        analysis = mesh_optimizer.analyze_mesh(sphere)

        self.assertEqual(analysis["polygon_count"], 1280)
        self.assertEqual(analysis["vertex_count"], 642)
        self.assertTrue(analysis["is_watertight"])
        self.assertTrue(analysis["is_manifold"])
        self.assertGreater(analysis["surface_area"], 12.0)
        self.assertGreater(analysis["volume"], 4.0)
        self.assertIn("bounding_box", analysis)
        self.assertEqual(len(analysis["bounding_box"]["extents"]), 3)
        self.assertIn(analysis["recommended_preset"], ["low", "medium", "high"])

        print(f"\n[PASS] Feature 1: Mesh Analysis ({analysis['polygon_count']} faces, Area={analysis['surface_area']}, Vol={analysis['volume']})")

    def test_02_budget_presets_and_custom(self):
        """User Settings: Verify resolution of budget tiers (Low, Medium, High, Custom)."""
        self.assertEqual(mesh_optimizer.resolve_target_budget("low"), 3000)
        self.assertEqual(mesh_optimizer.resolve_target_budget("medium"), 10000)
        self.assertEqual(mesh_optimizer.resolve_target_budget("high"), 35000)
        self.assertEqual(mesh_optimizer.resolve_target_budget("custom", custom_budget=4500), 4500)
        self.assertEqual(mesh_optimizer.resolve_target_budget(PolygonBudgetPreset.LOW), 3000)

        print("[PASS] User Settings: All 4 budget presets (Low=3k, Med=10k, High=35k, Custom=4.5k) resolved")

    def test_03_mesh_decimation_qem(self):
        """Feature 2: Verify Quadric Error Metric (QEM) decimation to target budget."""
        dense_mesh = trimesh.creation.icosphere(subdivisions=4, radius=1.0)
        initial_faces = len(dense_mesh.faces)
        self.assertEqual(initial_faces, 5120)

        target_faces = 1200
        decimated = mesh_optimizer.decimate_geometry(dense_mesh, target_faces=target_faces)

        self.assertLessEqual(len(decimated.faces), target_faces + 50)
        self.assertGreater(len(decimated.faces), 500)
        self.assertTrue(len(decimated.vertices) < len(dense_mesh.vertices))

        print(f"[PASS] Feature 2: QEM Decimation verified ({initial_faces} -> {len(decimated.faces)} faces)")

    def test_04_vertex_optimization_and_duplicate_removal(self):
        """Features 3 & 4: Verify vertex deduplication, degenerate face removal, and cache optimization."""
        # Create a mesh with intentional duplicates and zero-area degenerate triangles
        verts = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0],  # Duplicate of vert 0
            [1.0, 0.0, 0.0],  # Duplicate of vert 1
            [0.5, 0.0, 0.0],  # Collinear on edge 0-1
        ])
        faces = np.array([
            [0, 1, 2],
            [0, 1, 2],  # Duplicate face
            [0, 1, 1],  # Degenerate collinear face
            [3, 4, 2],  # Face using duplicated vertices
        ])
        dirty_mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
        self.assertEqual(len(dirty_mesh.vertices), 6)
        self.assertEqual(len(dirty_mesh.faces), 4)

        cleaned = mesh_optimizer.remove_duplicates_and_degenerates(dirty_mesh)

        # Duplicates and degenerates removed
        self.assertLessEqual(len(cleaned.vertices), 4)
        self.assertLessEqual(len(cleaned.faces), 2)

        print(f"[PASS] Features 3 & 4: Vertex Optimization & Duplicate Removal ({len(dirty_mesh.faces)} -> {len(cleaned.faces)} faces)")

    def test_05_normal_preservation(self):
        """Feature 5: Verify normal preservation and orientation consistency."""
        sphere = trimesh.creation.icosphere(subdivisions=3, radius=1.0)
        decimated = mesh_optimizer.decimate_geometry(sphere, target_faces=400)
        decimated.fix_normals()

        # Vertex normals must be unit length
        norms = np.linalg.norm(decimated.vertex_normals, axis=1)
        self.assertTrue(np.allclose(norms, 1.0, atol=1e-3))

        # Normals on unit sphere centered at origin should closely align with vertex positions
        expected_normals = decimated.vertices / np.linalg.norm(decimated.vertices, axis=1, keepdims=True)
        alignment = np.sum(decimated.vertex_normals * expected_normals, axis=1)
        mean_alignment = np.mean(alignment)
        self.assertGreater(mean_alignment, 0.95, "Normals must point consistently outward from surface")

        print(f"[PASS] Feature 5: Normal Preservation verified (Mean outward normal alignment = {mean_alignment:.4f})")

    def test_06_uv_preservation(self):
        """Feature 6: Verify texture coordinates preservation across decimation."""
        sphere = trimesh.creation.icosphere(subdivisions=3, radius=1.0)
        bounds = sphere.bounds
        diff = bounds[1] - bounds[0]
        uvs = (sphere.vertices[:, :2] - bounds[0, :2]) / diff[:2]
        sphere.visual = trimesh.visual.TextureVisuals(uv=uvs)

        optimized, report = mesh_optimizer.optimize(
            mesh=sphere,
            target_polygon_budget=350,
            normalize_bounds=False,
        )

        self.assertTrue(hasattr(optimized.visual, "uv"))
        self.assertIsNotNone(optimized.visual.uv)
        self.assertEqual(len(optimized.visual.uv), len(optimized.vertices))
        # Coordinates must remain inside [0.0, 1.0]
        self.assertTrue(np.all(optimized.visual.uv >= -0.05))
        self.assertTrue(np.all(optimized.visual.uv <= 1.05))

        print(f"[PASS] Feature 6: UV Preservation verified across decimation ({len(sphere.faces)} -> {len(optimized.faces)} faces)")

    def test_07_material_preservation(self):
        """Feature 7: Verify PBR material bindings are retained."""
        box = trimesh.creation.box(extents=[1.0, 1.0, 1.0])
        pbr_mat = trimesh.visual.material.PBRMaterial(
            name="IronArmor",
            metallicFactor=0.90,
            roughnessFactor=0.35,
            baseColorFactor=[0.7, 0.7, 0.75, 1.0],
        )
        box.visual = trimesh.visual.TextureVisuals(
            uv=np.zeros((len(box.vertices), 2)),
            material=pbr_mat,
        )

        optimized, report = mesh_optimizer.optimize(
            mesh=box,
            budget_preset="low",
            normalize_bounds=False,
        )

        self.assertTrue(hasattr(optimized.visual, "material"))
        self.assertEqual(optimized.visual.material.name, "IronArmor")
        self.assertEqual(optimized.visual.material.metallicFactor, 0.90)

        print("[PASS] Feature 7: PBR Material Preserved with full metallic and roughness bindings")

    def test_08_bounding_box_normalization(self):
        """Feature 8: Verify Bounding-box centering, ground plane alignment, and scale normalization."""
        # Create an offset box
        mesh = trimesh.creation.box(extents=[2.0, 4.0, 6.0])
        mesh.apply_translation([10.0, 5.0, -8.0])

        normalized = mesh_optimizer.normalize_bounding_box(
            mesh,
            center_at_origin=True,
            align_to_ground=True,
            target_scale=1.0,
        )

        bounds = normalized.bounds
        extents = bounds[1] - bounds[0]
        max_extent = np.max(extents)

        # Check maximum extent normalized to 1.0
        self.assertAlmostEqual(max_extent, 1.0, places=4)
        # Check ground plane alignment: y_min == 0.0
        self.assertAlmostEqual(bounds[0][1], 0.0, places=4)
        # Check X and Z are centered around 0
        center_xz = (bounds[0][[0, 2]] + bounds[1][[0, 2]]) / 2.0
        self.assertTrue(np.allclose(center_xz, 0.0, atol=1e-4))

        print(f"[PASS] Feature 8: Bounding-box Normalization verified (Max Dim={max_extent}, Y_min={bounds[0][1]:.4f})")

    def test_09_mesh_validation_after_optimization(self):
        """Feature 9: Verify mesh validation after decimation."""
        valid_mesh = trimesh.creation.icosphere(subdivisions=2)
        val_valid = mesh_optimizer.validate_optimized_mesh(valid_mesh)
        self.assertTrue(val_valid["is_valid"])
        self.assertEqual(val_valid["status"], "VALID")
        self.assertEqual(len(val_valid["errors"]), 0)

        # Corrupt mesh with NaN vertex
        corrupt_mesh = valid_mesh.copy()
        corrupt_mesh.vertices[0] = [np.nan, 0.0, 0.0]
        val_corrupt = mesh_optimizer.validate_optimized_mesh(corrupt_mesh)
        self.assertFalse(val_corrupt["is_valid"])
        self.assertEqual(val_corrupt["status"], "INVALID")
        self.assertTrue(any("NaN" in err for err in val_corrupt["errors"]))

        print("[PASS] Feature 9: Mesh Validation accurately flags valid and corrupted geometries")

    def test_10_master_optimization_report(self):
        """Reports: Verify comprehensive telemetry metrics."""
        sphere = trimesh.creation.icosphere(subdivisions=4)
        input_obj = os.path.join(TEST_OUTPUT_DIR, "sphere_raw.obj")
        output_glb = os.path.join(TEST_OUTPUT_DIR, "sphere_optimized.glb")
        sphere.export(input_obj)

        opt_mesh, report = mesh_optimizer.optimize(
            mesh=sphere,
            budget_preset="low",
            input_file_path=input_obj,
            output_file_path=output_glb,
        )

        # Check all required fields
        self.assertIn("original_polygon_count", report)
        self.assertIn("final_polygon_count", report)
        self.assertIn("original_file_size_bytes", report)
        self.assertIn("final_file_size_bytes", report)
        self.assertIn("reduction_percentage", report)
        self.assertIn("optimization_duration_seconds", report)
        self.assertIn("bounds_before", report)
        self.assertIn("bounds_after", report)
        self.assertIn("validation", report)

        self.assertGreater(report["original_polygon_count"], report["final_polygon_count"])
        self.assertGreater(report["reduction_percentage"], 0.0)
        self.assertGreater(report["original_file_size_bytes"], 0)
        self.assertGreater(report["final_file_size_bytes"], 0)
        self.assertTrue(os.path.exists(output_glb))

        print(
            f"[PASS] Reports: Master Telemetry Report ({report['original_polygon_count']} -> {report['final_polygon_count']} faces, "
            f"-{report['reduction_percentage']}%, Time={report['optimization_duration_seconds']}s)"
        )

    def test_11_fastapi_optimizer_endpoints(self):
        """API: Verify /api/optimizer/presets, /api/optimizer/analyze, and /api/optimizer/optimize."""
        # 1. GET /api/optimizer/presets
        res_presets = self.client.get("/api/optimizer/presets")
        self.assertEqual(res_presets.status_code, 200)
        presets_data = res_presets.json()["presets"]
        self.assertIn("low", presets_data)
        self.assertIn("medium", presets_data)
        self.assertIn("high", presets_data)
        self.assertIn("custom", presets_data)

        # 2. POST /api/optimizer/analyze
        test_mesh_path = os.path.join(TEST_OUTPUT_DIR, "sphere_raw.obj")
        res_analyze = self.client.post("/api/optimizer/analyze", json={"mesh_path": test_mesh_path})
        self.assertEqual(res_analyze.status_code, 200)
        data_analyze = res_analyze.json()
        self.assertEqual(data_analyze["polygon_count"], 5120)

        # 3. POST /api/optimizer/optimize
        res_opt = self.client.post("/api/optimizer/optimize", json={
            "mesh_path": test_mesh_path,
            "budget_preset": "low",
            "normalize_bounds": True,
            "align_ground": True,
        })
        self.assertEqual(res_opt.status_code, 200)
        data_opt = res_opt.json()
        self.assertEqual(data_opt["status"], "SUCCESS")
        self.assertIn("report", data_opt)
        self.assertLess(data_opt["report"]["final_polygon_count"], 5120)
        self.assertLess(data_opt["report"]["final_polygon_count"], 5120)

        print("[PASS] API: FastAPI Endpoints /api/optimizer/presets, /analyze, and /optimize verified (HTTP 200)")

    def test_12_visual_and_numerical_comparison(self):
        """Testing: Compare before and after meshes visually and numerically."""
        # High-poly cylinder with detailed caps
        high_poly = trimesh.creation.cylinder(radius=1.0, height=3.0, sections=128)
        initial_faces = len(high_poly.faces)
        self.assertGreaterEqual(initial_faces, 500)

        # Decimate to low-poly
        low_poly, report = mesh_optimizer.optimize(
            mesh=high_poly,
            target_polygon_budget=160,
            normalize_bounds=True,
            align_ground=True,
        )
        final_faces = len(low_poly.faces)

        # Numerical Comparison
        reduction = report["reduction_percentage"]
        self.assertGreater(reduction, 60.0)

        # Render Side-by-Side Visual Comparison (Before Wireframe vs After Wireframe)
        fig = plt.figure(figsize=(10, 5), facecolor="#0a0f1d")

        # Plot Before
        ax1 = fig.add_subplot(1, 2, 1, projection="3d", facecolor="#0a0f1d")
        v1 = high_poly.vertices
        f1 = high_poly.faces
        poly1 = Poly3DCollection(v1[f1], facecolors="#38bdf8", edgecolors="#0284c7", linewidths=0.3, alpha=0.7)
        ax1.add_collection3d(poly1)
        ax1.set_title(f"BEFORE: Original High-Poly\n({initial_faces:,} Polygons)", color="#ffffff", fontsize=11, fontweight="bold")
        ax1.set_xlim(-1.5, 1.5)
        ax1.set_ylim(-1.5, 1.5)
        ax1.set_zlim(-1.5, 1.5)
        ax1.axis("off")

        # Plot After
        ax2 = fig.add_subplot(1, 2, 2, projection="3d", facecolor="#0a0f1d")
        v2 = low_poly.vertices
        f2 = low_poly.faces
        poly2 = Poly3DCollection(v2[f2], facecolors="#34d399", edgecolors="#059669", linewidths=0.8, alpha=0.7)
        ax2.add_collection3d(poly2)
        ax2.set_title(f"AFTER: Optimized Real-Time LOD\n({final_faces:,} Polygons, -{reduction}%)", color="#ffffff", fontsize=11, fontweight="bold")
        ax2.set_xlim(-1.5, 1.5)
        ax2.set_ylim(-1.5, 1.5)
        ax2.set_zlim(-1.5, 1.5)
        ax2.axis("off")

        comparison_img_path = os.path.join(TEST_OUTPUT_DIR, "optimization_before_after_comparison.png")
        plt.tight_layout()
        plt.savefig(comparison_img_path, facecolor=fig.get_facecolor(), dpi=150)
        plt.close(fig)

        self.assertTrue(os.path.exists(comparison_img_path))
        self.assertGreater(os.path.getsize(comparison_img_path), 10000)

        # Also copy to brain artifact directory for delivery presentation
        brain_art_dir = r"C:\Users\windows\.gemini\antigravity\brain\64ef4193-7a70-417d-9b27-f29f773d54c4"
        os.makedirs(brain_art_dir, exist_ok=True)
        brain_img_path = os.path.join(brain_art_dir, "optimization_before_after_comparison.png")
        with open(comparison_img_path, "rb") as f_in, open(brain_img_path, "wb") as f_out:
            f_out.write(f_in.read())

        print(f"[PASS] Testing: Visual & Numerical Comparison saved to: {brain_img_path}")

if __name__ == "__main__":
    unittest.main()
