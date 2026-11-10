import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "PolyGen - Generative Text-to-3D Asset Pipeline"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # Security
    SECRET_KEY: str = "polygen-dev-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./polygen.db"
    
    # Storage Paths
    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    STORAGE_DIR: str = os.path.join(BASE_DIR, "storage")
    STORAGE_RAW_DIR: str = os.path.join(STORAGE_DIR, "raw")
    STORAGE_PROCESSED_DIR: str = os.path.join(STORAGE_DIR, "processed")
    STORAGE_TEXTURES_DIR: str = os.path.join(STORAGE_DIR, "textures")
    STORAGE_EXPORTS_DIR: str = os.path.join(STORAGE_DIR, "exports")
    STORAGE_PREVIEWS_DIR: str = os.path.join(STORAGE_DIR, "previews")
    
    # AI Engine Configuration
    AI_BACKEND: str = "local_shape"
    DEVICE: str = "cpu"
    TORCH_DTYPE: str = "float32"
    DEFAULT_POLYGON_BUDGET: int = 10000
    MAX_POLYGON_BUDGET: int = 50000
    
    # Celery / Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

# Ensure directories exist
for folder in [
    settings.STORAGE_RAW_DIR,
    settings.STORAGE_PROCESSED_DIR,
    settings.STORAGE_TEXTURES_DIR,
    settings.STORAGE_EXPORTS_DIR,
    settings.STORAGE_PREVIEWS_DIR,
]:
    os.makedirs(folder, exist_ok=True)

