import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.core.database import init_db
from app.core.errors import register_error_handlers
from app.api.auth import router as auth_router
from app.api.generate import router as generate_router, websocket_job_status
from app.api.assets import router as assets_router
from app.api.health import router as health_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("polygen")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing PolyGen backend service...")
    await init_db()
    logger.info("Database initialized successfully.")
    yield
    logger.info("PolyGen backend service shutting down.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Automated AI-driven Generative Text-to-3D Asset Pipeline with PBR texturing and decimation.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Global CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Custom Exception Handlers
register_error_handlers(app)

# API Routers
app.include_router(auth_router, prefix="/api")
app.include_router(generate_router, prefix="/api")
app.include_router(assets_router, prefix="/api")
app.include_router(health_router, prefix="/api")

# Direct WebSocket endpoint matching specification: WS /ws/jobs/{job_id}
app.add_api_websocket_route("/ws/jobs/{job_id}", websocket_job_status)

# Mount static frontend production build if present
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
if os.path.exists(frontend_dist):
    frontend_assets = os.path.join(frontend_dist, "assets")
    if os.path.exists(frontend_assets):
        app.mount("/assets", StaticFiles(directory=frontend_assets), name="frontend-assets")
    
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        if full_path.startswith("api") or full_path.startswith("ws") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("openapi.json"):
            return None
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
