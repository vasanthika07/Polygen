# PolyGen – Generative Text-to-3D Asset Pipeline

[![Python 3.10](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![Three.js](https://img.shields.io/badge/Three.js-r170-black.svg)](https://threejs.org/)
[![glTF 2.0](https://img.shields.io/badge/Format-glTF%202.0%20GLB-orange.svg)](https://www.khronos.org/gltf/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**PolyGen** is an enterprise-grade, end-to-end AI platform that transforms natural-language text prompts into production-ready, UV-unwrapped, PBR-textured, and decimated 3D assets in binary **glTF 2.0 (GLB)** format. Generated assets are immediately compatible with **Blender**, **Unreal Engine 5**, **Unity**, and modern WebGL/WebGPU engines.

---

## Architecture Overview

```
USER PROMPT ("A rusted medieval broadsword with a glowing blue sapphire in the hilt.")
    │
    ▼
REACT 19 FRONTEND (Interactive Three.js / R3F Viewport, Asset Library, History)
    │  ▲  (RESTful APIs + WebSocket Streaming with Polling Fallback)
    ▼  │
FASTAPI BACKEND & ORCHESTRATOR
    │
    ├── [STAGE 1] Prompt Analysis      : NLP attribute extraction & material decomposition
    ├── [STAGE 2] 3D Generation        : Implicit SDF / Shap-E neural volumetric generation
    ├── [STAGE 3] Mesh Processing      : Topology repair, normal recalculation, manifold check
    ├── [STAGE 4] UV Mapping           : xatlas conformal parameterization & non-overlapping atlas
    ├── [STAGE 5] Texture Generation   : Synthesizes PBR Albedo, Roughness, Metallic, Normal, Emissive
    ├── [STAGE 6] PBR Material Binding : Cook-Torrance physical material compile & glTF 2.0 mapping
    ├── [STAGE 7] Mesh Optimization    : Quadric Error Metric (QEM) decimation to target budget
    ├── [STAGE 8] GLB Export           : Binary packaging, texture embedding & 3D thumbnail rendering
    └── [STAGE 9] Completed            : Verification pass, database persistence & library indexing
```

---

## Key Features

1. **Complete Prompt-to-Asset Pipeline**: Converts raw text descriptions into fully realized 3D models with geometry, UVs, and PBR textures in ~4.5 seconds.
2. **Real-Time Progress & Observability**: Streams live pipeline stage updates via WebSockets (`/ws/jobs/{id}`) with automated HTTP polling fallback.
3. **Automated UV Parameterization**: Wrapped `xatlas` charting with seam optimization, zero overlaps, and texel padding scaling.
4. **glTF 2.0 Physically Based Rendering**: Standardized metallic-roughness workflow supporting BaseColor, Roughness, Metallic, Normal, Ambient Occlusion, and Emissive channels.
5. **Budget-Constrained Decimation**: Quadric Error Metric (QEM) decimation with strict preservation of UV atlas coordinates and material assignments.
6. **Interactive Three.js 3D Viewport**: Studio 3-point lighting, contact shadows, wireframe overlay, normal/roughness heatmaps, and geometry telemetry HUD.
7. **Asset Library & Generation History**: Multi-tenant asset management with keyword search, date filtering, sorting options, and failure diagnostic drawers.
8. **Enterprise Multi-Tenant Security**: Bcrypt password hashing, JWT expiration, row-level ownership enforcement (HTTP 403), and path-traversal prevention.

---

## Empirical Benchmark Performance

*Benchmarks measured on 12-core host architecture (PyTorch 2.14.1+cpu) with automated profiling:*

| Asset / Prompt Scenario | Polygon Budget | Faces (Raw &rarr; Final) | GLB File Size | Total Pipeline Time | Viewport Parse |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Rusted Medieval Broadsword** | 5,000 | 4,364 &rarr; 4,364 | 1.33 MB | **4.53 s** | 1.73 ms |
| **Glowing Sapphire Crystal** | 3,000 | 5,256 &rarr; 3,000 (-42.9%) | 1.29 MB | **4.82 s** | 1.77 ms |
| **Weathered Granite Gargoyle** | 7,500 | 5,256 &rarr; 5,256 | 3.01 MB | **4.76 s** | 3.44 ms |
| **Carved Oak Treasure Chest** | 6,000 | 1,452 &rarr; 1,452 | 3.04 MB | **3.76 s** | 3.41 ms |

---

## Quick Start Guide

### Prerequisites
- Python 3.10+
- Node.js 20+
- npm 10+
- (Optional) Docker & Docker Compose
- (Optional) Redis (for distributed worker mode)

### Local Development Setup

1. **Clone & Set Up Python Environment**:
   ```powershell
   git clone https://github.com/polygen-ai/polygen.git
   cd polygen
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```

2. **Set Up Frontend Environment**:
   ```powershell
   cd frontend
   npm install
   npm run build
   cd ..
   ```

3. **Start the Application**:
   - **Windows PowerShell**:
     ```powershell
     .\start_polygen.ps1
     ```
   - **Windows Command Prompt**:
     ```cmd
     start_polygen.bat
     ```
   - **Manual Start**:
     ```powershell
     # Terminal 1: Backend
     .\venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload

     # Terminal 2: Frontend
     npm --prefix frontend run dev
     ```

4. **Access the Application**:
   - Frontend UI: `http://localhost:5173`
   - FastAPI Swagger Docs: `http://localhost:8000/docs`
   - ReDoc Reference: `http://localhost:8000/redoc`

---

## Production Deployment with Docker

PolyGen includes a production-ready `docker-compose.yml` orchestrating PostgreSQL, Redis, FastAPI, Celery GPU/CPU workers, and Nginx:

```bash
# 1. Configure environment variables
cp .env.example .env

# 2. Build and launch all services in detached mode
docker-compose up -d --build

# 3. Verify container health
docker-compose ps
```

Services started:
- `polygen-frontend`: Nginx serving optimized React 19 production build (Port `80`, `5173`)
- `polygen-backend`: FastAPI ASGI application server (Port `8000`)
- `polygen-worker`: Celery distributed task runner
- `polygen-db`: PostgreSQL 15 alpine database (Port `5432`)
- `polygen-redis`: Redis 7 in-memory cache and message broker (Port `6379`)

---

## Verification & Testing Suite

Execute the automated test suites:

```powershell
# Run the complete Part 15 End-to-End System Integration Suite
.\venv\Scripts\python tests/test_full_system_integration_part15.py

# Run the Empirical Performance Benchmark Suite
.\venv\Scripts\python scripts/measure_system_performance.py

# Run Asset Management & Multi-Tenant Tests (Part 14)
.\venv\Scripts\python tests/test_asset_management_part14.py

# Run GLB Export Pipeline & Binary Validation Tests (Part 12)
.\venv\Scripts\python tests/test_glb_export_part12.py

# Run Mesh Optimizer Tests (Part 11)
.\venv\Scripts\python tests/test_mesh_optimizer_part11.py

# Build frontend to verify TypeScript strict types
npm --prefix frontend run build
```

---

## Documentation Index

- [System Architecture Specification](docs/ARCHITECTURE.md)
- [REST & WebSocket API Reference](docs/API_REFERENCE.md)
- [Empirical Performance & Benchmark Report](docs/BENCHMARK_REPORT.md)
- [Live Product Demonstration Walkthrough](docs/DEMO_SCRIPT.md)

---

## License

PolyGen is distributed under the MIT Open Source License.
