# PolyGen – Generative Text-to-3D Asset Pipeline

[![Python 3.10](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![Three.js](https://img.shields.io/badge/Three.js-r170-black.svg)](https://threejs.org/)
[![glTF 2.0](https://img.shields.io/badge/Format-glTF%202.0%20GLB-orange.svg)](https://www.khronos.org/gltf/)

**PolyGen** is an AI-powered text-to-3D generation platform that transforms natural-language descriptions into optimized, UV-unwrapped, PBR-textured, and downloadable 3D models ready for immediate import into **Blender**, **Unreal Engine**, and **Unity**.

---

## 1. System Architecture

```
USER PROMPT ("A rusted medieval broadsword with a glowing blue sapphire in the hilt.")
    │
    ▼
REACT THREE FIBER FRONTEND (Interactive 3D Viewer, Controls, Library)
    │  (REST / WebSockets)
    ▼
FASTAPI BACKEND & ORCHESTRATOR
    │
    ├── [STAGE 1] Prompt Understanding Engine (NLP Entity & Attribute Extraction)
    │             ↳ Material, Style, Surface Details, Emissive Signals, Polygon Budget
    │
    ├── [STAGE 2] 3D Mesh Generation Engine (Shap-E Diffusion / Procedural SDF)
    │             ↳ Raw Implicit Surfaces & Polygonal Meshes (OBJ/PLY)
    │
    ├── [STAGE 3] Mesh Cleaning & Preprocessing (Trimesh & Topology Repair)
    │             ↳ Coincident vertex welding, degenerate face culling, normal calculation
    │
    ├── [STAGE 4] Automated UV Parameterization (xatlas)
    │             ↳ Conformal parameterization, non-overlapping UV atlas charts
    │
    ├── [STAGE 5] PBR Texture Synthesis & Baking
    │             ↳ BaseColor, Roughness, Metallic, Normal, and Emissive maps
    │
    ├── [STAGE 6] Mesh Optimization & Decimation (Quadric Error Metrics)
    │             ↳ Target polygon budgeting (e.g. 10k polys) preserving UV seams
    │
    ├── [STAGE 7] Material Assignment & Binary GLB Packaging
    │             ↳ PBR Metallic-Roughness binding, buffer packing, file verification
    │
    ▼
INTERACTIVE 3D WEB VIEWER & ASSET REPOSITORY
    │
    ├── PBR Textured Rendering (HDRI Environment Lighting)
    ├── Clay Solid Mode
    ├── Topology Wireframe Overlay
    ├── Geometry Stats (Triangles, Vertices, Bounds in meters)
    └── Download GLB for Blender / Unreal Engine / Unity
```

---

## 2. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 19, Vite, TypeScript, Tailwind CSS, Three.js, React Three Fiber, React Three Drei, Zustand, Axios, Lucide Icons |
| **Backend API** | Python 3.10, FastAPI, Pydantic v2, SQLAlchemy 2.0, aiosqlite / PostgreSQL, WebSockets, JWT Authentication |
| **Generative AI** | PyTorch, OpenAI Shap-E, CLIP, Volumetric Parametric Synthesizer |
| **3D Engineering** | Trimesh, xatlas, Pillow, NumPy, SciPy |
| **Export Format** | glTF 2.0 Binary (`.glb`) with embedded PBR textures |

---

## 3. Directory Layout

```
PolyGen/
├── frontend/                     # React + Vite + Three.js application
│   ├── src/
│   │   ├── components/           # 3D Viewport, Prompt Studio, Progress, Cards
│   │   │   ├── ModelViewer.tsx   # Three.js / R3F Canvas with PBR, Wireframe, Solid modes
│   │   │   ├── PromptInput.tsx   # Parameter controls (Style, Quality, Budget)
│   │   │   ├── GenerationProgress.tsx # Real-time 8-stage progress tracker
│   │   │   ├── AssetCard.tsx     # Asset gallery cards
│   │   │   ├── Navbar.tsx        # Navigation and system telemetry
│   │   │   └── AuthModal.tsx     # JWT Authentication modal
│   │   ├── pages/                # Generate, AssetLibrary, Dashboard
│   │   ├── services/             # Axios client and WebSocket stream manager
│   │   └── store/                # Zustand global state store
│   └── package.json
│
├── backend/                      # FastAPI asynchronous service
│   ├── app/
│   │   ├── main.py               # Application entrypoint & CORS
│   │   ├── config.py             # Pydantic BaseSettings
│   │   ├── api/                  # Endpoints (auth, generate, assets)
│   │   ├── services/             # Pipeline orchestrator & prompt engine
│   │   ├── models/               # SQLAlchemy DB entities (User, Job, Asset)
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   └── core/                 # Security, database, WebSocket connection hub
│   ├── requirements.txt
│   └── Dockerfile
│
├── ai_models/                    # Generative 3D inference engines
│   ├── text_to_3d/               # Shap-E & procedural geometry generators
│   └── ...
│
├── processing/                   # 3D Mesh and texture pipeline modules
│   ├── mesh_cleaner.py           # Module 4: Degenerate face removal & normal recalculation
│   ├── uv_unwrapper.py           # Module 3: xatlas conformal UV parameterization
│   ├── texture_baker.py          # Module 3 & 5: PBR map synthesis (Base, Rough, Metal, Normal, Emissive)
│   ├── mesh_optimizer.py         # Module 4: Quadric Error Metric (QEM) decimation
│   └── glb_exporter.py           # Module 6: glTF 2.0 binary packaging & verification
│
├── storage/                      # Asset persistence hierarchy
│   ├── raw/                      # Raw OBJ/PLY geometries
│   ├── processed/                # Cleaned intermediate meshes
│   ├── textures/                 # PBR texture sets per job
│   ├── exports/                  # Downloadable .glb files
│   └── previews/                 # Visual asset previews
│
├── tests/                        # Comprehensive test & benchmark suite
│   ├── test_prompt_engine.py     # Prompt parsing unit tests
│   ├── test_3d_pipeline.py       # Full geometry & export pipeline test
│   ├── test_api.py               # REST API & WebSocket integration tests
│   └── test_benchmark_all_scenarios.py # 5 canonical benchmark scenarios
│
├── docker-compose.yml            # Multi-container orchestration (API, DB, Redis, UI)
└── README.md
```

---

## 4. Benchmark Verification Results

All 5 canonical scenarios specified in the master specification were executed and verified through the end-to-end pipeline:

| Scenario | Generated Asset | Final Faces | Vertices | Size (MB) | Pipeline Latency | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Wooden Chair** | Rustic Oak Chair | 536 | 600 | 3.33 MB | 1.96s | **PASSED & VERIFIED** |
| **2. Medieval Broadsword** | Broadsword + Sapphire | 856 | 699 | 3.40 MB | 2.31s | **PASSED & VERIFIED** |
| **3. Treasure Chest** | Pirate Brass Chest | 120 | 154 | 3.45 MB | 2.02s | **PASSED & VERIFIED** |
| **4. Metallic Robot** | Battle Robot + Visor | 548 | 624 | 3.84 MB | 2.10s | **PASSED & VERIFIED** |
| **5. Stone Sculpture** | Ancient Carved Monolith | 5,120 | 2,802 | 3.55 MB | 2.72s | **PASSED & VERIFIED** |

*All exported `.glb` files conform to glTF 2.0 specifications with valid vertex buffer views, UV coordinates, and embedded PBR metallic-roughness materials.*

---

## 5. Quickstart & Installation

### Prerequisites
- **Python 3.10**
- **Node.js v18+** (Detected: v24.12.0)
- **Git**

### Step 1: Clone and Set Up Virtual Environment

```bash
git clone https://github.com/your-org/PolyGen.git
cd PolyGen

# Create isolated Python 3.10 venv
py -3.10 -m venv venv

# Activate venv (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Upgrade pip & install backend dependencies
python -m pip install --upgrade pip setuptools wheel
pip install -r backend/requirements.txt
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install email-validator
pip install -e ai_models/text_to_3d/shap_e
```

### Step 2: Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### Step 3: Run the Test & Benchmark Suites

```bash
# 1. Prompt understanding engine unit tests
.\venv\Scripts\python.exe tests/test_prompt_engine.py

# 2. 3D geometry, xatlas UV, PBR texture, decimation, and GLB export test
.\venv\Scripts\python.exe tests/test_3d_pipeline.py

# 3. FastAPI authentication and generation endpoints integration test
.\venv\Scripts\python.exe tests/test_api.py

# 4. Full 5-scenario benchmark suite
.\venv\Scripts\python.exe tests/test_benchmark_all_scenarios.py
```

### Step 4: Launch the Applications

**Start the FastAPI Backend:**
```bash
.\venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
API Documentation available at: `http://127.0.0.1:8000/docs`

**Start the React Three.js Frontend:**
```bash
cd frontend
npm run dev
```
Interactive Viewport available at: `http://localhost:5173`

---

## 6. REST API Reference

### Authentication
- `POST /api/auth/register` – Register a new user account.
- `POST /api/auth/login` – Authenticate with username/password, returns JWT token.
- `GET /api/auth/me` – Retrieve current user profile.

### Generation Engine
- `POST /api/generate` – Submit a text prompt and generation parameters. Returns `job_id` and status `pending`.
- `GET /api/jobs/{job_id}` – Query job progression, current stage, and output asset ID.
- `WS /ws/jobs/{job_id}` – Real-time WebSocket connection streaming 8-stage progress events.

### Asset Repository
- `GET /api/assets` – List all generated 3D assets with metadata and polygon counts.
- `GET /api/assets/{asset_id}` – Query specific asset properties.
- `GET /api/assets/{asset_id}/download` – Stream binary `.glb` model.
- `DELETE /api/assets/{asset_id}` – Delete asset and associated disk buffers.

---

## 7. Engine Backends & Hardware Deployment

PolyGen features a pluggable AI backend configured via `.env` (`AI_BACKEND`):
- `local_shape`: Direct local inference using OpenAI's Shap-E model on PyTorch (CPU or CUDA).
- `procedural`: High-speed parametric volumetric surface synthesis with full PBR texturing and decimation (ideal for fast CI/CD and low-compute devices).
- `remote_gpu`: Connects to a dedicated high-end GPU cluster running Hunyuan3D or TripoSR.

---

## 8. License

Apache 2.0 License. Designed for production and gaming studio workflows.

#   P o l y g e n  
 