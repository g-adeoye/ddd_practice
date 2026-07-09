import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from domain.models import JobPriority, JobState
from db.models import JobModel
import uuid
from sqlalchemy import select, update
from sqlmodel import col
from datetime import datetime, UTC

logger = structlog.get_logger()


async def create_job(
    db: AsyncSession,
    payload: dict,
    priority: str = "NORMAL",
    max_retries: int = 5,
) -> JobModel:
    "Insert a new transaction and job row with PENDING status"

    job = JobModel(
        id=uuid.uuid4(),
        payload=payload,
        priority=JobPriority.from_str(priority),
        status=JobState.PENDING,
        max_retries=max_retries,
        worker_id=None,
        heartbeat_at=None,
        error=None,
    )

    db.add(job)
    await db.flush()  # writes to Db within the current transaction
    logger.info("job_created", job_id=str(job.id), priority=priority)
    return job


async def get_job(db: AsyncSession, job_id: uuid.UUID) -> JobModel | None:
    "Fetch a single job by ID."
    result = await db.execute(select(JobModel).where(col(JobModel.id) == job_id))
    return result.scalar_one_or_none()


async def mark_running(db: AsyncSession, job_id: uuid.UUID, worker_id: str) -> None:
    "Transition job to RUNNING and record which worker claimed it."
    await db.execute(
        update(JobModel)
        .where(col(JobModel.id) == job_id, col(JobModel.status) == JobState.PENDING)
        .values(
            status=JobState.RUNNING, worker_id=worker_id, heartbeat_at=datetime.now(UTC)
        )
    )


async def mark_completed(db: AsyncSession, job_id: uuid.UUID, result: dict) -> None:
    "Transition job to COMPLETED and store the result"
    await db.execute(
        update(JobModel)
        .where(col(JobModel.id) == job_id)
        .values(status=JobState.COMPLETED, result=result)
    )
    logger.info("job_completed", job_id=str(job_id))


async def mark_failed(
    db: AsyncSession, job_id: uuid.UUID, error: str, retry_count: int
) -> None:
    "Transition job to FAILED and record the error and retry count."
    await db.execute(
        update(JobModel)
        .where(col(JobModel.id) == job_id)
        .values(status=JobState.FAILED, error=error, retry_count=retry_count)
    )
    logger.info("job_completed", job_id=str(job_id))


async def update_heartbeat(db: AsyncSession, job_id: uuid.UUID) -> None:
    """
    Update the heartbeat timestamp for a running job.
    Called every 5 seconds by the worker.
    A stale heartbeat means the worker crashed - the reaper handles this.
    """
    await db.execute(
        update(JobModel)
        .where(col(JobModel.id) == job_id)
        .values(heartbeat_at=datetime.now(UTC))
    )


async def find_zombie_jobs(
    db: AsyncSession, max_heartbeat_age_seconds: int = 60
) -> list[JobModel]:
    """
    Find RUNNING jobs whose heartbeat has gone stale.
    These represent workers that crashed mid-job.
    """
    from sqlalchemy import func, text

    result = await db.execute(
        select(JobModel).where(
            col(JobModel.status) == JobState.RUNNING,
            col(JobModel.heartbeat_at)
            < func.now() - text(f"interval '{max_heartbeat_age_seconds} seconds'"),
        )
    )

    return list(result.scalars().all())
