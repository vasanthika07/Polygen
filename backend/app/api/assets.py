import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.asset import AssetResponse, AssetListResponse
from app.services.asset_service import asset_service
from app.config import settings

router = APIRouter(prefix="/assets", tags=["Asset Management"])

@router.get("", response_model=AssetListResponse)
async def list_assets(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, description="Search term matching asset name or prompt"),
    sort_by: str = Query("newest", regex="^(newest|oldest|polygons_desc|polygons_asc|size_desc|name_asc)$"),
    date_filter: str = Query("all", regex="^(all|today|week|month)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Lists generated 3D assets owned by the authenticated user with search, filtering, and sorting.
    Strictly isolates assets so users can only access their own assets.
    """
    assets, total = await asset_service.list_assets(
        db=db,
        limit=limit,
        offset=offset,
        user_id=current_user.id,
        search=search,
        sort_by=sort_by,
        date_filter=date_filter,
    )
    items = [AssetResponse.from_asset_model(a) for a in assets]
    return AssetListResponse(items=items, total=total)

@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves full specification, geometry metrics, and metadata for a 3D asset.
    Enforces user ownership check.
    """
    asset = await asset_service.get_asset(db, asset_id, current_user)
    return AssetResponse.from_asset_model(asset)

@router.get("/{asset_id}/download")
async def download_asset(
    asset_id: str,
    export_option: str = Query("standard", regex="^(standard|high_quality|optimized)$", description="Export profile: standard, high_quality, optimized"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Securely serves the binary Khronos glTF 2.0 (GLB) file.
    Validates user ownership, file existence, format header, and sets attachment disposition.
    Supports token via Bearer header or ?token= query parameter.
    Supports export profiles: standard (1024px), high_quality (2048px), and optimized (512px).
    """
    asset = await asset_service.get_asset(db, asset_id, current_user)
    if not asset.glb_path or not os.path.exists(asset.glb_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Binary GLB model for asset '{asset_id}' not found on storage"
        )

    # Resolve variant if specific export_option requested
    serve_path = os.path.abspath(asset.glb_path)
    storage_root = os.path.abspath(settings.STORAGE_DIR)
    if not serve_path.startswith(storage_root):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to specified file path is forbidden"
        )

    if export_option != "standard":
        dir_name = os.path.dirname(asset.glb_path)
        base_name = os.path.splitext(os.path.basename(asset.glb_path))[0]
        variant_path = os.path.join(dir_name, f"{base_name}_{export_option}.glb")
        if os.path.exists(variant_path):
            serve_path = os.path.abspath(variant_path)
            if not serve_path.startswith(storage_root):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access to specified file path is forbidden"
                )

    # Validate file integrity: check GLB magic header
    with open(serve_path, "rb") as f:
        magic = f.read(4)
        if magic != b"glTF":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Corrupted 3D asset file: invalid GLB header"
            )

    safe_filename = f"{asset.asset_name.replace(' ', '_').lower()}_{export_option}.glb" if export_option != "standard" else f"{asset.asset_name.replace(' ', '_').lower()}.glb"
    return FileResponse(
        path=serve_path,
        media_type="model/gltf-binary",
        filename=safe_filename,
        headers={
            "Content-Disposition": f'attachment; filename="{safe_filename}"',
            "Cache-Control": "private, max-age=86400",
        }
    )

@router.get("/{asset_id}/preview")
async def get_preview(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns thumbnail image preview of the asset. Enforces ownership."""
    asset = await asset_service.get_asset(db, asset_id, current_user)
    if not asset.thumbnail_path or not os.path.exists(asset.thumbnail_path):
        raise HTTPException(status_code=404, detail="Thumbnail preview not available")

    return FileResponse(
        path=asset.thumbnail_path,
        media_type="image/png",
    )

@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Deletes 3D asset record and associated binary files from disk. Enforces ownership."""
    await asset_service.delete_asset(db, asset_id, current_user)
