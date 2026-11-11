# PolyGen REST & WebSocket API Specification

## Base URL
- Local Development: `http://127.0.0.1:8000`
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc Documentation: `http://127.0.0.1:8000/redoc`

---

## 1. Authentication Endpoints

### 1.1 Register User
- **Method**: `POST`
- **Route**: `/api/auth/register`
- **Request Body**:
```json
{
  "username": "3dartist",
  "email": "artist@polygen.io",
  "password": "StrongPassword123!"
}
```
- **Response** (`201 Created`):
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {
    "id": "e83f2a1b-...",
    "username": "3dartist",
    "email": "artist@polygen.io",
    "created_at": "2026-11-10T13:20:00Z"
  }
}
```

### 1.2 User Login
- **Method**: `POST`
- **Route**: `/api/auth/login`
- **Request Body**:
```json
{
  "username_or_email": "3dartist",
  "password": "StrongPassword123!"
}
```

### 1.3 Get Current User
- **Method**: `GET`
- **Route**: `/api/auth/me`
- **Headers**: `Authorization: Bearer <token>`

---

## 2. Generation Engine Endpoints

### 2.1 Submit 3D Generation Job
- **Method**: `POST`
- **Route**: `/api/generate`
- **Headers**: `Authorization: Bearer <token>` (Optional)
- **Request Body**:
```json
{
  "prompt": "A rusted medieval broadsword with a glowing blue sapphire in the hilt.",
  "style": "medieval fantasy",
  "quality": "high",
  "polygon_budget": 10000,
  "target_format": "glb"
}
```
- **Response** (`202 Accepted`):
```json
{
  "job_id": "job_df51c6743604",
  "prompt": "A rusted medieval broadsword with a glowing blue sapphire in the hilt.",
  "status": "pending",
  "progress": 0,
  "current_stage": "queued",
  "error_message": null,
  "created_at": "2026-11-10T13:42:00Z",
  "completed_at": null,
  "asset_id": null
}
```

### 2.2 Query Job Status
- **Method**: `GET`
- **Route**: `/api/jobs/{job_id}`
- **Response** (`200 OK`):
```json
{
  "job_id": "job_df51c6743604",
  "prompt": "A rusted medieval broadsword with a glowing blue sapphire in the hilt.",
  "status": "completed",
  "progress": 100,
  "current_stage": "completed",
  "error_message": null,
  "created_at": "2026-11-10T13:42:00Z",
  "completed_at": "2026-11-10T13:42:02Z",
  "asset_id": "asset_92b8d0e74f"
}
```

### 2.3 Live WebSocket Progress Stream
- **Protocol**: `WebSocket` (`ws://` or `wss://`)
- **Route**: `/ws/jobs/{job_id}`
- **Sample Event Broadcasts**:
```json
{
  "job_id": "job_df51c6743604",
  "stage": "prompt_processing",
  "progress": 10,
  "message": "Deconstructing natural-language semantics, materials, and geometry",
  "timestamp": "2026-11-10T13:42:00.100Z"
}
```
```json
{
  "job_id": "job_df51c6743604",
  "stage": "completed",
  "progress": 100,
  "message": "Asset generated and verified! Ready for 3D inspection and download.",
  "data": {
    "asset_id": "asset_92b8d0e74f",
    "glb_url": "/api/assets/asset_92b8d0e74f/download",
    "polygon_count": 856,
    "file_size": 3567096,
    "file_size_mb": 3.4,
    "dimensions": [0.75, 0.31, 3.55]
  },
  "timestamp": "2026-11-10T13:42:02.300Z"
}
```

---

## 3. Asset Repository Endpoints

### 3.1 List Assets
- **Method**: `GET`
- **Route**: `/api/assets?limit=50&offset=0`

### 3.2 Get Asset Detail
- **Method**: `GET`
- **Route**: `/api/assets/{asset_id}`

### 3.3 Download Binary GLB
- **Method**: `GET`
- **Route**: `/api/assets/{asset_id}/download`
- **Response Headers**:
  - `Content-Type: model/gltf-binary`
  - `Content-Disposition: attachment; filename="asset_name.glb"`

### 3.4 Get Asset Preview
- **Method**: `GET`
- **Route**: `/api/assets/{asset_id}/preview`
- **Response Headers**:
  - `Content-Type: image/png`

### 3.5 Delete Asset
- **Method**: `DELETE`
- **Route**: `/api/assets/{asset_id}`
- **Response**: `204 No Content`
