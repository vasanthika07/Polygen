from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class AssetResponse(BaseModel):
    id: str
    asset_id: str
    job_id: str
    user_id: Optional[str] = None
    asset_name: str
    original_prompt: Optional[str] = None
    glb_url: str
    thumbnail_url: Optional[str] = None
    preview_url: Optional[str] = None
    polygon_count: int
    file_size: int
    texture_resolution: int = 1024
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_asset_model(cls, asset):
        return cls(
            id=asset.id,
            asset_id=asset.id,
            job_id=asset.job_id,
            user_id=asset.user_id,
            asset_name=asset.asset_name,
            original_prompt=asset.original_prompt,
            glb_url=f"/api/assets/{asset.id}/download",
            thumbnail_url=f"/api/assets/{asset.id}/preview" if asset.thumbnail_path else None,
            preview_url=f"/api/assets/{asset.id}/preview" if asset.thumbnail_path else None,
            polygon_count=asset.polygon_count,
            file_size=asset.file_size,
            texture_resolution=asset.texture_resolution,
            metadata=asset.metadata_json,
            created_at=asset.created_at,
        )

class AssetListResponse(BaseModel):
    items: List[AssetResponse]
    total: int
