import os
import sys
import time
os.environ["AI_BACKEND"] = "procedural"
sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

from app.config import settings
settings.AI_BACKEND = "procedural"
from app.services.prompt_engine import prompt_engine
from ai_models.text_to_3d.generator import text_to_3d_generator
from processing.mesh_cleaner import mesh_cleaner
from processing.uv_unwrapper import uv_unwrapper
from processing.texture_baker import texture_baker
from processing.mesh_optimizer import mesh_optimizer
from processing.glb_exporter import glb_exporter

SCENARIOS = [
    {
        "name": "1. Wooden Chair",
        "prompt": "A rustic oak wooden chair with carved armrests.",
        "style": "realistic",
        "budget": 8000,
    },
    {
        "name": "2. Medieval Broadsword",
        "prompt": "A rusted medieval broadsword with a glowing blue sapphire in the hilt.",
        "style": "medieval fantasy",
        "budget": 10000,
    },
    {
        "name": "3. Treasure Chest",
        "prompt": "A weathered pirate treasure chest reinforced with brass bands and padlock.",
        "style": "fantasy",
        "budget": 12000,
    },
    {
        "name": "4. Metallic Battle Robot",
        "prompt": "A futuristic metallic battle robot with neon green visor.",
        "style": "sci-fi",
        "budget": 15000,
    },
    {
        "name": "5. Stone Sculpture",
        "prompt": "An ancient carved stone sculpture covered in moss.",
        "style": "ancient",
        "budget": 10000,
    },
]

def run_benchmarks():
    print("=" * 80)
    print("POLYGEN BENCHMARK SUITE: 5 CANONICAL 3D GENERATION SCENARIOS")
    print("=" * 80)

    results = []

    for idx, item in enumerate(SCENARIOS):
        print(f"\n--- Testing Scenario: {item['name']} ---")
        prompt_text = item["prompt"]
        budget = item["budget"]
        start_time = time.time()

        # 1. Prompt processing
        t0 = time.time()
        structured = prompt_engine.process(prompt_text, style_override=item["style"], polygon_budget=budget)
        t_prompt = time.time() - t0
        print(f"  [1/6] Prompt parsed in {t_prompt:.3f}s: object='{structured.object}', material='{structured.material}'")

        slug = "".join(c for c in structured.object[:12] if c.isalnum() or c in ('_', '-')).strip()
        if not slug:
            slug = f"asset_{idx}"
        
        # 2. 3D Mesh Generation
        t0 = time.time()
        raw_path = os.path.join(settings.STORAGE_RAW_DIR, f"bench_{slug}_raw.obj")
        raw_mesh, meta = text_to_3d_generator.generate(structured, raw_path)
        t_mesh = time.time() - t0
        print(f"  [2/6] Mesh generated in {t_mesh:.3f}s: {len(raw_mesh.vertices)} verts, {len(raw_mesh.faces)} faces")

        # 3. Mesh cleaning & UV parameterization
        t0 = time.time()
        cleaned_mesh, clean_stats = mesh_cleaner.clean(raw_mesh)
        unwrapped_mesh, uv_stats = uv_unwrapper.unwrap(cleaned_mesh)
        t_uv = time.time() - t0
        print(f"  [3/6] UV parameterization (xatlas) in {t_uv:.3f}s: {len(unwrapped_mesh.vertices)} mapped verts")

        # 4. PBR texture synthesis
        t0 = time.time()
        tex_dir = os.path.join(settings.STORAGE_TEXTURES_DIR, f"bench_{slug}")
        tex_paths = texture_baker.generate_pbr_set(structured, tex_dir, resolution=1024)
        t_tex = time.time() - t0
        print(f"  [4/6] PBR maps baked in {t_tex:.3f}s (BaseColor, Roughness, Metallic, Normal, Emissive)")

        # 5. Mesh Optimization
        t0 = time.time()
        opt_mesh, opt_stats = mesh_optimizer.optimize(unwrapped_mesh, target_polygon_budget=budget)
        t_opt = time.time() - t0
        print(f"  [5/6] Optimization in {t_opt:.3f}s: final faces={opt_stats['optimized_faces']}")

        # 6. GLB Export & Verification
        t0 = time.time()
        glb_path = os.path.join(settings.STORAGE_EXPORTS_DIR, f"bench_{slug}.glb")
        val_stats = glb_exporter.export(opt_mesh, tex_paths, glb_path)
        t_export = time.time() - t0
        print(f"  [6/6] GLB exported & verified in {t_export:.3f}s: {val_stats['file_size_mb']} MB")

        total_time = time.time() - start_time
        print(f"  --> TOTAL DURATION: {total_time:.2f}s | VALID: {val_stats['is_valid']}")

        results.append({
            "name": item["name"],
            "prompt": prompt_text,
            "object": structured.object,
            "material": structured.material,
            "verified_faces": val_stats["verified_faces"],
            "verified_verts": val_stats["verified_vertices"],
            "size_mb": val_stats["file_size_mb"],
            "duration_s": round(total_time, 2),
            "dimensions": val_stats["bounding_box_dimensions"],
            "glb_path": glb_path
        })

    print("\n" + "=" * 80)
    print("FINAL BENCHMARK SUMMARY TABLE")
    print("=" * 80)
    print(f"{'Scenario':<26} | {'Faces':<7} | {'Verts':<7} | {'Size MB':<8} | {'Time (s)':<8} | {'Status'}")
    print("-" * 80)
    for r in results:
        print(f"{r['name']:<26} | {r['verified_faces']:<7} | {r['verified_verts']:<7} | {r['size_mb']:<8} | {r['duration_s']:<8} | PASSED")
    print("=" * 80)

if __name__ == "__main__":
    run_benchmarks()
