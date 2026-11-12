import os
import logging
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.asset import GeneratedAsset
from app.models.user import User
from app.services.storage import storage_service
from app.core.errors import EntityNotFoundException, AuthorizationException

logger = logging.getLogger(__name__)

class AssetService:
    """Service handling asset retrieval, ownership authorization, file removal, and metadata."""

    @classmethod
    async def list_assets(
        cls,
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[str] = None
    ) -> Tuple[List[GeneratedAsset], int]:
        """Lists assets with pagination. If user_id is provided, filters by owner."""
        query = select(GeneratedAsset)
        count_query = select(func.count(GeneratedAsset.id))

        if user_id:
            query = query.where(GeneratedAsset.user_id == user_id)
            count_query = count_query.where(GeneratedAsset.user_id == user_id)

        query = query.order_by(GeneratedAsset.created_at.desc()).offset(offset).limit(limit)

        result = await db.execute(query)
        assets = result.scalars().all()

        count_result = await db.execute(count_query)
        total = count_result.scalar_one() or len(assets)

        return assets, total

    @classmethod
    async def get_asset(
        cls,
        db: AsyncSession,
        asset_id: str,
        current_user: Optional[User] = None
    ) -> GeneratedAsset:
        """Retrieves an asset by ID."""
        result = await db.execute(select(GeneratedAsset).where(GeneratedAsset.id == asset_id))
        asset = result.scalars().first()
        if not asset:
            raise EntityNotFoundException("GeneratedAsset", asset_id)
        return asset

    @classmethod
    async def delete_asset(
        cls,
        db: AsyncSession,
        asset_id: str,
        current_user: Optional[User] = None
    ) -> bool:
        """Deletes asset record and corresponding storage files."""
        asset = await cls.get_asset(db, asset_id, current_user)

        # Enforce user ownership if user is authenticated and asset has owner
        if current_user and asset.user_id and asset.user_id != current_user.id:
            raise AuthorizationException("You do not own this asset and cannot delete it")

        # Delete physical GLB file if present
        if asset.glb_path and os.path.exists(asset.glb_path):
            try:
                os.remove(asset.glb_path)
            except OSError as e:
                logger.warning(f"Could not delete GLB file at {asset.glb_path}: {e}")

        # Delete thumbnail if present
        if asset.thumbnail_path and os.path.exists(asset.thumbnail_path):
            try:
                os.remove(asset.thumbnail_path)
            except OSError as e:
                logger.warning(f"Could not delete thumbnail at {asset.thumbnail_path}: {e}")

        await db.delete(asset)
        await db.commit()
        return True

asset_service = AssetService()

