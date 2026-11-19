# PolyGen REST & WebSocket API Specification

## Base URLs
- **Local API**: `http://127.0.0.1:8000`
- **Interactive OpenAPI Documentation**: `http://127.0.0.1:8000/docs`
- **ReDoc Interactive Reference**: `http://127.0.0.1:8000/redoc`
- **WebSocket Gateway**: `ws://127.0.0.1:8000/ws/jobs/{job_id}`

---

## 1. Authentication Endpoints (`/api/auth`)

### 1.1 Register User Account
- **Endpoint**: `POST /api/auth/register`
- **Status**: `201 Created`
- **Request Body**:
```json
{
  "name": "Alex Mercer",
  "username": "alex3d",
  "email": "alex@polygen.ai",
  "password": "SecurePassword123!"
}
```
- **Response**: Returns JWT access token, refresh token, and user profile.

### 1.2 User Login
- **Endpoint**: `POST /api/auth/login`
- **Status**: `200 OK`
- **Request Body**:
```json
{
  "username_or_email": "alex@polygen.ai",
  "password": "SecurePassword123!"
}
```
- **Response**: Returns session access token (`bearer`) and user profile.

### 1.3 Get Current User Profile
- **Endpoint**: `GET /api/auth/me`
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**: User model with id, email, username, display name, and creation timestamp.

---

## 2. 3D Asset Generation Endpoints (`/api`)

### 2.1 Submit 3D Generation Job
- **Endpoint**: `POST /api/generate`
- **Status**: `202 Accepted`
- **Headers**: `Authorization: Bearer <access_token>`
- **Request Body**:
```json
{
  "prompt": "A rusted medieval broadsword with a glowing blue sapphire in the hilt.",
  "style": "fantasy",
  "quality": "high",
  "polygon_budget": 5000,
  "target_format": "glb"
}
```
- **Response**:
```json
{
  "job_id": "job_32af37896e21",
  "status": "queued",
  "progress": 0,
  "current_stage": "queued",
  "created_at": "2026-11-19T14:50:00Z"
}
```

### 2.2 Get Generation Job Status
- **Endpoint**: `GET /api/jobs/{job_id}`
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**:
```json
{
  "job_id": "job_32af37896e21",
  "status": "completed",
  "progress": 100,
  "current_stage": "completed",
  "asset_id": "asset_b86dd1fdac40",
  "created_at": "2026-11-19T14:50:00Z",
  "completed_at": "2026-11-19T14:50:04Z",
  "duration_seconds": 4.5
}
```

### 2.3 List Generation Jobs (History)
- **Endpoint**: `GET /api/jobs`
- **Query Parameters**:
  - `limit`: `1..100` (default 50)
  - `offset`: `0..N`
  - `status`: `all` | `completed` | `processing` | `queued` | `failed`
  - `search`: Keyword string
- **Response**: Array of jobs owned by current user.

---

## 3. Real-Time WebSocket Streaming

### 3.1 Real-Time Stage Progress WebSocket
- **Protocol**: `WebSocket`
- **Endpoint**: `/ws/jobs/{job_id}`
- **Client Keepalive**: Send string `"ping"` every 15s; server responds with `{"type": "pong"}`.
- **Stage Progression Events Emitted**:
  1. `prompt_analysis` (10%)
  2. `mesh_generation` (25% &rarr; 35%)
  3. `mesh_processing` (45%)
  4. `uv_mapping` (55%)
  5. `texture_generation` (70%)
  6. `material_creation` (80%)
  7. `mesh_optimization` (88%)
  8. `glb_export` (95%)
  9. `completed` (100%)

---

## 4. Asset Library & Download Endpoints (`/api/assets`)

### 4.1 List Assets
- **Endpoint**: `GET /api/assets`
- **Query Parameters**:
  - `search`: Keyword filter
  - `sort_by`: `newest` | `oldest` | `polygons_desc` | `polygons_asc` | `size_desc` | `name_asc`
  - `date_filter`: `today` | `week` | `month` | `all`
  - `limit`, `offset`: Pagination
- **Response**: `{ "items": [...], "total": 12 }`

### 4.2 Get Asset Details
- **Endpoint**: `GET /api/assets/{asset_id}`
- **Headers**: `Authorization: Bearer <access_token>`
- **Response**: Complete metadata including bounding box dimensions, polygon count, file size, and texture map paths.

### 4.3 Download Binary GLB Asset
- **Endpoint**: `GET /api/assets/{asset_id}/download`
- **Query Parameters**:
  - `export_option`: `standard` | `high_quality` | `optimized`
  - `token`: (Optional query token for direct anchor downloads)
- **Response**: Binary stream (`model/gltf-binary`) with content disposition attachment.

### 4.4 Delete Asset
- **Endpoint**: `DELETE /api/assets/{asset_id}`
- **Status**: `204 No Content`
- **Behavior**: Verifies user ownership, deletes database record and associated physical files on disk.

---

## 5. PBR Materials & Mesh Optimizer Endpoints

### 5.1 Get Material Presets
- **Endpoint**: `GET /api/materials/presets`
- **Response**: Physical parameter configurations for `rusted_sword`, `glowing_sapphire`, `carved_wood`, `granite_stone`, `translucent_glass`, `polished_gold`.

### 5.2 Evaluate PBR Material
- **Endpoint**: `POST /api/materials/evaluate`
- **Request Body**: `{ "prompt": "...", "material_type": "...", "details": [...] }`
- **Response**: Cook-Torrance parameters, Gram-Schmidt tangent status, and glTF 2.0 schema validation.

### 5.3 Get Optimizer Presets
- **Endpoint**: `GET /api/optimizer/presets`
- **Response**: Defined budgets (`low`: 3,000, `medium`: 10,000, `high`: 35,000).

### 5.4 Analyze Mesh Topology
- **Endpoint**: `POST /api/optimizer/analyze`
- **Response**: Vertex/face counts, watertightness, surface area, bounding box volume, non-manifold edge detection.
