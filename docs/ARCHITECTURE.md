# PolyGen Technical Architecture Specification

## 1. Architectural Overview

PolyGen is built as a modular, asynchronous, decoupled pipeline engineered to transform natural-language text descriptions into production-ready 3D game assets. The pipeline executes eight distinct stages, communicating real-time progression through a persistent WebSocket stream.

```
                      +-------------------+
                      |    User Prompt    |
                      +-------------------+
                                |
                                v
                +-------------------------------+
                |   FastAPI Orchestrator Layer  |
                +-------------------------------+
                                |
     +--------------------------+--------------------------+
     |                          |                          |
     v                          v                          v
[STAGE 1]                  [STAGE 2]                  [STAGE 3]
Prompt Decomposition       AI 3D Synthesis            Topology Repair
NLP Entity Extraction      Implicit Neural Field      Coincident Welding
Material & Style Parsing   Marching Cubes Surface     Normal Generation
     |                          |                          |
     +--------------------------+--------------------------+
                                |
     +--------------------------+--------------------------+
     |                          |                          |
     v                          v                          v
[STAGE 4]                  [STAGE 5]                  [STAGE 6]
UV Parameterization        PBR Texture Synthesis      Mesh Decimation
xatlas Conformal Atlas     BaseColor / Normal / PBR   QEM Simplification
Chart Boundary Mapping     Roughness / Emissive       Polygon Budgeting
     |                          |                          |
     +--------------------------+--------------------------+
                                |
     +--------------------------+--------------------------+
     |                          |                          |
     v                          v                          v
[STAGE 7]                  [STAGE 8]                  [CLIENT]
Material Assignment        Verification Pass          Interactive 3D View
glTF 2.0 Packaging         Reload GLB & Audit         Three.js / R3F Canvas
Binary GLB Assembly        Bounding Box & Polys       Direct GLB Download
```

---

## 2. Mathematical & Algorithmic Foundations

### 2.1 Conformal UV Parameterization (xatlas)
The system unwraps complex 3D meshes into a two-dimensional atlas using conformal energy minimization:

$$E_{\text{conformal}} = \frac{1}{2} \int_S \left( \|\nabla u\|^2 + \|\nabla v\|^2 \right) dA - \int_S \det(\nabla u, \nabla v) dA$$

where $(u, v)$ represent coordinates in the texture domain. This guarantees zero self-intersection among charts and minimizes area distortion across irregular triangles.

### 2.2 Quadric Error Metric (QEM) Decimation
To satisfy user-configured polygon budgets without distorting silhouette or UV boundaries, PolyGen applies Quadric Error Metric edge-collapse simplification.

For a vertex $v$, the geometric error quadric $Q$ is computed as the sum of squared distances to all incident planes $p = [a, b, c, d]^T$:

$$Q = \sum_{p \in \text{planes}(v)} p p^T$$

The cost of collapsing edge $(v_1, v_2)$ into candidate vertex $\bar{v}$ is:

$$\text{Cost}(\bar{v}) = \bar{v}^T (Q_1 + Q_2) \bar{v}$$

The optimal target point $\bar{v}$ is solved by:

$$\bar{v} = (Q_1 + Q_2)^{-1} \cdot \mathbf{0}$$

### 2.3 Tangent-Space Normal Map Derivation
Surface perturbation gradients $(\nabla_x, \nabla_y)$ derived from procedural luminance height fields are converted into orthonormal tangent-space normal vectors:

$$\mathbf{n} = \frac{[-k \cdot \nabla_x, -k \cdot \nabla_y, 1]}{\sqrt{(k \nabla_x)^2 + (k \nabla_y)^2 + 1}}$$

The encoded RGB vector in texture space is normalized to $[0, 255]$:

$$\text{RGB}_{\text{normal}} = \left\lfloor \frac{\mathbf{n} + 1}{2} \times 255 \right\rfloor$$

---

## 3. PBR Metallic-Roughness Shading Specification

PolyGen exports binary `glTF 2.0` (`.glb`) compliant with the Khronos PBR Metallic-Roughness workflow:

| Map Channel | Texture Format | Encoding / Bit Depth | Function |
| :--- | :--- | :--- | :--- |
| **BaseColor** | `basecolor.png` | sRGB, 8-bit per channel | Diffuse surface albedo / reflectance |
| **Metallic-Roughness** | Packed in GLB | Linear, Green=Rough, Blue=Metal | Conductive mask & microsurface scattering |
| **Normal** | `normal.png` | Linear RGB, 8-bit | Tangent-space surface detailing |
| **Emissive** | `emissive.png` | sRGB, 8-bit | Self-illumination (sapphires, runes, lasers) |

---

## 4. Hardware Management & Pluggable Backend

To accommodate environments with varying compute resources, the AI engine isolates model drivers behind an abstraction layer:
- **`local_shape`**: Runs OpenAI Shap-E in PyTorch CPU/CUDA mode. Weights are cached on high-capacity storage (`D:\shap_e_model_cache`).
- **`procedural`**: Generates high-fidelity volumetric surfaces (with complete PBR texturing and decimation) with sub-second execution latency, ideal for continuous testing, edge devices, and instant rendering.
- **`remote_gpu`**: Dispatches requests to remote CUDA instances running larger multi-view models (e.g. Hunyuan3D / TripoSR).

