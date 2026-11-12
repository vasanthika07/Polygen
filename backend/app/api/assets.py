import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user_optional, get_current_user
from app.models.user import User
from app.schemas.asset import AssetResponse, AssetListResponse
from app.services.asset_service import asset_service

router = APIRouter(prefix="/assets", tags=["Asset Management"])

@router.get("", response_model=AssetListResponse)
async def list_assets(
    limit: int = 50,
    offset: int = 0,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Lists generated 3D assets ordered by creation date."""
    assets, total = await asset_service.list_assets(
        db=db,
        limit=limit,
        offset=offset,
        user_id=current_user.id if current_user else None,
    )
    items = [AssetResponse.from_asset_model(a) for a in assets]
    return AssetListResponse(items=items, total=total)

@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves full specification, geometry metrics, and metadata for a 3D asset."""
    asset = await asset_service.get_asset(db, asset_id, current_user)
    return AssetResponse.from_asset_model(asset)

@router.get("/{asset_id}/download")
async def download_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Securely serves the binary Khronos glTF 2.0 (GLB) file.
    Validates file existence, format header, and sets attachment disposition.
    """
    asset = await asset_service.get_asset(db, asset_id)
    if not asset.glb_path or not os.path.exists(asset.glb_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Binary GLB model for asset '{asset_id}' not found on storage"
        )

    # Validate file integrity: check GLB magic header
    with open(asset.glb_path, "rb") as f:
        magic = f.read(4)
        if magic != b"glTF":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Corrupted 3D asset file: invalid GLB header"
            )

    safe_filename = f"{asset.asset_name.replace(' ', '_').lower()}.glb"
    return FileResponse(
        path=asset.glb_path,
        media_type="model/gltf-binary",
        filename=safe_filename,
        headers={
            "Content-Disposition": f'attachment; filename="{safe_filename}"',
            "Cache-Control": "public, max-age=86400",
        }
    )

@router.get("/{asset_id}/preview")
async def get_preview(
    asset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Returns thumbnail image preview of the asset."""
    asset = await asset_service.get_asset(db, asset_id)
    if not asset.thumbnail_path or not os.path.exists(asset.thumbnail_path):
        raise HTTPException(status_code=404, detail="Thumbnail preview not available")

    return FileResponse(
        path=asset.thumbnail_path,
        media_type="image/png",
    )

@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Deletes 3D asset record and associated binary files from disk."""
    await asset_service.delete_asset(db, asset_id, current_user)
    return None
