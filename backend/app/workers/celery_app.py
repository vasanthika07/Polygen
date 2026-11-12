import os
from celery import Celery
from app.config import settings

# Initialize Celery app with Redis broker and backend
celery_app = Celery(
    "polygen",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600, # 10 minute hard limit for 3D generation
    task_soft_time_limit=480, # 8 minute soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
)

if __name__ == "__main__":
    celery_app.start()

