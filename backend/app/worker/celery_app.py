from celery import Celery

from app.core.settings import settings

# Run the worker with: celery -A app.worker.celery_app worker
celery_app = Celery(
    "cube_tutor",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"],
)
