import os
import sys
import uuid

os.environ["AI_BACKEND"] = "procedural"
os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

from app.workers.celery_app import celery_app
from app.workers.tasks import generate_3d_asset_task
from app.core.database import AsyncSessionLocal, init_db
from app.models.job import GenerationJob
import asyncio
from sqlalchemy.future import select

async def run_celery_worker_test():
    print("=" * 60)
    print("TESTING CELERY ASYNC WORKER INTEGRATION")
    print("=" * 60)

    await init_db()

    # 1. Create a job in DB
    job_id = f"job_celery_{uuid.uuid4().hex[:8]}"
    async with AsyncSessionLocal() as db:
        job = GenerationJob(
            id=job_id,
            prompt="A futuristic metallic battle robot with neon green visor.",
            status="queued",
            progress=0,
            current_stage="queued",
            configuration={"style": "sci-fi", "quality": "high", "polygon_budget": 5000}
        )
        db.add(job)
        await db.commit()

    print(f"✓ Created test job record in DB: {job_id}")

    # 2. Invoke Celery task in eager worker mode
    result = generate_3d_asset_task.apply(
        kwargs={
            "job_id": job_id,
            "style_override": "sci-fi",
            "quality": "high",
            "polygon_budget": 5000,
            "target_format": "glb"
        }
    )

    assert result.successful(), f"Celery task did not succeed: {result.result}"
    print(f"✓ Celery worker task executed successfully: {result.result}")

    # 3. Verify database state updated to completed
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(GenerationJob).where(GenerationJob.id == job_id))
        completed_job = res.scalars().first()
        assert completed_job is not None
        assert completed_job.status == "completed", f"Status expected 'completed', got {completed_job.status}"
        assert completed_job.progress == 100
        assert completed_job.completed_at is not None

    print(f"✓ Verified Celery worker updated database status to 'completed' with 100% progress")
    print("=" * 60)
    print("CELERY WORKER INTEGRATION TEST PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_celery_worker_test())

