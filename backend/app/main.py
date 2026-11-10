import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.core.database import init_db
from app.api.auth import router as auth_router
from app.api.generate import router as generate_router
from app.api.assets import router as assets_router

logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
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
    description="Generative Text-to-3D Asset Pipeline API with PBR texturing and GLB export",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In development allow all; configurable via settings.CORS_ORIGINS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(auth_router, prefix="/api")
app.include_router(generate_router, prefix="/api")
app.include_router(assets_router, prefix="/api")

@app.get("/api/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "ai_backend": settings.AI_BACKEND,
        "device": settings.DEVICE,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)

