import asyncio
import os
import sys

# Ensure repository root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from httpx import AsyncClient, ASGITransport
from app.main import app

async def test_frontend_spa_and_assets():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Test root loads compiled index.html
        res = await ac.get("/")
        assert res.status_code == 200, f"Expected 200 from /, got {res.status_code}"
        assert "<div id=\"root\"></div>" in res.text, "Index.html does not contain #root div"
        print("✓ Root index.html served correctly")

        # 2. Test SPA fallback routes (12 routes)
        routes = [
            "/landing",
            "/login",
            "/register",
            "/dashboard",
            "/generate",
            "/workspace",
            "/viewer",
            "/library",
            "/history",
            "/asset-details",
            "/settings",
            "/not-found"
        ]
        for route in routes:
            r = await ac.get(route)
            assert r.status_code == 200, f"Route {route} failed with {r.status_code}"
            assert "<div id=\"root\"></div>" in r.text
        print(f"✓ All {len(routes)} client routes fallback properly to SPA index.html")

        # 3. Test static sample GLB models accessibility
        sample_models = [
            "/models/sample_sword.glb",
            "/models/sample_chair.glb",
            "/models/sample_robot.glb",
            "/models/sample_sculpture.glb",
        ]
        for model_path in sample_models:
            r = await ac.get(model_path)
            assert r.status_code == 200, f"Failed to fetch {model_path}: {r.status_code}"
            assert len(r.content) > 1000000, f"Sample model {model_path} too small ({len(r.content)} bytes)"
            # GLB magic header is 'glTF' in ASCII (0x46546C67)
            assert r.content[:4] == b'glTF', f"{model_path} does not have valid GLB magic header 'glTF'"
        print("✓ All 4 real sample GLB models served and verified with valid 'glTF' binary headers")

if __name__ == "__main__":
    asyncio.run(test_frontend_spa_and_assets())
    print("\nAll Frontend Integration and Model Tests Passed Successfully!")

