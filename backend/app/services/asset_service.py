import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_

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
        user_id: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "newest",
        date_filter: Optional[str] = "all"
    ) -> Tuple[List[GeneratedAsset], int]:
        """Lists assets with pagination, search, date filtering, and sorting. If user_id is provided, filters strictly by owner."""
        query = select(GeneratedAsset)
        count_query = select(func.count(GeneratedAsset.id))

        # Strict user ownership isolation
        if user_id:
            query = query.where(GeneratedAsset.user_id == user_id)
            count_query = count_query.where(GeneratedAsset.user_id == user_id)

        # Keyword search matching asset_name or original_prompt
        if search and search.strip():
            term = f"%{search.strip()}%"
            search_cond = or_(
                GeneratedAsset.asset_name.ilike(term),
                GeneratedAsset.original_prompt.ilike(term)
            )
            query = query.where(search_cond)
            count_query = count_query.where(search_cond)

        # Creation date filter
        if date_filter and date_filter != "all":
            now = datetime.utcnow()
            if date_filter == "today":
                from_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif date_filter == "week":
                from_date = now - timedelta(days=7)
            elif date_filter == "month":
                from_date = now - timedelta(days=30)
            else:
                from_date = None

            if from_date:
                query = query.where(GeneratedAsset.created_at >= from_date)
                count_query = count_query.where(GeneratedAsset.created_at >= from_date)

        # Dynamic sorting
        if sort_by == "oldest":
            query = query.order_by(GeneratedAsset.created_at.asc())
        elif sort_by == "polygons_desc":
            query = query.order_by(GeneratedAsset.polygon_count.desc(), GeneratedAsset.created_at.desc())
        elif sort_by == "polygons_asc":
            query = query.order_by(GeneratedAsset.polygon_count.asc(), GeneratedAsset.created_at.desc())
        elif sort_by == "size_desc":
            query = query.order_by(GeneratedAsset.file_size.desc(), GeneratedAsset.created_at.desc())
        elif sort_by == "name_asc":
            query = query.order_by(GeneratedAsset.asset_name.asc())
        else: # "newest" default
            query = query.order_by(GeneratedAsset.created_at.desc())

        query = query.offset(offset).limit(limit)

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
        """Retrieves an asset by ID and enforces user ownership authorization."""
        result = await db.execute(select(GeneratedAsset).where(GeneratedAsset.id == asset_id))
        asset = result.scalars().first()
        if not asset:
            raise EntityNotFoundException("GeneratedAsset", asset_id)
        
        # Enforce user-level ownership isolation
        if current_user and asset.user_id and asset.user_id != current_user.id:
            raise AuthorizationException("You do not have permission to access this 3D asset")

        return asset

    @classmethod
    async def delete_asset(
        cls,
        db: AsyncSession,
        asset_id: str,
        current_user: Optional[User] = None
    ) -> bool:
        """Deletes asset record and corresponding storage files after verifying ownership."""
        asset = await cls.get_asset(db, asset_id, current_user)

        # Enforce user ownership
        if current_user and asset.user_id and asset.user_id != current_user.id:
            raise AuthorizationException("You do not have permission to delete this 3D asset")

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
