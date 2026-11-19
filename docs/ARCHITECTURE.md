# PolyGen Technical Architecture & System Specification

## 1. Executive Architectural Overview

PolyGen is an enterprise-grade Generative Text-to-3D pipeline designed to synthesize production-ready 3D game assets from natural language. It unifies neural implicit geometry extraction, topological repairing, conformal UV parameterization, PBR texture synthesis, quadric mesh decimation, and binary glTF 2.0 (GLB) packaging into an asynchronous, observable microservices architecture.

```
+---------------------------------------------------------------------------------------+
|                                    REACT 19 FRONTEND                                  |
|   PromptInput -> GenerationProgress -> ModelViewer (R3F/Three.js) -> AssetLibrary     |
+---------------------------------------------------------------------------------------+
                                           |  ^ (REST + WebSockets / HTTP Polling)
                                           v  |
+---------------------------------------------------------------------------------------+
|                              FASTAPI ORCHESTRATION LAYER                              |
|   Auth (/api/auth)  |  Jobs (/api/jobs)  |  Assets (/api/assets)  |  Optimizer/PBR    |
+---------------------------------------------------------------------------------------+
        |                                                       |
        v                                                       v
+-------------------------------+               +-------------------------------+
|     ASYNC CELERY / REDIS      |               |     PERSISTENCE / STORAGE     |
|   Distributed Task Broker     |               |  PostgreSQL 15 (Metadata/Auth)|
|   Optional In-Process Runner  |               |  Local / S3 Binary Assets     |
+-------------------------------+               +-------------------------------+
                                |
                                v
+---------------------------------------------------------------------------------------+
|                            THE 9-STAGE PIPELINE ENGINE                                |
|                                                                                       |
|  [Stage 1] Prompt Analysis     : NLP semantic deconstruction & material lexicons      |
|  [Stage 2] 3D Generation       : Implicit SDF / Shap-E neural volumetric generation    |
|  [Stage 3] Mesh Processing     : Topology repair, normal recalculation, manifold check|
|  [Stage 4] UV Mapping          : xatlas conformal parameterization & non-overlapping |
|  [Stage 5] Texture Generation  : PBR Diffuse, Roughness, Metallic, Normal, Emissive   |
|  [Stage 6] PBR Material Binding: glTF 2.0 Cook-Torrance physical material compiling   |
|  [Stage 7] Mesh Optimization   : Quadric Error Metric (QEM) polygon decimation       |
|  [Stage 8] GLB Export          : glTF 2.0 binary container packaging & 3D thumbnail   |
|  [Stage 9] Completed           : Verification pass, DB indexing & asset library ready |
+---------------------------------------------------------------------------------------+
```

---

## 2. Core Subsystems

### 2.1 Prompt Understanding Engine (`app.services.prompt_engine`)
- **Semantic Lexicon**: Parses natural language input across 24 object categories into physical attributes: primary shape, symmetry, materials, colors, lighting, surface details, and target polygon budget.
- **Model-Specific Prompt Synthesis**: Compiles specialized prompts tailored for Shap-E (`shap_e`), Hunyuan3D (`hunyuan3d`), TripoSR (`triposr`), and Stable Diffusion PBR map generation.

### 2.2 Text-to-3D Geometry Engine (`ai_models.text_to_3d`)
- **Neural & Procedural Dual-Mode**:
  - `CUDA` Hardware: Shap-E neural latent diffusion model (`shap-e-text300M`) with timeout and GPU memory boundaries.
  - `CPU` Hardware / Fallback: Deterministic procedural volumetric Signed Distance Field (SDF) synthesizer with Marching Cubes surface extraction.
- **Fail-Safe Mechanism**: Automatic fallback to procedural geometry on GPU out-of-memory or model download failures.

### 2.3 Mesh Cleaning & Topology Validation (`processing.mesh_cleaner`)
- **Non-Manifold Detection**: Identifies edges shared by &gt;2 faces and topological holes.
- **Degenerate Face Elimination**: Strips zero-area and collapsed triangles.
- **Duplicate Vertex Merging**: Coincident vertex welding within spatial epsilon ($10^{-5}$).
- **Normal Recalculation**: Recomputes outward face and vertex surface normals with winding consistency verification.

### 2.4 Automatic UV Unwrapping (`processing.uv_unwrapper`)
- **Engine**: Wrapped `xatlas` library for conformal surface charting and atlas packing.
- **Seam Optimization**: Dihedral angle and normal deviation weighting to minimize visible UV seams.
- **Overlap Auditor**: 2D AABB and triangle intersection testing to guarantee 0 overlapping charts.
- **Resilience Fallback**: Procedural spherical/box parameterization fallback if pathological topology causes atlas failure.

### 2.5 Physically Based Rendering (PBR) Engine (`processing.pbr_material_system`)
- **glTF 2.0 Metallic-Roughness Model**:
  - `BaseColor` (sRGB diffuse albedo)
  - `MetallicRoughness` (Green channel: Roughness; Blue channel: Metallic)
  - `Normal` (Tangent-space normal vectors derived via Gram-Schmidt orthonormalization)
  - `Ambient Occlusion` (Red channel of ORM map)
  - `Emissive` (Linear RGB emissive color & intensity multiplier)
- **Presets**: Rusted Broadsword, Glowing Sapphire, Carved Wood, Granite Stone, Translucent Glass, Polished Gold.

### 2.6 Mesh Optimization Engine (`processing.mesh_optimizer`)
- **Quadric Error Metric (QEM)**: Surface-preserving polygon reduction targeting user-defined budgets (Low: 3,000, Medium: 10,000, High: 35,000, or Custom).
- **Attribute Preservation**: Maintains UV atlas coordinates (`TEXCOORD_0`) and material boundaries across decimated topologies using nearest-neighbor KD-tree interpolation.

### 2.7 glTF 2.0 GLB Exporter (`processing.glb_exporter`)
- **Profiles**:
  - `standard`: 1024x1024 textures, optimal compression.
  - `high_quality`: 2048x2048 textures, lossless packing.
  - `optimized`: 512x512 textures, minimal transmission payload.
- **Binary Structure**: Validates 12-byte header (`0x46546C67`, version 2), structured JSON chunk, and aligned 4-byte binary buffer chunk.

---

## 3. Real-Time Telemetry & Progress Architecture

- **Primary Transport**: Bidirectional WebSocket connection (`/ws/jobs/{job_id}`).
- **Event Payload**:
```json
{
  "job_id": "job_32af37896e21",
  "stage": "mesh_processing",
  "progress": 45,
  "message": "Validating geometry, repairing non-manifold topology and recalculating normals",
  "data": { "raw_faces": 4364, "raw_vertices": 2200 },
  "timestamp": "2026-11-19T14:50:00Z"
}
```
- **Automatic Polling Fallback**: The client `JobWebSocket` service automatically detects WebSocket connection failures, network disconnects, or proxy blocks, seamlessly falling back to periodic `GET /api/jobs/{job_id}` polling every 1,500ms without interrupting the user experience.

---

## 4. Security Architecture

1. **Password Storage**: Passwords hashed using bcrypt with salt rounds = 12.
2. **Session Authentication**: JWT access tokens signed with HMAC-SHA256 (`HS256`) and configurable expiration.
3. **Multi-Tenant Ownership Isolation**: Strict row-level tenant validation on all job and asset endpoints (`job.user_id == current_user.id`). Unauthorized access returns `HTTP 403 Forbidden`.
4. **Download Security**: File delivery strictly validates asset ownership and verifies absolute paths within designated export storage to eliminate directory traversal risks (`../`).
5. **CORS Governance**: Configured via strict whitelist origins in settings (`settings.CORS_ORIGINS`).
