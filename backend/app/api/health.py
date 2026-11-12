from fastapi import APIRouter, status
from app.config import settings
from app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check():
    """System health probe returning pipeline status, AI backend, and device telemetry."""
    return HealthResponse(
        status="online",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        ai_backend=settings.AI_BACKEND,
        device=settings.DEVICE,
        storage_backend=settings.STORAGE_BACKEND,
    )

