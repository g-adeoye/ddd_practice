import uuid
from fastapi import APIRouter, HTTPException

from schemas.job import JobResponse, JobCreate
from services import job_service, queue_service
from db.models import JobModel
from dependencies import DbDep, RedisDep
from infrastructure.metrics import backpressure_rejection_total
from domain.errors import BackPressureError

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", status_code=202, response_model=JobResponse)
async def create_job(body: JobCreate, db: DbDep, redis: RedisDep) -> JobModel:
    """
    Submit a new job to the queue.

    Returns 202 Accepted - the job is queued, not yet processed.
    Returns 503 if the queue is above the high watermark (backpressure).
    """
    try:
        # 1. Write job record to PostgreSQL first
        job = await job_service.create_job(
            db,
            payload=body.payload,
            priority=body.priority,
            max_retries=body.max_retries,
        )
        await db.commit()
        await db.refresh(job)

        # 2. Enqueue to Redis Streams (may raise BackpressureError)
        await queue_service.enqueue(
            redis,
            job_id=str(job.id),
            payload=body.payload,
            priority=body.priority.lower(),
        )

        return job
    except BackPressureError as e:
        backpressure_rejection_total.inc()
        raise HTTPException(
            status_code=503,
            detail=str(e),
            headers={"Retry-After": "10"},
        )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: uuid.UUID, db: DbDep) -> JobModel:
    """
    Fetch the current status and result  of a job.
    Poll this endpoint to check if your job has completed.
    """
    job = await job_service.get_job(db, job_id)

    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return job
