import sys
import os
import shutil

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("backend"))
from processing.mesh_cleaner import mesh_cleaner

os.makedirs("storage/processed_meshes", exist_ok=True)
os.makedirs("storage/raw_meshes", exist_ok=True)

models = [
    "wooden_chair",
    "medieval_sword",
    "fantasy_treasure_chest",
    "metallic_robot",
    "stone_sculpture"
]

print("=" * 60)
print("POLYGEN: COPYING & RE-CLEANING TO storage/processed_meshes/")
print("=" * 60)

for name in models:
    src_raw = os.path.join("tests/output_part6", f"{name}_raw.obj")
    if os.path.exists(src_raw):
        shutil.copy(src_raw, os.path.join("storage/raw_meshes", f"{name}_raw.obj"))
        cleaned_path = os.path.join("storage/processed_meshes", f"{name}_cleaned.obj")
        cleaned_mesh, rep = mesh_cleaner.clean(src_raw, output_path=cleaned_path)
        print(f"[SUCCESS] {name}: {rep['original_vertex_count']} -> {rep['processed_vertex_count']} verts, "
              f"{rep['original_face_count']} -> {rep['processed_face_count']} faces | "
              f"watertight={rep['watertight_after']} | components={rep['connected_components']} | "
              f"time={rep['processing_duration_ms']}ms -> {cleaned_path}")

print("=" * 60)
print("All cleaned meshes persisted in storage/processed_meshes/")
