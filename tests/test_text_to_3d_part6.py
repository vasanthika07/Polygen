import os
import sys
import unittest
import trimesh
import numpy as np

# Ensure backend and root are in python path
sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

from app.config import settings
from app.services.prompt_engine import prompt_engine
from ai_models.text_to_3d.config import default_config, TextTo3DConfig
from ai_models.text_to_3d.hardware import hardware_detector
from ai_models.text_to_3d.model_loader import model_loader
from ai_models.text_to_3d.prompt_formatter import prompt_formatter
from ai_models.text_to_3d.mesh_validator import mesh_validator
from ai_models.text_to_3d.preview_generator import preview_generator
from ai_models.text_to_3d.generator import text_to_3d_generator

TEST_OUTPUT_DIR = os.path.abspath("tests/output_part6")

class TestTextTo3DPart6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

    def test_01_hardware_detector_and_evaluations(self):
        """Verify hardware detection and comparative model suitability analysis."""
        hw = hardware_detector.get_hardware_info()
        self.assertIn("cpu_count", hw)
        self.assertIn("cuda_available", hw)
        self.assertIn("system_ram_total_mb", hw)

        # Shap-E evaluation
        shape_eval = hardware_detector.evaluate_model_fit("shap-e")
        self.assertTrue(shape_eval["supported"])
        self.assertIn("diffusion", shape_eval["reason"])

        # Hunyuan3D evaluation
        hunyuan_eval = hardware_detector.evaluate_model_fit("hunyuan3d")
        self.assertIn("16GB VRAM", hunyuan_eval["reason"])

        # TripoSR evaluation
        triposr_eval = hardware_detector.evaluate_model_fit("triposr")
        self.assertFalse(triposr_eval["supported"])  # Strictly image-to-3D
        self.assertIn("image-to-3d", triposr_eval["reason"].lower())
        print(f"\n[PASS] Hardware & Model Evaluations: CUDA={hw['cuda_available']}, RAM={hw['system_ram_total_mb']} MB")

    def test_02_prompt_formatter(self):
        """Verify model-specific prompt conditioning formatter."""
        structured = prompt_engine.process("A rusted medieval broadsword with a glowing blue sapphire in the hilt.")
        formatted = prompt_formatter.format_for_shape(structured)

        self.assertEqual(formatted["model_target"], "shap-e-text300M")
        self.assertIn("medieval broadsword", formatted["formatted_prompt"])
        self.assertEqual(formatted["guidance_scale"], 15.0)
        self.assertGreater(len(formatted["negative_prompt"]), 0)

        hunyuan_format = prompt_formatter.format_for_hunyuan3d(structured)
        self.assertEqual(hunyuan_format["model_target"], "hunyuan3d")
        self.assertIn("3D asset", hunyuan_format["formatted_prompt"])
        print(f"[PASS] Prompt Formatter: Positive='{formatted['formatted_prompt']}'")

    def test_03_mesh_validator_clean(self):
        """Verify mesh geometry validation and degenerate face removal."""
        box = trimesh.creation.box()
        validated_mesh, stats = mesh_validator.validate_and_clean(box)
        self.assertTrue(stats["is_valid"])
        self.assertEqual(stats["valid_vertices"], 8)
        self.assertEqual(stats["valid_faces"], 12)
        self.assertGreater(stats["bounding_box_volume"], 0.9)
        print(f"[PASS] Mesh Validator: 8 verts, 12 faces validated cleanly")

    def _verify_generated_model(self, prompt_text: str, safe_slug: str):
        """Helper to verify a generated 3D model according to Part 6 specifications."""
        raw_mesh_path = os.path.join(TEST_OUTPUT_DIR, f"{safe_slug}_raw.obj")

        mesh, meta = text_to_3d_generator.generate(
            prompt_input=prompt_text,
            output_path=raw_mesh_path,
            output_format="obj",
            generate_preview_image=True,
        )

        # 1. Verify file exists on disk and is non-empty
        self.assertTrue(os.path.exists(raw_mesh_path), f"Output file missing: {raw_mesh_path}")
        self.assertGreater(os.path.getsize(raw_mesh_path), 500, f"Output file is too small: {os.path.getsize(raw_mesh_path)} bytes")

        # 2. Verify mesh can be loaded by Trimesh (standard 3D engine parser)
        loaded_mesh = trimesh.load(raw_mesh_path, file_type="obj")
        self.assertIsInstance(loaded_mesh, trimesh.Trimesh, "Failed to load OBJ as Trimesh instance")

        # 3. Verify non-empty vertices and faces
        self.assertGreater(len(loaded_mesh.vertices), 0, "Mesh contains 0 vertices")
        self.assertGreater(len(loaded_mesh.faces), 0, "Mesh contains 0 faces")
        self.assertEqual(loaded_mesh.faces.shape[1], 3, "Mesh faces are not triangular")

        # 4. Verify non-zero 3D bounding box volume (not a flat 2D plane or point)
        extents = loaded_mesh.extents
        volume = extents[0] * extents[1] * extents[2]
        self.assertGreater(volume, 0.001, f"Mesh volume too small or degenerate: {volume}")

        # 5. Verify Blender-compliant Wavefront OBJ structure
        with open(raw_mesh_path, "r", encoding="utf-8") as f:
            obj_lines = f.readlines()
            has_v = any(line.startswith("v ") for line in obj_lines)
            has_f = any(line.startswith("f ") for line in obj_lines)
            self.assertTrue(has_v, "OBJ missing vertex lines ('v ')")
            self.assertTrue(has_f, "OBJ missing face lines ('f ')")

        # 6. Verify offscreen preview thumbnail exists and is valid PNG
        preview_path = meta.get("preview_image_path")
        self.assertIsNotNone(preview_path, "Preview image path is None")
        self.assertTrue(os.path.exists(preview_path), f"Preview thumbnail does not exist: {preview_path}")
        self.assertGreater(os.path.getsize(preview_path), 1000, "Preview image is empty or invalid")

        # 7. Verify telemetry measurements
        self.assertIn("model_loading_time_ms", meta)
        self.assertGreaterEqual(meta["model_loading_time_ms"], 0)
        self.assertIn("inference_time_ms", meta)
        self.assertGreater(meta["inference_time_ms"], 0)
        self.assertIn("mesh_generation_time_ms", meta)
        self.assertGreater(meta["mesh_generation_time_ms"], 0)
        self.assertIn("memory_usage_mb", meta)
        self.assertGreater(meta["memory_usage_mb"], 0)
        self.assertIn(meta["device"], ["cuda", "cpu"])
        self.assertIn(meta["execution_mode"], ["neural_diffusion", "cpu_fallback_procedural"])

        # 8. Verify documented fallback mode transparency
        if not meta["gpu_detected"]:
            self.assertTrue(meta["fallback_used"])
            self.assertIsNotNone(meta["fallback_reason"])
            self.assertIn("CUDA", meta["fallback_reason"])

        print(
            f"[PASS] '{prompt_text}' -> Verts: {len(loaded_mesh.vertices)}, "
            f"Faces: {len(loaded_mesh.faces)}, Time: {meta['mesh_generation_time_ms']} ms, "
            f"RAM: {meta['memory_usage_mb']} MB, Preview: {os.path.basename(preview_path)}"
        )
        return loaded_mesh, meta

    def test_04_generate_model_1_wooden_chair(self):
        """1. Wooden chair generation test"""
        self._verify_generated_model("Wooden chair", "wooden_chair")

    def test_05_generate_model_2_medieval_sword(self):
        """2. Medieval sword generation test"""
        self._verify_generated_model("Medieval sword", "medieval_sword")

    def test_06_generate_model_3_fantasy_treasure_chest(self):
        """3. Fantasy treasure chest generation test"""
        self._verify_generated_model("Fantasy treasure chest", "fantasy_treasure_chest")

    def test_07_generate_model_4_metallic_robot(self):
        """4. Metallic robot generation test"""
        self._verify_generated_model("Metallic robot", "metallic_robot")

    def test_08_generate_model_5_stone_sculpture(self):
        """5. Stone sculpture generation test"""
        self._verify_generated_model("Stone sculpture", "stone_sculpture")

    def test_09_ply_export_format(self):
        """Verify PLY format raw mesh export."""
        ply_path = os.path.join(TEST_OUTPUT_DIR, "sculpture_test.ply")
        mesh, meta = text_to_3d_generator.generate(
            prompt_input="Stone sculpture",
            output_path=ply_path,
            output_format="ply",
            generate_preview_image=False,
        )
        self.assertTrue(os.path.exists(ply_path))
        loaded_ply = trimesh.load(ply_path, file_type="ply")
        self.assertGreater(len(loaded_ply.vertices), 0)
        self.assertGreater(len(loaded_ply.faces), 0)
        self.assertEqual(meta["output_format"], "ply")
        print(f"[PASS] PLY Export Format: {len(loaded_ply.vertices)} verts, {len(loaded_ply.faces)} faces in PLY file")

if __name__ == "__main__":
    unittest.main(verbosity=2)
