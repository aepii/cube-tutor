import time

from app.worker.celery_app import celery_app


@celery_app.task
def process_image(data: str):
    print(f"Received data: {data}", flush=True)
    print("Processing image...")
    time.sleep(3)
    return "done"
