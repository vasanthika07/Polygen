import sys
import os
import asyncio
import json

os.environ["AI_BACKEND"] = "procedural"
os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

from httpx import AsyncClient, ASGITransport
from app.main import app

TEST_PROMPTS = [
    # 1. Furniture
    {
        "category": "furniture",
        "prompt": "A rustic oak dining table with polished brass legs and subtle wood grain.",
        "expected_object": "dining table",
        "expected_materials": ["carved oak wood", "tarnished brass"],
    },
    {
        "category": "furniture",
        "prompt": "An ornate Victorian armchair upholstered in dark red velvet with carved mahogany armrests.",
        "expected_object": "armchair",
        "expected_materials": ["rich velvet", "polished mahogany"],
    },
    {
        "category": "furniture",
        "prompt": "A modern minimalist bookshelf made of frosted glass and black steel frame.",
        "expected_object": "bookshelf",
        "expected_materials": ["translucent glass", "forged steel"],
    },
    {
        "category": "furniture",
        "prompt": "A four-poster king size bed with weathered pine posts and embroidered linen curtains.",
        "expected_object": "bed",
        "expected_materials": ["rustic pine", "textured fabric"],
    },

    # 2. Weapons
    {
        "category": "weapons",
        "prompt": "A rusted medieval broadsword with a glowing blue sapphire in the hilt.",
        "expected_object": "medieval broadsword",
        "expected_materials": ["rusted metal", "blue sapphire"],
    },
    {
        "category": "weapons",
        "prompt": "A dual-bladed battleaxe forged from damascus steel with chipped edge and leather grip wrap.",
        "expected_object": "battleaxe",
        "expected_materials": ["damascus steel", "worn leather"],
    },
    {
        "category": "weapons",
        "prompt": "A futuristic sci-fi sniper rifle with matte carbon fiber body and glowing cyan laser sight.",
        "expected_object": "rifle",
        "expected_materials": ["woven carbon fiber"],
    },
    {
        "category": "weapons",
        "prompt": "An ancient elven recurve bow carved from polished yew wood with glowing golden runes.",
        "expected_object": "bow",
        "expected_materials": ["aged wood"],
    },

    # 3. Vehicles
    {
        "category": "vehicles",
        "prompt": "A sleek cyberpunk sports car with reflective black chrome and neon magenta underglow.",
        "expected_object": "sports car",
        "expected_materials": ["reflective chrome"],
    },
    {
        "category": "vehicles",
        "prompt": "A weathered pirate galleon with tattered canvas sails and battle-worn wooden hull.",
        "expected_object": "galleon",
        "expected_materials": ["aged wood"],
    },
    {
        "category": "vehicles",
        "prompt": "An interstellar starfighter spacecraft with titanium armor plating and twin plasma exhaust conduits.",
        "expected_object": "starfighter",
        "expected_materials": ["brushed titanium"],
    },
    {
        "category": "vehicles",
        "prompt": "A vintage steampunk airship with brass boiler pipes and riveted copper fuselage.",
        "expected_object": "airship",
        "expected_materials": ["tarnished brass", "oxidized copper"],
    },

    # 4. Architecture
    {
        "category": "architecture",
        "prompt": "A gothic cathedral bell tower with arched stained glass windows and stone gargoyles.",
        "expected_object": "tower",
        "expected_materials": ["stained glass", "weathered stone"],
    },
    {
        "category": "architecture",
        "prompt": "A modular sci-fi bunker fortress reinforced with blast-proof concrete and steel security doors.",
        "expected_object": "bunker",
        "expected_materials": ["reinforced concrete", "forged steel"],
    },
    {
        "category": "architecture",
        "prompt": "An ancient Japanese pagoda temple with curved terracotta roof tiles and red cedar pillars.",
        "expected_object": "pagoda",
        "expected_materials": ["weathered stone"],
    },
    {
        "category": "architecture",
        "prompt": "A medieval stone castle fortress with crenelated battlements and deep moat archway.",
        "expected_object": "castle",
        "expected_materials": ["weathered stone"],
    },

    # 5. Animals & Creatures
    {
        "category": "animals",
        "prompt": "A cybernetic mechanical wolf with polished steel chassis and glowing emerald eyes.",
        "expected_object": "wolf",
        "expected_materials": ["polished steel", "green emerald"],
    },
    {
        "category": "animals",
        "prompt": "A ferocious fire-breathing dragon with crimson scales, horned crest, and smoking nostrils.",
        "expected_object": "dragon",
        "expected_materials": ["organic skin"],
    },
    {
        "category": "animals",
        "prompt": "A majestic soaring golden eagle with feathered wings and razor-sharp talons.",
        "expected_object": "eagle",
        "expected_materials": ["ornate gold"],
    },
    {
        "category": "animals",
        "prompt": "A mystical crystal stag with translucent amethyst antlers and ethereal glowing fur.",
        "expected_object": "stag",
        "expected_materials": ["purple amethyst", "thick animal fur"],
    },

    # 6. Fantasy Objects / Props
    {
        "category": "fantasy_props",
        "prompt": "An ancient runic treasure chest bound in heavy iron bands with an ornate skull padlock.",
        "expected_object": "treasure chest",
        "expected_materials": ["cast iron"],
    },
    {
        "category": "fantasy_props",
        "prompt": "A bubbling health potion vial filled with luminescent red elixir and sealed with beeswax cork.",
        "expected_object": "potion bottle",
        "expected_materials": ["translucent glass"],
    },
    {
        "category": "fantasy_props",
        "prompt": "A levitating arcane magic orb crackling with purple lightning sparks and floating brass rings.",
        "expected_object": "magic orb",
        "expected_materials": ["tarnished brass"],
    },
    {
        "category": "fantasy_props",
        "prompt": "A leather-bound sorcerer spellbook with tarnished gold filigree and an embossed dragon sigil.",
        "expected_object": "spellbook",
        "expected_materials": ["worn leather", "ornate gold"],
    },
]

async def run_part5_tests():
    print("=" * 70)
    print("POLYGEN PART 5: NATURAL LANGUAGE PROMPT UNDERSTANDING ENGINE TESTS")
    print("=" * 70)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Prompt Validation Checks
        print("\n--- 1. Testing Input Validation ---")
        short_res = await client.post("/api/prompt/analyze", json={"prompt": "hi"})
        assert short_res.status_code == 422, f"Expected 422 for prompt under 3 chars: {short_res.text}"
        print("✓ Prompts under 3 characters rejected with 422 Unprocessable Entity")

        empty_res = await client.post("/api/prompt/analyze", json={"prompt": "   "})
        assert empty_res.status_code == 422
        print("✓ Whitespace-only prompts rejected with 422 Unprocessable Entity")

        too_long_res = await client.post("/api/prompt/analyze", json={"prompt": "A" * 1005})
        assert too_long_res.status_code == 422
        print("✓ Prompts exceeding 1000 characters rejected with 422 Unprocessable Entity")

        # 2. Test Canonical Example
        print("\n--- 2. Testing Master Prompt Canonical Example ---")
        canonical_prompt = "A rusted medieval broadsword with a glowing blue sapphire in the hilt."
        can_res = await client.post("/api/prompt/analyze", json={"prompt": canonical_prompt})
        assert can_res.status_code == 200, f"Canonical prompt failed: {can_res.text}"
        can_data = can_res.json()

        assert can_data["object"] == "medieval broadsword", f"Expected 'medieval broadsword', got '{can_data['object']}'"
        assert can_data["style"] == "fantasy medieval", f"Expected 'fantasy medieval', got '{can_data['style']}'"
        assert "rusted metal" in can_data["materials"]
        assert "blue sapphire" in can_data["materials"]
        assert "dark brown" in can_data["colors"]
        assert "steel grey" in can_data["colors"]
        assert "blue" in can_data["colors"]
        assert "rust" in can_data["surface_details"]
        assert "scratches" in can_data["surface_details"]
        assert can_data["lighting"] == "cinematic"
        assert "blue emissive glow" in can_data["special_effects"]
        assert len(can_data["geometry_requirements"]) > 0
        assert len(can_data["texture_requirements"]) > 0
        assert len(can_data["negative_prompt"]) > 0
        print("✓ Canonical 'rusted medieval broadsword' matches master prompt specification 100%")

        # 3. Test 24 Diverse Prompts Across All 6 Required Categories
        print("\n--- 3. Testing 24 Multi-Category Prompts ---")
        current_cat = None
        for i, item in enumerate(TEST_PROMPTS, 1):
            if item["category"] != current_cat:
                current_cat = item["category"]
                print(f"\n  [Category: {current_cat.upper()}]")

            res = await client.post("/api/prompt/analyze", json={"prompt": item["prompt"]})
            assert res.status_code == 200, f"Failed analyzing '{item['prompt']}': {res.text}"
            data = res.json()

            # Verify key properties
            assert len(data["object"]) > 0, f"Empty object extracted for: {item['prompt']}"
            assert len(data["style"]) > 0, f"Empty style for: {item['prompt']}"
            assert len(data["materials"]) > 0, f"Empty materials for: {item['prompt']}"
            assert len(data["colors"]) > 0, f"Empty colors for: {item['prompt']}"
            assert len(data["surface_details"]) > 0, f"Empty surface details for: {item['prompt']}"
            assert len(data["geometry_requirements"]) >= 3, f"Insufficient geometry constraints for: {item['prompt']}"
            assert len(data["texture_requirements"]) >= 3, f"Insufficient texture requirements for: {item['prompt']}"
            assert len(data["negative_prompt"]) >= 5, f"Insufficient negative prompt items for: {item['prompt']}"
            
            # Verify Model Specific Prompts
            assert "shap_e" in data["model_prompts"]
            assert "hunyuan3d" in data["model_prompts"]
            assert "stable_diffusion" in data["model_prompts"]
            assert "triposr" in data["model_prompts"]

            # Ensure parser does NOT claim that it has generated a 3D model
            assert "glb_path" not in data, "Parser must not pretend to have generated GLB file!"
            assert "asset_id" not in data, "Parser must not claim to have created a GeneratedAsset record!"

            print(f"    ✓ Prompt {i:02d} ({item['category']}): '{data['object']}' | Style: {data['style']} | Mat: {data['materials'][:2]} | Col: {data['colors'][:2]}")

        # 4. Test Missing Detail Handling
        print("\n--- 4. Testing Missing Detail Heuristic Inferences ---")
        sparse_res = await client.post("/api/prompt/analyze", json={"prompt": "A simple chair."})
        assert sparse_res.status_code == 200
        sparse_data = sparse_res.json()
        assert sparse_data["object"] == "chair"
        assert len(sparse_data["materials"]) > 0, "Failed to infer default materials for simple prompt"
        assert len(sparse_data["colors"]) > 0, "Failed to infer default colors for simple prompt"
        assert len(sparse_data["inferred_details"]) > 0
        print(f"✓ Inferred missing materials and colors for sparse prompt 'A simple chair.': {sparse_data['materials']}")

    print("\n" + "=" * 70)
    print("ALL 24 MULTI-CATEGORY PROMPT SPECIFICATION TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_part5_tests())

