# PolyGen Product Demonstration & Presentation Script

## Introduction (30 Seconds)

> *"Hello everyone. Today, 3D asset creation for games, spatial computing, and extended reality is bottlenecked by manual workflows: modeling, retopology, UV unwrapping, texturing, and engine optimization can take artists several days per asset.*
> 
> *Meet **PolyGen**: an AI-driven, end-to-end text-to-3D asset pipeline. PolyGen turns natural-language descriptions into game-ready, UV-unwrapped, PBR-textured 3D models in binary GLB format, ready for immediate drag-and-drop into Unreal Engine, Unity, and Blender."*

---

## Live Demonstration Walkthrough

### Step 1: Launching the Unified Service
Show the terminal starting the application:
```powershell
.\start_polygen.bat
```
Navigate to `http://127.0.0.1:8000`.

Highlight the modern dark charcoal dashboard inspired by Unreal Engine 5 and Blender.

---

### Step 2: Submitting a Natural Language Prompt
In the Generative 3D Studio, enter the prompt:
> **"A rusted medieval broadsword with a glowing blue sapphire in the hilt."**

Demonstrate the parameter controls:
- **Style Selector**: Set to *Medieval Fantasy*.
- **Quality Preset**: Set to *High (1024px PBR Maps)*.
- **Polygon Budget Slider**: Set to *10,000 Polygons*.

Click **GENERATE 3D MODEL**.

---

### Step 3: Real-Time 8-Stage Pipeline Observability
Point the audience to the **Generation Progress** panel:
- **Stage 1 (Prompt Understanding)**: NLP parses "rusted iron" for material, "medieval fantasy" for style, and detects the "blue sapphire" emissive cue.
- **Stage 2 (3D Mesh Generation)**: Generates 3D polygonal geometry and saves raw vertices.
- **Stage 3 (Topology Cleaning & UV Mapping)**: Removes duplicate vertices, culls non-manifold edges, and runs `xatlas` conformal parameterization.
- **Stage 4 (Texture Synthesis)**: Synthesizes five PBR maps: BaseColor, Roughness, Metallic, Normal, and Emissive.
- **Stage 5 (QEM Decimation)**: Simplifies geometry down to the user's exact polygon budget.
- **Stage 6 (Material Binding & GLB Export)**: Binds metallic-roughness channels and packs standard glTF 2.0 binary (`.glb`).
- **Stage 7 & 8 (Verification & Display)**: Verification pass verifies polygon counts, dimensions, and loads the model directly into the 3D viewport.

---

### Step 4: Interactive 3D Inspection
Once generated:
1. **PBR Texture Mode**: Rotate the broadsword with OrbitControls. Note how lighting glistens on the metallic blade and the blue sapphire emits glow.
2. **Clay Solid Mode**: Click *Clay Solid* to inspect the raw geometric silhouette.
3. **Wireframe Mode**: Click *Wireframe* to reveal clean edge topology and polygon distribution.
4. **Live Telemetry**: Point out the polygon count, vertex count, file size (MB), and bounding box dimensions in meters.

---

### Step 5: Asset Download & Game Engine Import
Click **Download GLB**.
Show how the exported file is self-contained:
- Open Blender $\to$ `File` $\to$ `Import` $\to$ `glTF 2.0 (.glb)`.
- The sword appears with correct scale, origin, materials, and embedded textures automatically linked into the Principled BSDF node!

---

### Step 6: Asset Library & Management
Click **Asset Library** in the navigation header:
- View all previously generated models.
- Demonstrate instant switching between assets.
- Show search filtering and asset deletion.

---

## Conclusion & Next Steps (30 Seconds)

> *"PolyGen eliminates hours of tedious 3D grunt work, empowering game development studios and indie developers to populate worlds rapidly with production-grade 3D assets.*
> 
> *Thank you, and we're ready to answer any questions."*

