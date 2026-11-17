import sys
import os
import trimesh

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("backend"))

from ai_models.text_to_3d.preview_generator import PreviewGenerator

artifact_dir = r"C:\Users\windows\.gemini\antigravity\brain\64ef4193-7a70-417d-9b27-f29f773d54c4"
models = [
    "wooden_chair",
    "medieval_sword",
    "fantasy_treasure_chest",
    "metallic_robot",
    "stone_sculpture"
]

for name in models:
    cleaned_mesh_path = os.path.join("storage/processed_meshes", f"{name}_cleaned.obj")
    if os.path.exists(cleaned_mesh_path):
        mesh = trimesh.load(cleaned_mesh_path, process=False)
        out_img = os.path.join(artifact_dir, f"{name}_cleaned_preview.png")
        PreviewGenerator.generate_preview(mesh, out_img)
        print(f"Generated cleaned preview: {out_img}")
