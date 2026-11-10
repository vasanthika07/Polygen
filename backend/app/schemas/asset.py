from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class AssetResponse(BaseModel):
    asset_id: str
    job_id: str
    user_id: Optional[str] = None
    asset_name: str
    glb_url: str
    preview_url: Optional[str] = None
    polygon_count: int
    file_size: int
    texture_resolution: int
    created_at: datetime

    class Config:
        from_attributes = True

class AssetListResponse(BaseModel):
    items: List[AssetResponse]
    total: int

