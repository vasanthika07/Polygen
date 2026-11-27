"""
PolyGen – Interactive Gradio Multimodal 3D Web Application
Provides real-time Image-to-3D, Multimodal Fusion, and 3D Model3D Viewport inspection.
"""

import os
import sys
import time
import logging
from PIL import Image

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import gradio as gr
import trimesh

from ai_models.multimodal.multimodal_analyzer import multimodal_analyzer
from ai_models.multimodal.multimodal_generator import multimodal_generator
from processing.pbr_material_system import pbr_material_system
from processing.mesh_optimizer import MeshOptimizer
from processing.glb_exporter import glb_exporter, ExportProfile
from dashboard.three_background import get_3d_background_script
from app.config import settings

logger = logging.getLogger("polygen_gradio")

# Custom Dark Theme CSS
CUSTOM_CSS = """
body {
    background-color: #070a13 !important;
}
.gradio-container {
    background: radial-gradient(circle at 50% 20%, rgba(13, 18, 31, 0.65) 0%, rgba(6, 9, 14, 0.90) 100%) !important;
    position: relative;
    z-index: 1;
    font-family: 'Space Grotesk', -apple-system, sans-serif !important;
    color: #f1f5f9 !important;
}
#polygen-ambient-3d-canvas {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: 0;
    pointer-events: none;
    opacity: 0.55;
}
.header-box {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.65) 0%, rgba(15, 23, 42, 0.75) 100%);
    border: 1px solid rgba(59, 130, 246, 0.35);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 20px;
    text-align: center;
    backdrop-filter: blur(12px);
}
.header-title {
    font-size: 2.2rem;
    font-weight: 700;
    background: linear-gradient(90deg, #60a5fa 0%, #c084fc 50%, #f472b6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}
.stat-pill {
    display: inline-block;
    padding: 4px 12px;
    margin: 0 4px;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 600;
    background: rgba(59, 130, 246, 0.15);
    color: #60a5fa;
    border: 1px solid rgba(59, 130, 246, 0.3);
}
"""

def generate_multimodal_studio(
    image,
    prompt: str,
    style: str,
    budget: int,
    quality: str,
    progress=gr.Progress()
):
    """Executes Multimodal 3D Generation pipeline."""
    if not prompt and image is None:
        return None, None, {"error": "Please provide either a text prompt or an image input."}, "⚠️ Provide a text prompt or upload an image."

    progress(0.1, desc="Fusing Multimodal Modalities...")
    start_time = time.time()
    
    progress(0.3, desc="Synthesizing 3D Geometry & Displacements...")
    res = multimodal_generator.generate_multimodal_asset(
        text_prompt=prompt if prompt and prompt.strip() else None,
        image_input=image,
        style_override=style,
        polygon_budget=int(budget),
        quality=quality,
    )
    
    progress(0.8, desc="Optimizing & Packaging glTF 2.0 Binary...")
    glb_path = res["glb_path"]
    dur = round(time.time() - start_time, 2)

    telemetry = {
        "job_id": res["job_id"],
        "fused_prompt": res["fused_prompt"],
        "polygon_count": res["polygon_count"],
        "vertex_count": res["vertex_count"],
        "file_size_mb": res["file_size_mb"],
        "duration_seconds": dur,
        "uv_charts": res["uv_charts"],
        "pbr_material": res["pbr_material"],
        "is_valid_glb": res["is_valid_glb"]
    }

    status_msg = f"### ✅ Generation Completed in {dur}s!\n" \
                 f"• **Polygons:** `{res['polygon_count']:,} faces` | **Size:** `{res['file_size_mb']} MB`\n" \
                 f"• **PBR Material:** `{res['pbr_material']}` | **Format:** `Khronos glTF 2.0 (GLB)`"

    return glb_path, glb_path, telemetry, status_msg


def optimize_uploaded_mesh(file_obj, target_faces: int):
    """Optimizes uploaded 3D asset using Quadric Error Metric decimation."""
    if file_obj is None:
        return None, None, "Please upload a 3D mesh file."

    in_path = file_obj.name
    loaded = trimesh.load(in_path, force="mesh")
    initial_faces = len(loaded.faces)

    opt_mesh, report = MeshOptimizer.optimize(
        mesh=loaded,
        target_polygon_budget=target_faces,
        normalize_bounds=True,
    )

    out_name = f"optimized_{os.path.basename(in_path)}"
    out_path = os.path.join(settings.STORAGE_EXPORTS_DIR, out_name)
    opt_mesh.export(out_path)

    summary = f"### ⚡ Optimization Complete!\n" \
              f"• Initial Faces: `{initial_faces:,}` &rarr; Optimized: `{len(opt_mesh.faces):,}`\n" \
              f"• Reduction: `-{report.get('reduction_percentage', 0)}%`"

    return out_path, out_path, summary


def inspect_pbr_preset(preset_key: str):
    """Returns details and parameters for selected PBR material preset."""
    preset = pbr_material_system.PRESETS.get(preset_key, {})
    desc = preset.get("description", "Standard physical PBR material.")
    params = {
        "Name": preset.get("name"),
        "Material Class": preset.get("material_class"),
        "Metallic Factor": preset.get("metallic_factor"),
        "Roughness Factor": preset.get("roughness_factor"),
        "Normal Scale": preset.get("normal_scale"),
        "Occlusion Strength": preset.get("occlusion_strength"),
        "Emissive Factor": preset.get("emissive_factor"),
        "Emissive Multiplier": preset.get("emissive_intensity"),
        "Alpha Mode": preset.get("alpha_mode"),
        "Double Sided": preset.get("double_sided"),
    }
    return f"**Description:** {desc}", params


# Build Gradio UI
with gr.Blocks(title="PolyGen Multimodal 3D Studio") as demo:
    gr.HTML("""
    <div class="header-box">
        <h1 class="header-title">🔮 PolyGen Multimodal 3D Studio</h1>
        <p style="color: #94a3b8; margin-top: 6px; font-size: 1.05rem;">
            Next-Generation Text-to-3D, Image-to-3D, and PBR Asset Optimization Engine
        </p>
        <div style="margin-top: 12px;">
            <span class="stat-pill">✨ Multimodal Fusion</span>
            <span class="stat-pill">⚡ Real-time QEM Decimation</span>
            <span class="stat-pill">📦 Khronos glTF 2.0 (GLB)</span>
        </div>
    </div>
    """)

    with gr.Tabs():
        # TAB 1: MULTIMODAL 3D STUDIO
        with gr.Tab("🎨 Multimodal 3D Studio"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 🎛️ Input Controls")
                    mm_image = gr.Image(label="Reference Image / Concept Art (Optional)", type="pil")
                    mm_prompt = gr.Textbox(
                        label="Natural Language Prompt",
                        placeholder="A glowing blue sapphire gemstone with ornate gold trim...",
                        value="A glowing sapphire crystal gemstone with sharp facets",
                        lines=3
                    )
                    
                    with gr.Row():
                        mm_style = gr.Dropdown(
                            choices=["realistic", "fantasy", "sci-fi", "stylized", "cyberpunk", "low-poly"],
                            value="fantasy",
                            label="Artistic Style"
                        )
                        mm_quality = gr.Radio(
                            choices=["standard", "high", "ultra"],
                            value="high",
                            label="Texture Quality"
                        )
                    
                    mm_budget = gr.Slider(
                        minimum=1000,
                        maximum=30000,
                        value=4000,
                        step=500,
                        label="Target Polygon Budget (Faces)"
                    )
                    
                    generate_btn = gr.Button("🚀 Synthesize 3D Model", variant="primary", size="lg")

                with gr.Column(scale=1):
                    gr.Markdown("### 🪐 Interactive 3D Model Viewport")
                    model_viewer = gr.Model3D(label="3D glTF 2.0 / GLB Canvas", clear_color=[0.05, 0.07, 0.12, 1.0])
                    status_display = gr.Markdown("Ready to synthesize.")
                    
                    with gr.Row():
                        download_file = gr.File(label="Download Asset (.glb)")
                        telemetry_json = gr.JSON(label="Pipeline Telemetry")

            generate_btn.click(
                fn=generate_multimodal_studio,
                inputs=[mm_image, mm_prompt, mm_style, mm_budget, mm_quality],
                outputs=[model_viewer, download_file, telemetry_json, status_display]
            )

        # TAB 2: IMAGE-TO-3D RAPID CONVERTER
        with gr.Tab("🖼️ Image-to-3D Converter"):
            gr.Markdown("### Rapid Single-View 2D Image to 3D Textured Asset Conversion")
            with gr.Row():
                with gr.Column(scale=1):
                    i2m_image = gr.Image(label="Drop Concept Art or Photo", type="pil")
                    i2m_budget = gr.Slider(minimum=1000, maximum=20000, value=3500, step=500, label="Polygon Budget")
                    i2m_btn = gr.Button("⚡ Convert Image to 3D", variant="primary")
                with gr.Column(scale=1):
                    i2m_viewer = gr.Model3D(label="Synthesized 3D Model")
                    i2m_status = gr.Markdown()

            i2m_btn.click(
                fn=lambda img, bud: generate_multimodal_studio(img, "", "realistic", bud, "high")[:2] + (generate_multimodal_studio(img, "", "realistic", bud, "high")[3],),
                inputs=[i2m_image, i2m_budget],
                outputs=[i2m_viewer, gr.File(), i2m_status]
            )

        # TAB 3: MESH OPTIMIZER & DECIMATOR
        with gr.Tab("📐 Mesh Decimation Studio"):
            gr.Markdown("### Quadric Error Metric (QEM) 3D Mesh Decimator")
            with gr.Row():
                with gr.Column(scale=1):
                    mesh_upload = gr.File(label="Upload 3D Mesh (OBJ, PLY, GLB)")
                    mesh_target = gr.Slider(minimum=500, maximum=30000, value=2500, step=500, label="Target Faces")
                    opt_btn = gr.Button("⚡ Decimate & Optimize Mesh", variant="primary")
                with gr.Column(scale=1):
                    opt_viewer = gr.Model3D(label="Optimized Mesh Viewport")
                    opt_download = gr.File(label="Download Optimized Asset")
                    opt_summary = gr.Markdown()

            opt_btn.click(
                fn=optimize_uploaded_mesh,
                inputs=[mesh_upload, mesh_target],
                outputs=[opt_viewer, opt_download, opt_summary]
            )

        # TAB 4: PBR MATERIAL EXPLORER
        with gr.Tab("🧪 PBR Material Explorer"):
            gr.Markdown("### Khronos glTF 2.0 Physically Based Rendering Material Explorer")
            preset_picker = gr.Dropdown(
                choices=list(pbr_material_system.PRESETS.keys()),
                value="glowing_sapphire",
                label="Select PBR Material Preset"
            )
            pbr_desc = gr.Markdown()
            pbr_params_json = gr.JSON()

            preset_picker.change(
                fn=inspect_pbr_preset,
                inputs=[preset_picker],
                outputs=[pbr_desc, pbr_params_json]
            )

    gr.HTML("<div style='text-align: center; color: #64748b; margin-top: 30px;'>PolyGen Generative Text-to-3D & Multimodal Platform • Khronos glTF 2.0 Standard</div>")

if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        theme=gr.themes.Soft(primary_hue="blue", neutral_hue="slate"),
        css=CUSTOM_CSS,
        head=get_3d_background_script()
    )
