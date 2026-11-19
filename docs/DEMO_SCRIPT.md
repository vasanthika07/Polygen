# PolyGen Product Demonstration & Presentation Script

## Introduction (30 Seconds)

> *"Welcome to the demonstration of **PolyGen**, an automated AI-driven Text-to-3D asset pipeline. Traditional 3D content creation requires hours or days of manual modeling, retopology, UV mapping, texture baking, and shader configuration.*
> 
> *PolyGen turns natural language descriptions into game-ready, UV-unwrapped, PBR-textured 3D models in binary GLB format in under 5 seconds, ready for immediate drag-and-drop into Unreal Engine 5, Unity, and Blender."*

---

## Live Demonstration Flow

### Step 1: Authentication & Workspace Initialization
1. Open browser at `http://localhost:5173` (or production port `80`).
2. Log in with user credentials or demonstrate quick registration.
3. Show the Unreal Engine 5 dark workspace aesthetic with real-time HUD telemetry.

---

### Step 2: Prompt Input & Multi-Parameter Configuration
1. In the Generative 3D Studio, enter the prompt:
   > **"A rusted medieval broadsword with a glowing blue sapphire in the hilt."**
2. Configure parameters:
   - **Style**: *Fantasy*
   - **Quality**: *High Quality (1024px PBR Maps)*
   - **Polygon Budget**: *5,000 Polygons*
   - **Target Format**: *glTF 2.0 Binary (GLB)*
3. Click **GENERATE 3D ASSET**.

---

### Step 3: Real-Time 9-Stage Progress Tracking
Show the animated progress bar and live stage checklist receiving WebSocket telemetry updates:
1. **Prompt Analysis (10%)**: Deconstructing natural-language semantics, materials, and geometry.
2. **3D Generation (25% &rarr; 35%)**: AI neural synthesis & surface polygon extraction.
3. **Mesh Processing (45%)**: Validating topology, welding coincident vertices, repairing non-manifold edges.
4. **UV Mapping (55%)**: Parameterizing non-overlapping UV atlas charts via xatlas.
5. **Texture Generation (70%)**: Synthesizing PBR diffuse, roughness, metallic, normal, and emissive channels.
6. **PBR Material Creation (80%)**: Compiling glTF 2.0 Cook-Torrance physical material definitions.
7. **Mesh Optimization (88%)**: Decimating mesh using Quadric Error Metric (QEM) to match polygon budget.
8. **GLB Export (95%)**: Packaging binary container, embedding textures, and rendering thumbnail.
9. **Completed (100%)**: Final validation pass complete; automatically loads in interactive 3D viewer.

---

### Step 4: Interactive Three.js 3D Viewer Inspection
Demonstrate the 16 interactive viewport features:
1. **OrbitControls**: Rotate, pan, and zoom around the generated broadsword.
2. **Camera Reset / Framing**: Frame asset in camera view.
3. **Lighting & Shadows**: Studio three-point lighting with dynamic contact shadow ground plane.
4. **Shading Modes**:
   - *PBR Textured* (Full physical rendering)
   - *Wireframe Overlay* (Inspect topological edge loops)
   - *Base Color Only*
   - *Normals Preview* (Inspect tangent vectors)
   - *Roughness / Metallic Heatmaps*
5. **Telemetry HUD**: Inspect vertex count (2,858), polygon count (4,364), file size (1.33 MB), and bounding box dimensions.

---

### Step 5: Asset Download & Engine Import
1. In the viewer action bar, select the export profile:
   - *Standard GLB (1024px)*
   - *High-Quality GLB (2048px)*
   - *Optimized GLB (512px)*
2. Click **Download GLB**.
3. Verify downloaded file integrity in Blender or Unreal Engine.

---

### Step 6: Asset Library & Generation History Audit
1. Navigate to **Asset Library**:
   - Filter assets by date: *Today*, *This Week*, *This Month*.
   - Sort by: *Newest*, *Polygon Count (Desc/Asc)*, *File Size*.
   - Search by keyword: `"sword"`, `"sapphire"`.
2. Navigate to **Generation History**:
   - Review complete audit trail of prompt, duration, selected settings, and status badges.
   - Expand failure diagnostic drawers to show error isolation and retry options.
