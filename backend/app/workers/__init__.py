from app.workers.celery_app import celery_app
from app.workers.tasks import generate_3d_asset_task

__all__ = ["celery_app", "generate_3d_asset_task"]

