from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.schemas.job import JobAccepted, JobCreate, JobRead
from app.core.db import get_session
from app.core.dependencies import get_current_user
from app.jobs import service
from app.jobs.deps import get_job_queue
from app.jobs.queue import JobQueue
from app.models import User

router = APIRouter(prefix="/v1/jobs", tags=["jobs"])


# Submits a job. 202: the work happens later in the worker; poll GET /{id}.
@router.post("/", status_code=status.HTTP_202_ACCEPTED, response_model=JobAccepted)
def create_job(
    body: JobCreate,
    session: Session = Depends(get_session),
    queue: JobQueue = Depends(get_job_queue),
    current_user: User = Depends(get_current_user),
) -> JobAccepted:
    job = service.enqueue(
        session,
        queue,
        user_id=current_user.id,
        type=body.type,
        payload=body.payload.model_dump(exclude_none=True),
    )
    return JobAccepted(id=job.id, status=job.status)


# Reads one of the caller's jobs. Another user's job is a 404, same as an
# unknown id, so the endpoint doesn't reveal that it exists.
@router.get("/{job_id}", response_model=JobRead)
def read_job(
    job_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> JobRead:
    job = service.get_job_for_user(session, job_id, current_user.id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    return JobRead.model_validate(job, from_attributes=True)
