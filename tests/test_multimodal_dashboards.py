"""
PolyGen Multimodal & Dashboard Verification Test Suite
Tests:
1. Multimodal Analyzer: Image silhouette, depth estimation, color palette extraction.
2. Multimodal Generator: Image-to-3D and Image+Text synthesis to binary GLB.
3. FastAPI Multimodal endpoint: POST /api/generate/multimodal.
4. Streamlit & Gradio Live Dashboard HTTP connectivity checks.
"""

import os
import sys
import uuid
import unittest
import urllib.request
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from fastapi.testclient import TestClient
from backend.app.main import app
from ai_models.multimodal.multimodal_analyzer import multimodal_analyzer
from ai_models.multimodal.multimodal_generator import multimodal_generator

class TestMultimodalAndDashboards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.user_email = f"mm_{uuid.uuid4().hex[:6]}@polygen.ai"
        res = cls.client.post("/api/auth/register", json={
            "email": cls.user_email,
            "password": "PolyGenSecure2026!",
            "name": "Multimodal Tester"
        })
        assert res.status_code == 201
        cls.token = res.json()["access_token"]

        # Synthetic test image (blue diamond on transparent canvas)
        cls.test_image = Image.new("RGBA", (150, 150), (0, 0, 0, 0))
        for y in range(150):
            for x in range(150):
                if abs(x - 75) + abs(y - 75) < 45:
                    cls.test_image.putpixel((x, y), (20, 160, 255, 255))

    def test_01_multimodal_visual_feature_extraction(self):
        """Verify visual feature extraction from reference image."""
        feats = multimodal_analyzer.extract_visual_features(self.test_image)
        self.assertIn("aspect_ratio", feats)
        self.assertIn("dominant_color_hex", feats)
        self.assertIn("estimated_roughness", feats)
        self.assertIn("depth_map", feats)
        self.assertEqual(feats["depth_map"].shape, (128, 128))
        self.assertTrue(feats["dominant_color_hex"].startswith("#"))

    def test_02_multimodal_prompt_fusion(self):
        """Verify fusion of text directives with image visual cues."""
        fused = multimodal_analyzer.fuse_multimodal_prompt(
            text_prompt="An ornate glowing dagger with gold hilt",
            image_input=self.test_image,
            audio_transcript="Make the blade razor sharp",
        )
        self.assertIn("An ornate glowing dagger with gold hilt", fused["fused_prompt"])
        self.assertIn("Make the blade razor sharp", fused["fused_prompt"])
        self.assertTrue(fused["has_image"])
        self.assertIsNotNone(fused["visual_features"])

    def test_03_multimodal_image_to_3d_generation(self):
        """Verify end-to-end Image-to-3D asset generation."""
        res = multimodal_generator.generate_multimodal_asset(
            image_input=self.test_image,
            polygon_budget=1200,
            quality="standard"
        )
        self.assertTrue(os.path.exists(res["glb_path"]))
        self.assertTrue(res["is_valid_glb"])
        self.assertGreater(res["polygon_count"], 100)
        self.assertGreater(res["file_size_mb"], 0.1)

        # Check binary glTF magic bytes
        with open(res["glb_path"], "rb") as f:
            magic = f.read(4)
        self.assertEqual(magic, b"glTF")

    def test_04_fastapi_multimodal_endpoint(self):
        """Verify POST /api/generate/multimodal API endpoint."""
        import base64, io
        buf = io.BytesIO()
        self.test_image.save(buf, format="PNG")
        b64_str = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"

        headers = {"Authorization": f"Bearer {self.token}"}
        res = self.client.post("/api/generate/multimodal", json={
            "prompt": "A glowing crystal relic",
            "image_base64": b64_str,
            "style": "fantasy",
            "quality": "high",
            "polygon_budget": 2500,
        }, headers=headers)
        self.assertEqual(res.status_code, 202)
        data = res.json()
        self.assertIn("job_id", data)
        self.assertEqual(data["status"], "queued")

    def test_05_streamlit_dashboard_live_status(self):
        """Verify Streamlit dashboard is online and responding on port 8501."""
        try:
            req = urllib.request.Request("http://localhost:8501", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                self.assertEqual(resp.status, 200)
                html = resp.read().decode("utf-8")
                self.assertIn("Streamlit", html)
        except Exception as e:
            self.fail(f"Streamlit dashboard unreachable at http://localhost:8501: {e}")

    def test_06_gradio_dashboard_live_status(self):
        """Verify Gradio dashboard is online and responding on port 7860."""
        try:
            req = urllib.request.Request("http://127.0.0.1:7860", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                self.assertEqual(resp.status, 200)
                html = resp.read().decode("utf-8")
                self.assertIn("Gradio", html)
        except Exception as e:
            self.fail(f"Gradio dashboard unreachable at http://127.0.0.1:7860: {e}")

if __name__ == "__main__":
    unittest.main()
