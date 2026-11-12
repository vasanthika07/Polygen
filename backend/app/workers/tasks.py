import asyncio
import logging
import concurrent.futures
from app.workers.celery_app import celery_app
from app.services.pipeline_orchestrator import pipeline_orchestrator
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

def _run_async(coro):
    """Executes an async coroutine safely, even if called within an existing event loop."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)

@celery_app.task(name="generate_3d_asset_task", bind=True)
def generate_3d_asset_task(
    self,
    job_id: str,
    style_override: str = None,
    quality: str = "high",
    polygon_budget: int = 10000,
    target_format: str = "glb",
):
    """
    Celery background worker task for asynchronous 3D asset generation.
    Executes the 8-stage pipeline, updates database state, and streams progress.
    """
    logger.info(f"[Celery Worker] Received 3D generation task for job: {job_id}")
    try:
        _run_async(
            pipeline_orchestrator.run_pipeline(
                job_id=job_id,
                db_factory=AsyncSessionLocal,
                style_override=style_override,
                quality=quality,
                polygon_budget=polygon_budget,
                target_format=target_format,
            )
        )
        logger.info(f"[Celery Worker] Successfully completed job: {job_id}")
        return {"status": "success", "job_id": job_id}
    except Exception as e:
        logger.error(f"[Celery Worker] Task failed for job {job_id}: {e}", exc_info=True)
        raise e
