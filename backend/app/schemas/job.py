from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator

class GenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=1000, description="Natural language description of the 3D asset")
    style: Optional[str] = Field("fantasy", description="Visual style: realistic, fantasy, sci-fi, stylized, low-poly")
    quality: Optional[str] = Field("high", description="Generation quality preset: standard, high, ultra")
    polygon_budget: Optional[int] = Field(10000, ge=500, le=50000, description="Target polygon count")
    target_format: Optional[str] = Field("glb", description="Export 3D format")

    @field_validator("prompt")
    @classmethod
    def validate_and_strip_prompt(cls, v: str) -> str:
        trimmed = v.strip()
        if len(trimmed) < 3:
            raise ValueError("Prompt must contain at least 3 non-whitespace characters")
        return trimmed

    @field_validator("style", "quality", "target_format")
    @classmethod
    def normalize_string_enums(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip().lower()
            if v.startswith("."):
                v = v[1:]
        return v

class MultimodalGenerationRequest(BaseModel):
    prompt: Optional[str] = Field(None, max_length=1000, description="Natural language description or refinement directives")
    image_base64: Optional[str] = Field(None, description="Base64 encoded image or data URI")
    image_url: Optional[str] = Field(None, description="URL to reference image")
    audio_transcript: Optional[str] = Field(None, description="Audio voice prompt transcription")
    style: Optional[str] = Field("realistic", description="Visual style")
    quality: Optional[str] = Field("high", description="Quality preset: standard, high, ultra")
    polygon_budget: Optional[int] = Field(5000, ge=500, le=50000, description="Target polygon budget")
    target_format: Optional[str] = Field("glb", description="Export format")

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
    duration_seconds: Optional[float] = None
    asset_id: Optional[str] = None
    asset: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_job_model(cls, job, asset_id: Optional[str] = None, asset_obj: Optional[Any] = None):
        dur = None
        if job.completed_at and job.created_at:
            dur = round((job.completed_at - job.created_at).total_seconds(), 2)

        resolved_asset_id = asset_id
        asset_dict = None
        if asset_obj:
            resolved_asset_id = asset_obj.id
            asset_dict = {
                "asset_id": asset_obj.id,
                "asset_name": asset_obj.asset_name,
                "glb_url": f"/api/assets/{asset_obj.id}/download",
                "preview_url": f"/api/assets/{asset_obj.id}/preview" if asset_obj.thumbnail_path else None,
                "polygon_count": asset_obj.polygon_count,
                "file_size": asset_obj.file_size,
                "created_at": asset_obj.created_at.isoformat() if asset_obj.created_at else None,
            }

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
            duration_seconds=dur,
            asset_id=resolved_asset_id,
            asset=asset_dict,
        )

class StageUpdateMessage(BaseModel):
    job_id: str
    stage: str
    progress: int
    message: str
    data: Optional[Dict[str, Any]] = None
