from fastapi import APIRouter
from shared.tasks import process_image

router = APIRouter(prefix="/v1/images", tags=["scans"])


@router.post("/upload")
async def upload_image():
    fake_data = "fake data!"

    task = process_image.delay(fake_data)

    return {"task_id": task.id, "status": "queued"}
