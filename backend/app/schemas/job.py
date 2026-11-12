from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class GenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=1000, description="Natural language description of the 3D asset")
    style: Optional[str] = Field("fantasy", description="Visual style: realistic, fantasy, sci-fi, stylized, low-poly")
    quality: Optional[str] = Field("high", description="Generation quality preset: standard, high, ultra")
    polygon_budget: Optional[int] = Field(10000, ge=1000, le=50000, description="Target polygon count")
    target_format: Optional[str] = Field("glb", description="Export 3D format")

class StructuredPrompt(BaseModel):
    object: str
    style: str
    material: str
    details: List[str] = []
    texture: str
    quality: str = "high"
    target_format: str = "glb"
    polygon_budget: int = 10000
    raw_prompt: str

class JobStatusResponse(BaseModel):
    id: str
    job_id: str
    user_id: Optional[str] = None
    prompt: str
    configuration: Optional[Dict[str, Any]] = None
    status: str
    progress: int
    current_stage: str
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    asset_id: Optional[str] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_job_model(cls, job, asset_id: Optional[str] = None):
        return cls(
            id=job.id,
            job_id=job.id,
            user_id=job.user_id,
            prompt=job.prompt,
            configuration=job.configuration,
            status=job.status,
            progress=job.progress,
            current_stage=job.current_stage,
            error_message=job.error_message,
            created_at=job.created_at,
            completed_at=job.completed_at,
            asset_id=asset_id,
        )

class StageUpdateMessage(BaseModel):
    job_id: str
    stage: str
    progress: int
    message: str
    data: Optional[Dict[str, Any]] = None
