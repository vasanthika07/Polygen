import os
import sys
import shutil
os.environ["AI_BACKEND"] = "procedural"
sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

from app.config import settings
settings.AI_BACKEND = "procedural"

from app.schemas.job import StructuredPrompt
from app.services.prompt_engine import prompt_engine
from ai_models.text_to_3d.generator import text_to_3d_generator
from processing.mesh_cleaner import mesh_cleaner
from processing.uv_unwrapper import uv_unwrapper
from processing.texture_baker import texture_baker
from processing.mesh_optimizer import mesh_optimizer
from processing.glb_exporter import glb_exporter

def test_full_3d_pipeline():
    test_prompt = "A rusted medieval broadsword with a glowing blue sapphire in the hilt."
    output_dir = "tests/output"
    os.makedirs(output_dir, exist_ok=True)

    print("Step 1: Processing Prompt...")
    structured = prompt_engine.process(test_prompt)
    assert structured.object
    print(f"  Object: {structured.object}, Material: {structured.material}, Details: {structured.details}")

    print("Step 2: Generating 3D Geometry...")
    raw_path = os.path.join(output_dir, "sword_raw.obj")
    mesh, meta = text_to_3d_generator.generate(structured, raw_path)
    assert os.path.exists(raw_path)
    assert len(mesh.faces) > 0
    print(f"  Generated raw mesh: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")

    print("Step 3: Cleaning Mesh...")
    cleaned, clean_stats = mesh_cleaner.clean(mesh)
    assert len(cleaned.faces) > 0
    print(f"  Cleaned mesh: {clean_stats['cleaned_vertices']} vertices, {clean_stats['cleaned_faces']} faces")

    print("Step 4: Unwrapping UVs with xatlas...")
    unwrapped, uv_stats = uv_unwrapper.unwrap(cleaned)
    assert uv_stats["has_uv"] is True
    print(f"  Unwrapped UV atlas onto {len(unwrapped.vertices)} vertices")

    print("Step 5: Synthesizing PBR Textures...")
    tex_dir = os.path.join(output_dir, "textures")
    textures = texture_baker.generate_pbr_set(structured, tex_dir, resolution=512)
    for channel in ["basecolor", "roughness", "metallic", "normal", "emissive"]:
        assert os.path.exists(textures[channel]), f"Missing {channel} texture"
    print(f"  PBR texture maps generated at {tex_dir}")

    print("Step 6: Optimizing Mesh...")
    optimized, opt_stats = mesh_optimizer.optimize(unwrapped, target_polygon_budget=5000)
    print(f"  Optimized faces: {opt_stats['optimized_faces']} (reduction: {opt_stats['reduction_ratio']}%)")

    print("Step 7: Binding PBR Materials and Exporting GLB...")
    glb_path = os.path.join(output_dir, "test_sword.glb")
    export_stats = glb_exporter.export(optimized, textures, glb_path)
    assert os.path.exists(glb_path)
    assert export_stats["is_valid"] is True
    assert export_stats["verified_faces"] > 0
    print(f"  GLB export successful: {export_stats['file_size_bytes']} bytes ({export_stats['file_size_mb']} MB)")
    print(f"  Verified vertices: {export_stats['verified_vertices']}, faces: {export_stats['verified_faces']}")
    print(f"  Dimensions: {export_stats['bounding_box_dimensions']}")

    # Clean up test output
    shutil.rmtree(output_dir, ignore_errors=True)
    print("Full 3D pipeline verified successfully!")

if __name__ == "__main__":
    test_full_3d_pipeline()
