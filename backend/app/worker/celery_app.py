import os

from celery import Celery

# Run the worker with: celery -A app.worker.celery_app worker
REDIS_HOST = os.getenv("REDIS_HOST", "redis")

celery_app = Celery(
    "cube_tutor",
    broker=f"redis://{REDIS_HOST}:6379/0",
    backend=f"redis://{REDIS_HOST}:6379/1",
    include=["app.worker.tasks"],
)
