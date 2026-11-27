import logging
import socket
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

from app.core.database import get_db, AsyncSessionLocal
from app.core.dependencies import get_current_user
from app.core.security import decode_token
from app.core.websocket_manager import ws_manager
from app.models.user import User
from app.models.job import GenerationJob
from app.models.asset import GeneratedAsset
from app.schemas.job import GenerationRequest, MultimodalGenerationRequest, JobStatusResponse
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submits a generative text-to-3D synthesis request for the authenticated user.
    Creates a database record bound to user_id and queues an asynchronous worker task.
    """
    config_payload = {
        "style": request.style,
        "quality": request.quality,
        "polygon_budget": request.polygon_budget,
        "target_format": request.target_format,
    }

    job = GenerationJob(
        user_id=current_user.id,
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
            logger.info(f"Job {job.id} dispatched to Celery worker for user {current_user.id}")
        except Exception as e:
            logger.warning(f"Failed to enqueue to Celery ({e}). Falling back to background tasks.")

    if not dispatched_to_celery:
        logger.info(f"Executing job {job.id} asynchronously for user {current_user.id} via background task runner.")
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

@router.post("/generate/multimodal", response_model=JobStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_multimodal_asset_endpoint(
    request: MultimodalGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submits a multimodal generative 3D synthesis request combining image, voice, and text directives.
    """
    from datetime import datetime
    resolved_prompt = request.prompt or "Multimodal 3D reference asset"
    config_payload = {
        "style": request.style,
        "quality": request.quality,
        "polygon_budget": request.polygon_budget,
        "target_format": request.target_format,
        "has_image": bool(request.image_base64 or request.image_url),
        "has_audio": bool(request.audio_transcript),
    }

    job = GenerationJob(
        user_id=current_user.id,
        prompt=resolved_prompt,
        configuration=config_payload,
        status="queued",
        progress=0,
        current_stage="queued",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    async def run_mm_job(job_id: str, req_data: MultimodalGenerationRequest, uid: str):
        from ai_models.multimodal.multimodal_generator import multimodal_generator
        from app.models.asset import GeneratedAsset
        async with AsyncSessionLocal() as session:
            res_job = await session.execute(select(GenerationJob).where(GenerationJob.id == job_id))
            job_obj = res_job.scalars().first()
            if not job_obj:
                return
            job_obj.status = "processing"
            job_obj.current_stage = "multimodal_synthesis"
            job_obj.progress = 30
            await session.commit()

            try:
                img_input = req_data.image_base64 or req_data.image_url
                res = multimodal_generator.generate_multimodal_asset(
                    text_prompt=req_data.prompt,
                    image_input=img_input,
                    audio_transcript=req_data.audio_transcript,
                    style_override=req_data.style,
                    polygon_budget=req_data.polygon_budget or 5000,
                    quality=req_data.quality or "high",
                )
                
                asset = GeneratedAsset(
                    job_id=job_id,
                    user_id=uid,
                    asset_name=req_data.prompt or "Multimodal 3D Asset",
                    original_prompt=res["fused_prompt"],
                    glb_path=res["glb_path"],
                    thumbnail_path=res.get("thumbnail_path"),
                    polygon_count=res["polygon_count"],
                    file_size=int(res["file_size_mb"] * 1024 * 1024),
                    metadata_json={"generation_duration": res["total_duration_seconds"]},
                )
                session.add(asset)
                
                job_obj.status = "completed"
                job_obj.current_stage = "completed"
                job_obj.progress = 100
                job_obj.completed_at = datetime.utcnow()
                await session.commit()
            except Exception as e:
                logger.error(f"Multimodal generation failed: {e}", exc_info=True)
                job_obj.status = "failed"
                job_obj.error_message = str(e)
                await session.commit()

    background_tasks.add_task(run_mm_job, job.id, request, current_user.id)
    return JobStatusResponse.from_job_model(job)

@router.get("/jobs", response_model=List[JobStatusResponse])
async def list_jobs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None, alias="status", regex="^(all|completed|processing|queued|failed|pending)$"),
    search: Optional[str] = Query(None, description="Search prompt or job ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists generation jobs owned by the authenticated user with filtering and search.
    Strictly isolates history by owner.
    """
    query = select(GenerationJob).where(GenerationJob.user_id == current_user.id)

    if status_filter and status_filter != "all":
        query = query.where(GenerationJob.status == status_filter)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.where(
            or_(
                GenerationJob.prompt.ilike(term),
                GenerationJob.id.ilike(term)
            )
        )

    query = query.order_by(GenerationJob.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    jobs = result.scalars().all()
    
    responses = []
    for j in jobs:
        asset_res = await db.execute(select(GeneratedAsset).where(GeneratedAsset.job_id == j.id))
        asset = asset_res.scalars().first()
        responses.append(JobStatusResponse.from_job_model(j, asset_id=asset.id if asset else None, asset_obj=asset))
    return responses

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves real-time status and stage progress for a generation job.
    Enforces user ownership check.
    """
    result = await db.execute(select(GenerationJob).where(GenerationJob.id == job_id))
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Generation job '{job_id}' not found")
    
    if job.user_id and job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this generation job"
        )

    asset_result = await db.execute(select(GeneratedAsset).where(GeneratedAsset.job_id == job_id))
    asset = asset_result.scalars().first()

    return JobStatusResponse.from_job_model(job, asset_id=asset.id if asset else None, asset_obj=asset)

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
