import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.dependencies import get_current_user_optional
from app.models.user import User
from app.models.asset import GeneratedAsset
from app.schemas.asset import AssetResponse, AssetListResponse

router = APIRouter(prefix="/assets", tags=["Assets"])

@router.get("", response_model=AssetListResponse)
async def list_assets(
    limit: int = 50,
    offset: int = 0,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    query = select(GeneratedAsset).order_by(GeneratedAsset.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    assets = result.scalars().all()

    items = []
    for a in assets:
        items.append(AssetResponse(
            asset_id=a.asset_id,
            job_id=a.job_id,
            user_id=a.user_id,
            asset_name=a.asset_name,
            glb_url=f"/api/assets/{a.asset_id}/download",
            preview_url=f"/api/assets/{a.asset_id}/preview" if a.preview_path else None,
            polygon_count=a.polygon_count,
            file_size=a.file_size,
            texture_resolution=a.texture_resolution,
            created_at=a.created_at,
        ))

    return AssetListResponse(items=items, total=len(items))

@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GeneratedAsset).where(GeneratedAsset.asset_id == asset_id))
    asset = result.scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return AssetResponse(
        asset_id=asset.asset_id,
        job_id=asset.job_id,
        user_id=asset.user_id,
        asset_name=asset.asset_name,
        glb_url=f"/api/assets/{asset.asset_id}/download",
        preview_url=f"/api/assets/{asset.asset_id}/preview" if asset.preview_path else None,
        polygon_count=asset.polygon_count,
        file_size=asset.file_size,
        texture_resolution=asset.texture_resolution,
        created_at=asset.created_at,
    )

@router.get("/{asset_id}/download")
async def download_asset(asset_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GeneratedAsset).where(GeneratedAsset.asset_id == asset_id))
    asset = result.scalars().first()
    if not asset or not os.path.exists(asset.glb_path):
        raise HTTPException(status_code=404, detail="GLB file not found on disk")

    filename = f"{asset.asset_name.replace(' ', '_').lower()}.glb"
    return FileResponse(
        path=asset.glb_path,
        media_type="model/gltf-binary",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/{asset_id}/preview")
async def get_preview(asset_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GeneratedAsset).where(GeneratedAsset.asset_id == asset_id))
    asset = result.scalars().first()
    if not asset or not asset.preview_path or not os.path.exists(asset.preview_path):
        raise HTTPException(status_code=404, detail="Preview image not found")

    return FileResponse(
        path=asset.preview_path,
        media_type="image/png",
    )

@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(asset_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GeneratedAsset).where(GeneratedAsset.asset_id == asset_id))
    asset = result.scalars().first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Remove files if exist
    if os.path.exists(asset.glb_path):
        try:
            os.remove(asset.glb_path)
        except Exception:
            pass

    await db.delete(asset)
    await db.commit()
    return None

