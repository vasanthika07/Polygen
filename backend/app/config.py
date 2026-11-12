import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "PolyGen - Generative Text-to-3D Asset Pipeline"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # Security & JWT
    SECRET_KEY: str = "polygen-dev-super-secret-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # Database Configuration (PostgreSQL / SQLite)
    # Default to sqlite+aiosqlite for local dev, can be overridden by DATABASE_URL in .env
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./polygen.db",
        description="Async database connection string. e.g. postgresql+asyncpg://polygen:polygen@localhost:5432/polygen"
    )
    POSTGRES_SERVER: Optional[str] = "localhost"
    POSTGRES_USER: Optional[str] = "postgres"
    POSTGRES_PASSWORD: Optional[str] = "postgres"
    POSTGRES_DB: Optional[str] = "polygen"
    POSTGRES_PORT: Optional[int] = 5432
    
    # Storage Configuration
    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    STORAGE_DIR: str = os.path.join(BASE_DIR, "storage")
    STORAGE_RAW_DIR: str = os.path.join(STORAGE_DIR, "raw_meshes")
    STORAGE_PROCESSED_DIR: str = os.path.join(STORAGE_DIR, "processed_meshes")
    STORAGE_TEXTURES_DIR: str = os.path.join(STORAGE_DIR, "textures")
    STORAGE_EXPORTS_DIR: str = os.path.join(STORAGE_DIR, "exports")
    STORAGE_THUMBNAILS_DIR: str = os.path.join(STORAGE_DIR, "thumbnails")
    
    # Storage Provider Abstraction ('local' or 's3')
    STORAGE_BACKEND: str = "local"
    S3_BUCKET_NAME: str = "polygen-assets"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_ENDPOINT_URL: Optional[str] = None
    
    # AI Engine Configuration
    AI_BACKEND: str = "local_shape"
    DEVICE: str = "cpu"
    TORCH_DTYPE: str = "float32"
    DEFAULT_POLYGON_BUDGET: int = 10000
    MAX_POLYGON_BUDGET: int = 50000
    
    # Celery & Redis Worker Integration
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    CELERY_BROKER_URL: str = "redis://127.0.0.1:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://127.0.0.1:6379/0"
    CELERY_TASK_ALWAYS_EAGER: bool = False  # Set True for synchronous test runs
    
    # CORS Origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
    ]

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

# Ensure all 5 designated storage directories exist
for folder in [
    settings.STORAGE_RAW_DIR,
    settings.STORAGE_PROCESSED_DIR,
    settings.STORAGE_TEXTURES_DIR,
    settings.STORAGE_EXPORTS_DIR,
    settings.STORAGE_THUMBNAILS_DIR,
]:
    os.makedirs(folder, exist_ok=True)
