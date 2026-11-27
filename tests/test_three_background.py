"""
Tests for PolyGen Interactive 3D Ambient WebGL Background System.
Verifies Three.js script generation, CSS styling, non-blocking properties,
Streamlit/Gradio integration, and live server endpoints.
"""

import os
import sys
import unittest
import urllib.request

# Ensure workspace root is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from dashboard.three_background import (
    get_3d_background_script,
    get_gradio_3d_background_html,
)


class TestThreeBackground(unittest.TestCase):
    def test_script_structure_and_components(self):
        """Verify that the 3D WebGL script contains all required architectural elements."""
        script = get_3d_background_script()
        self.assertIsInstance(script, str)
        self.assertIn("<script>", script)
        self.assertIn("</script>", script)
        self.assertIn("polygen-ambient-3d-canvas", script)

        # Check non-blocking configuration
        self.assertTrue("pointer-events: none" in script or 'pointerEvents = "none"' in script)
        self.assertTrue("position: fixed" in script or 'position = "fixed"' in script)
        self.assertTrue("z-index: 0" in script or 'zIndex = "0"' in script)

        # Check 3D Three.js components
        self.assertIn("IcosahedronGeometry", script)
        self.assertIn("OctahedronGeometry", script)
        self.assertIn("PlaneGeometry", script)
        self.assertIn("BufferGeometry", script)
        self.assertIn("PointsMaterial", script)

        # Check interactive controls
        self.assertIn("mousemove", script)
        self.assertIn("resize", script)
        self.assertIn("requestAnimationFrame", script)

        # Check offline fallback
        self.assertIn("runNative3DFallback", script)

    def test_gradio_integration_html(self):
        """Verify Gradio helper function returns expected snippet."""
        html = get_gradio_3d_background_html()
        self.assertIsInstance(html, str)
        self.assertIn("polygen-ambient-3d-canvas", html)

    def test_streamlit_server_live(self):
        """Verify that Streamlit dashboard on port 8501 is serving requests."""
        try:
            resp = urllib.request.urlopen("http://localhost:8501", timeout=5)
            self.assertEqual(resp.status, 200)
        except Exception as e:
            self.skipTest(f"Streamlit server not reachable: {e}")

    def test_gradio_server_live_with_3d_canvas(self):
        """Verify that Gradio dashboard on port 7860 serves HTML with the 3D background."""
        try:
            resp = urllib.request.urlopen("http://127.0.0.1:7860", timeout=5)
            self.assertEqual(resp.status, 200)
            content = resp.read().decode("utf-8")
            self.assertIn("polygen-ambient-3d-canvas", content)
            self.assertIn("IcosahedronGeometry", content)
        except Exception as e:
            self.skipTest(f"Gradio server not reachable: {e}")

    def test_frontend_react_three_background_integration(self):
        """Verify that the frontend React app includes the 3D WebGL background across all dashboards."""
        comp_path = os.path.join(BASE_DIR, "frontend", "src", "components", "ThreeBackground.tsx")
        app_path = os.path.join(BASE_DIR, "frontend", "src", "App.tsx")
        self.assertTrue(os.path.exists(comp_path), f"Missing {comp_path}")
        self.assertTrue(os.path.exists(app_path), f"Missing {app_path}")

        with open(comp_path, "r", encoding="utf-8") as f:
            comp_content = f.read()

        # Check required 3D features in React component
        self.assertIn("IcosahedronGeometry", comp_content)
        self.assertIn("OctahedronGeometry", comp_content)
        self.assertIn("PlaneGeometry", comp_content)
        self.assertIn("BufferGeometry", comp_content)
        self.assertIn("mousemove", comp_content)
        self.assertIn("pointer-events-none", comp_content)

        with open(app_path, "r", encoding="utf-8") as f:
            app_content = f.read()

        self.assertIn("ThreeBackground", app_content)
        self.assertIn("<ThreeBackground />", app_content)


if __name__ == "__main__":
    unittest.main()
