import logging
import socket
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db, AsyncSessionLocal
from app.core.dependencies import get_current_user_optional
from app.core.websocket_manager import ws_manager
from app.models.user import User
from app.models.job import GenerationJob
from app.models.asset import GeneratedAsset
from app.schemas.job import GenerationRequest, JobStatusResponse
from app.services.pipeline_orchestrator import pipeline_orchestrator
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Generation Jobs"])

def is_redis_available(host: str = "127.0.0.1", port: int = 6379, timeout: float = 0.5) -> bool:
    """Quickly probes whether Redis broker is reachable without blocking."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

@router.post("/generate", response_model=JobStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_asset(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Submits a generative text-to-3D synthesis request.
    Creates a database record and queues an asynchronous generation worker task.
    """
    config_payload = {
        "style": request.style,
        "quality": request.quality,
        "polygon_budget": request.polygon_budget,
        "target_format": request.target_format,
    }

    job = GenerationJob(
        user_id=current_user.id if current_user else None,
        prompt=request.prompt,
        configuration=config_payload,
        status="queued",
        progress=0,
        current_stage="queued",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Dispatch to Celery worker if Redis is reachable, otherwise execute via async background task
    redis_active = is_redis_available()
    dispatched_to_celery = False

    if redis_active and not settings.CELERY_TASK_ALWAYS_EAGER:
        try:
            from app.workers.tasks import generate_3d_asset_task
            generate_3d_asset_task.delay(
                job_id=job.id,
                style_override=request.style,
                quality=request.quality,
                polygon_budget=request.polygon_budget,
                target_format=request.target_format,
            )
            dispatched_to_celery = True
            logger.info(f"Job {job.id} dispatched to Celery worker via Redis.")
        except Exception as e:
            logger.warning(f"Failed to enqueue to Celery ({e}). Falling back to background tasks.")

    if not dispatched_to_celery:
        logger.info(f"Executing job {job.id} asynchronously via background task runner.")
        background_tasks.add_task(
            pipeline_orchestrator.run_pipeline,
            job_id=job.id,
            db_factory=AsyncSessionLocal,
            style_override=request.style,
            quality=request.quality,
            polygon_budget=request.polygon_budget,
            target_format=request.target_format,
        )

    return JobStatusResponse.from_job_model(job)

@router.get("/jobs", response_model=List[JobStatusResponse])
async def list_jobs(
    limit: int = 50,
    offset: int = 0,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Lists generation jobs ordered by creation timestamp."""
    query = select(GenerationJob)
    if current_user:
        query = query.where(GenerationJob.user_id == current_user.id)
    query = query.order_by(GenerationJob.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    jobs = result.scalars().all()
    
    responses = []
    for j in jobs:
        asset_res = await db.execute(select(GeneratedAsset).where(GeneratedAsset.job_id == j.id))
        asset = asset_res.scalars().first()
        responses.append(JobStatusResponse.from_job_model(j, asset_id=asset.id if asset else None))
    return responses

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves real-time status and stage progress for a generation job."""
    result = await db.execute(select(GenerationJob).where(GenerationJob.id == job_id))
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Generation job '{job_id}' not found")
    
    asset_result = await db.execute(select(GeneratedAsset).where(GeneratedAsset.job_id == job_id))
    asset = asset_result.scalars().first()
    asset_id = asset.id if asset else None

    return JobStatusResponse.from_job_model(job, asset_id=asset_id)

@router.websocket("/ws/jobs/{job_id}")
async def websocket_job_status(websocket: WebSocket, job_id: str):
    """Bidirectional WebSocket connection streaming stage updates for the given job."""
    await ws_manager.connect(job_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(job_id, websocket)
    except Exception:
        ws_manager.disconnect(job_id, websocket)
