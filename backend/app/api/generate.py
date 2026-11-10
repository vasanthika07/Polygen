import asyncio
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

router = APIRouter(tags=["Generation"])

@router.post("/generate", response_model=JobStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_asset(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    # Create generation job record
    job = GenerationJob(
        user_id=current_user.id if current_user else None,
        prompt=request.prompt,
        status="pending",
        progress=0,
        current_stage="queued",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Dispatch to background task worker
    background_tasks.add_task(
        pipeline_orchestrator.run_pipeline,
        job_id=job.job_id,
        db_factory=AsyncSessionLocal,
        style_override=request.style,
        quality=request.quality,
        polygon_budget=request.polygon_budget,
        target_format=request.target_format,
    )

    return JobStatusResponse.model_validate(job)

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(GenerationJob).where(GenerationJob.job_id == job_id))
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Query asset separately or check if exists
    asset_result = await db.execute(select(GeneratedAsset).where(GeneratedAsset.job_id == job_id))
    asset = asset_result.scalars().first()
    asset_id = asset.asset_id if asset else None

    resp = JobStatusResponse.model_validate(job)
    resp.asset_id = asset_id
    return resp

@router.websocket("/ws/jobs/{job_id}")
async def websocket_job_status(websocket: WebSocket, job_id: str):
    await ws_manager.connect(job_id, websocket)
    try:
        while True:
            # Keep socket alive and listen for client pings or queries
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(job_id, websocket)
    except Exception:
        ws_manager.disconnect(job_id, websocket)
